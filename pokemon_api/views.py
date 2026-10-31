import csv
from collections import Counter

from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Avg, Count, F, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CapturaForm, ConsultaForm, HabilidadeForm, PerfilForm, RegistroForm
from .models import Captura, Habilidade, Pokemon, Regiao, Treinador
from .services import buscar_dados_pokemon


def _base_context():
    """Dados pequenos usados no layout lateral em todas as páginas."""
    total_cidades = (
        Treinador.objects.exclude(cidade_natal='')
        .values('cidade_natal')
        .distinct()
        .count()
    )
    return {
        'sidebar_total_treinadores': Treinador.objects.count(),
        'sidebar_total_cidades': total_cidades,
    }


def _meu_treinador(request):
    """Treinador (perfil) do usuário logado; é o dono dos Pokémon que ele salva."""
    return Treinador.para_usuario(request.user)


def _pokemon_permitido(request, pk, consulta=None):
    """Busca o Pokémon e garante que pertence ao usuário logado.

    Quem tentar acessar o Pokémon de outro treinador recebe 403.
    """
    if consulta is None:
        consulta = Pokemon.objects.all()
    pokemon = get_object_or_404(consulta.select_related('treinador__usuario'), pk=pk)
    if not pokemon.pertence_a(request.user):
        raise PermissionDenied
    return pokemon


def _pokemon_da_api(dados):
    return {
        'nome': dados['name'],
        'id_pokemon': dados['id'],
        'tipos': [t['type']['name'] for t in dados['types']],
        'altura': dados['height'],
        'peso': dados['weight'],
        'habilidades': [
            {'nome': item['ability']['name'], 'oculta': item.get('is_hidden', False)}
            for item in dados['abilities']
        ],
        'hp': dados['stats'][0]['base_stat'],
        'ataque': dados['stats'][1]['base_stat'],
        'defesa': dados['stats'][2]['base_stat'],
        'velocidade': dados['stats'][5]['base_stat'],
        'sprite_url': dados['sprites']['front_default'],
    }


def _habilidades_do_post(post):
    """Lê as linhas de habilidade do formulário: [{'nome': ..., 'oculta': ...}]."""
    nomes = post.getlist('habilidade_nome')
    ocultas = post.getlist('habilidade_oculta')
    return [
        {'nome': nome.strip(), 'oculta': indice < len(ocultas) and ocultas[indice] == '1'}
        for indice, nome in enumerate(nomes)
        if nome.strip()
    ]


def _pokemon_do_post(post):
    """Reconstrói os dados digitados, para reexibir o formulário após um erro."""
    treinador = post.get('treinador', '')
    return {
        'nome': post.get('nome', '').strip(),
        'id_pokemon': post.get('id_pokemon', ''),
        'tipos': [item.strip() for item in post.getlist('tipos') if item.strip()],
        'altura': post.get('altura', ''),
        'peso': post.get('peso', ''),
        'hp': post.get('hp') or 0,
        'ataque': post.get('ataque') or 0,
        'defesa': post.get('defesa') or 0,
        'velocidade': post.get('velocidade') or 0,
        'sprite_url': post.get('sprite_url', ''),
        'observacoes': post.get('observacoes', ''),
        'capturado': 'capturado' in post,
        'favorito': 'favorito' in post,
        'treinador_id': int(treinador) if treinador.isdigit() else None,
    }


def _preencher_pokemon(pokemon, post, treinador):
    """Copia os campos simples do formulário para o objeto (sem salvar)."""
    pokemon.nome = post.get('nome', '').strip()
    pokemon.id_pokemon = post.get('id_pokemon')
    pokemon.tipos = [item.strip() for item in post.getlist('tipos') if item.strip()]
    pokemon.altura = post.get('altura', '')
    pokemon.peso = post.get('peso', '')
    pokemon.hp = post.get('hp') or 0
    pokemon.ataque = post.get('ataque') or 0
    pokemon.defesa = post.get('defesa') or 0
    pokemon.velocidade = post.get('velocidade') or 0
    pokemon.sprite_url = post.get('sprite_url', '')
    pokemon.observacoes = post.get('observacoes', '')
    pokemon.capturado = 'capturado' in post
    pokemon.favorito = 'favorito' in post
    # o dono é sempre o treinador do usuário logado (ignora o que veio no POST)
    pokemon.treinador = treinador


def _salvar_relacionados(pokemon, post, captura_form):
    """Grava o N:N (habilidades) e o 1:1 (ficha de captura) do Pokémon."""
    pokemon.definir_habilidades(
        [(item['nome'], item['oculta']) for item in _habilidades_do_post(post)]
    )
    if captura_form.tem_dados():
        ficha = captura_form.save(commit=False)
        ficha.pokemon = pokemon
        ficha.save()
    elif captura_form.instance.pk:
        captura_form.instance.delete()


def _contexto_form_pokemon(pokemon, habilidades, captura_form, treinador, **extra):
    contexto = _base_context()
    contexto.update({
        'pokemon': pokemon,
        'habilidades_form': habilidades,
        'captura_form': captura_form,
        'catalogo_habilidades': Habilidade.objects.values_list('nome', flat=True),
        'treinadores': Treinador.objects.filter(pk=treinador.pk),
    })
    contexto.update(extra)
    return contexto


@login_required
def buscar_pokemon(request):
    erro = None
    pokemon = None

    if request.method == 'POST':
        id_nome = request.POST.get('pokemon', '').strip()
        if id_nome:
            dados = buscar_dados_pokemon(id_nome)
            if dados is None:
                erro = f'Nenhum Pokémon encontrado com o nome ou número "{id_nome}".'
            else:
                pokemon = _pokemon_da_api(dados)

    contexto = _base_context()
    contexto.update({'pokemon': pokemon, 'erro': erro})
    return render(request, 'buscar_dados_pokemon.html', contexto)


@login_required
def home(request):
    meu = _meu_treinador(request)
    # indicadores de Pokémon = coleção do usuário logado
    pokemons = Pokemon.objects.select_related('treinador', 'regiao').filter(treinador=meu)
    favoritos = pokemons.filter(favorito=True)

    tipos = set()
    for lista in pokemons.values_list('tipos', flat=True):
        tipos.update(lista or [])

    medias = pokemons.aggregate(
        hp=Avg('hp'),
        ataque=Avg('ataque'),
        defesa=Avg('defesa'),
        velocidade=Avg('velocidade'),
    )

    por_regiao = (
        Regiao.objects.annotate(total=Count('pokemons', filter=Q(pokemons__treinador=meu)))
        .filter(total__gt=0)
        .order_by('-total', 'numero_inicial')
    )
    por_treinador = (
        Treinador.objects.annotate(total=Count('pokemons'))
        .order_by('-total', 'nome')
    )
    por_cidade = (
        Treinador.objects.exclude(cidade_natal='')
        .values('cidade_natal')
        .annotate(total=Count('id'))
        .order_by('-total', 'cidade_natal')
    )
    mais_forte = (
        pokemons.annotate(
            total_stats=F('hp') + F('ataque') + F('defesa') + F('velocidade')
        )
        .order_by('-total_stats')
        .first()
    )

    contexto = _base_context()
    contexto.update({
        'total_colecao': pokemons.count(),
        'total_capturados': pokemons.filter(capturado=True).count(),
        'total_favoritos': favoritos.count(),
        'tipos_descobertos': len(tipos),
        'total_treinadores': Treinador.objects.count(),
        'total_cidades': por_cidade.count(),
        'total_habilidades': Habilidade.objects.count(),
        'total_regioes': por_regiao.count(),
        'medias': medias,
        'por_regiao': por_regiao,
        'por_treinador': por_treinador,
        'por_cidade': por_cidade,
        'sem_treinador': Pokemon.objects.filter(treinador__isnull=True).count(),
        'mais_forte': mais_forte,
        'recentes': pokemons.order_by('-data_captura', '-id')[:5],
        'favoritos': favoritos[:3],
    })
    return render(request, 'home.html', contexto)


# C - CREATE
@login_required
def salvar_pokemon(request):
    meu = _meu_treinador(request)
    pokemon = None
    habilidades = []
    captura_form = CapturaForm(prefix='captura')

    if request.method == 'POST':
        captura_form = CapturaForm(request.POST, prefix='captura')
        nome = request.POST.get('nome', '').strip()
        id_pokemon = request.POST.get('id_pokemon')

        if nome and id_pokemon and captura_form.is_valid():
            with transaction.atomic():
                novo = Pokemon()
                _preencher_pokemon(novo, request.POST, meu)
                novo.save()
                _salvar_relacionados(novo, request.POST, captura_form)
            messages.success(request, f'{novo.nome} foi adicionado à sua coleção.')
            return redirect('listar_pokemons')

        pokemon = _pokemon_do_post(request.POST)
        habilidades = _habilidades_do_post(request.POST)
    else:
        id_pokemon = request.GET.get('id_pokemon')
        if id_pokemon:
            dados = buscar_dados_pokemon(id_pokemon)
            if dados:
                pokemon = _pokemon_da_api(dados)
                habilidades = pokemon['habilidades']

    contexto = _contexto_form_pokemon(pokemon, habilidades, captura_form, meu)
    return render(request, 'form_pokemon.html', contexto)


# R - READ
@login_required
def listar_pokemons(request):
    meu = _meu_treinador(request)
    pokemons = Pokemon.objects.select_related('treinador', 'regiao').filter(treinador=meu)
    meus_treinadores = Treinador.objects.filter(pk=meu.pk)
    tipos = sorted({
        tipo
        for lista in pokemons.values_list('tipos', flat=True)
        for tipo in (lista or [])
        if tipo
    })
    cidades = list(
        meus_treinadores.exclude(cidade_natal='')
        .order_by('cidade_natal')
        .values_list('cidade_natal', flat=True)
        .distinct()
    )

    contexto = _base_context()
    contexto.update({
        'pokemons': pokemons,
        'tipos_disponiveis': tipos,
        'treinadores': meus_treinadores,
        'cidades': cidades,
    })
    return render(request, 'listar_pokemons.html', contexto)


# R - READ (detalhe): exibe o Pokémon com os dados do 1:1 e do N:N
@login_required
def detalhes_pokemon(request, pk):
    pokemon = _pokemon_permitido(
        request, pk, Pokemon.objects.select_related('regiao', 'captura')
    )
    atributos = [
        {'rotulo': rotulo, 'valor': valor, 'pct': min(100, round(valor * 100 / 150))}
        for rotulo, valor in (
            ('HP', pokemon.hp),
            ('Ataque', pokemon.ataque),
            ('Defesa', pokemon.defesa),
            ('Velocidade', pokemon.velocidade),
        )
    ]

    contexto = _base_context()
    contexto.update({
        'pokemon': pokemon,
        'captura': getattr(pokemon, 'captura', None),
        'vinculos': pokemon.vinculos.select_related('habilidade'),
        'atributos': atributos,
    })
    return render(request, 'detalhes_pokemon.html', contexto)


# U - UPDATE
@login_required
def editar_pokemon(request, pk):
    pokemon = _pokemon_permitido(request, pk, Pokemon.objects.select_related('captura'))
    meu = pokemon.treinador
    captura = getattr(pokemon, 'captura', None)

    if request.method == 'POST':
        captura_form = CapturaForm(request.POST, instance=captura, prefix='captura')

        if captura_form.is_valid():
            with transaction.atomic():
                _preencher_pokemon(pokemon, request.POST, meu)
                pokemon.save()
                _salvar_relacionados(pokemon, request.POST, captura_form)
            messages.success(request, f'{pokemon.nome} foi atualizado.')
            return redirect('listar_pokemons')

        dados = _pokemon_do_post(request.POST)
        habilidades = _habilidades_do_post(request.POST)
        titulo = dados['nome'] or pokemon.nome
    else:
        captura_form = CapturaForm(instance=captura, prefix='captura')
        dados = pokemon
        habilidades = [
            {'nome': vinculo.habilidade.nome, 'oculta': vinculo.oculta}
            for vinculo in pokemon.vinculos.select_related('habilidade')
        ]
        titulo = pokemon.nome

    contexto = _contexto_form_pokemon(dados, habilidades, captura_form, meu, titulo=titulo)
    return render(request, 'form_pokemon.html', contexto)


# D - DELETE
@login_required
def remover_pokemon(request, pk):
    pokemon = _pokemon_permitido(request, pk)
    if request.method == 'POST':
        nome = pokemon.nome
        pokemon.delete()
        messages.success(request, f'{nome} foi removido da sua coleção.')
    return redirect('listar_pokemons')


# ---------------------------------------------------------------------------
# CRUD 2 — Habilidade (segunda entidade do N:N Pokémon <-> Habilidade)
# ---------------------------------------------------------------------------

# R - READ (lista)
@login_required
def listar_habilidades(request):
    busca = request.GET.get('q', '').strip()
    habilidades = Habilidade.objects.annotate(total_pokemons=Count('vinculos'))
    total_catalogo = habilidades.count()
    if busca:
        habilidades = habilidades.filter(
            Q(nome__icontains=busca) | Q(descricao__icontains=busca)
        )

    contexto = _base_context()
    contexto.update({
        'habilidades': habilidades,
        'busca': busca,
        'total_catalogo': total_catalogo,
    })
    return render(request, 'listar_habilidades.html', contexto)


# R - READ (detalhe): habilidade + Pokémon que a possuem (dados do through)
@login_required
def detalhes_habilidade(request, pk):
    habilidade = get_object_or_404(Habilidade, pk=pk)

    contexto = _base_context()
    contexto.update({
        'habilidade': habilidade,
        'vinculos': habilidade.vinculos.select_related('pokemon').order_by(
            'pokemon__id_pokemon', 'id'
        ),
    })
    return render(request, 'detalhes_habilidade.html', contexto)


# C - CREATE
@login_required
def criar_habilidade(request):
    form = HabilidadeForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        habilidade = form.save()
        messages.success(request, f'Habilidade "{habilidade.nome}" criada.')
        return redirect('listar_habilidades')

    contexto = _base_context()
    contexto.update({'form': form})
    return render(request, 'form_habilidade.html', contexto)


# U - UPDATE
@login_required
def editar_habilidade(request, pk):
    habilidade = get_object_or_404(Habilidade, pk=pk)
    form = HabilidadeForm(request.POST or None, instance=habilidade)
    if request.method == 'POST' and form.is_valid():
        habilidade = form.save()
        messages.success(request, f'Habilidade "{habilidade.nome}" atualizada.')
        return redirect('detalhes_habilidade', pk=habilidade.pk)

    contexto = _base_context()
    contexto.update({'form': form, 'habilidade': habilidade})
    return render(request, 'form_habilidade.html', contexto)


# D - DELETE (GET mostra a confirmação; POST exclui)
@login_required
def remover_habilidade(request, pk):
    habilidade = get_object_or_404(Habilidade, pk=pk)
    if request.method == 'POST':
        nome = habilidade.nome
        habilidade.delete()
        messages.success(request, f'Habilidade "{nome}" removida.')
        return redirect('listar_habilidades')

    contexto = _base_context()
    contexto.update({
        'habilidade': habilidade,
        'vinculos': habilidade.vinculos.select_related('pokemon').order_by(
            'pokemon__id_pokemon', 'id'
        ),
    })
    return render(request, 'confirmar_remocao_habilidade.html', contexto)


# ---------------------------------------------------------------------------
# Autenticação e área restrita (semana 4)
# ---------------------------------------------------------------------------

def registrar(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = RegistroForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        usuario = form.save()
        login(request, usuario)
        messages.success(request, f'Bem-vindo, {usuario.first_name}! Sua conta foi criada.')
        return redirect('home')

    return render(request, 'registro.html', {'form': form})


@login_required
def perfil(request):
    """Área restrita: dados do usuário logado e resumo da própria coleção."""
    meu = _meu_treinador(request)
    pokemons = Pokemon.objects.filter(treinador=meu)

    contexto = _base_context()
    contexto.update({
        'treinador': meu,
        'total_pokemons': pokemons.count(),
        'total_capturados': pokemons.filter(capturado=True).count(),
        'total_favoritos': pokemons.filter(favorito=True).count(),
    })
    return render(request, 'perfil.html', contexto)


@login_required
def editar_perfil(request):
    """Cada usuário só edita o próprio perfil (a rota nunca recebe um id)."""
    meu = _meu_treinador(request)
    form = PerfilForm(request.POST or None, instance=meu)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Perfil atualizado com sucesso.')
        return redirect('perfil')

    contexto = _base_context()
    contexto.update({'form': form})
    return render(request, 'perfil_form.html', contexto)


@login_required
def alterar_senha(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        usuario = form.save()
        update_session_auth_hash(request, usuario)  # mantém a sessão ativa
        messages.success(request, 'Senha alterada com sucesso.')
        return redirect('perfil')

    contexto = _base_context()
    contexto.update({'form': form})
    return render(request, 'senha_form.html', contexto)


# ---------------------------------------------------------------------------
# Consultas e relatório (semana 5)
# ---------------------------------------------------------------------------

POR_PAGINA = 12


def _tipos_da_colecao(pokemons):
    """Tipos (minúsculos, ordenados) presentes na coleção informada."""
    return sorted({
        str(tipo).lower()
        for lista in pokemons.values_list('tipos', flat=True)
        for tipo in (lista or [])
        if tipo
    })


def _aplicar_filtros(pokemons, filtros):
    """Aplica os filtros já validados (cleaned_data do ConsultaForm) à coleção."""
    busca = filtros.get('q')
    if busca:
        condicao = (
            Q(nome__icontains=busca)
            | Q(captura__apelido__icontains=busca)
            | Q(captura__local__icontains=busca)
        )
        numero = busca.lstrip('#')
        if numero.isdigit():
            condicao |= Q(id_pokemon=int(numero))
        pokemons = pokemons.filter(condicao)

    tipo = filtros.get('tipo')
    if tipo:
        # `tipos` é um JSONField (lista); o SQLite não filtra dentro de listas,
        # então os ids que têm o tipo são separados em Python.
        ids = [
            pk for pk, lista in pokemons.values_list('pk', 'tipos')
            if tipo in [str(item).lower() for item in (lista or [])]
        ]
        pokemons = pokemons.filter(pk__in=ids)

    if filtros.get('regiao'):
        pokemons = pokemons.filter(regiao=filtros['regiao'])
    if filtros.get('habilidade'):
        pokemons = pokemons.filter(vinculos__habilidade=filtros['habilidade'])
    if filtros.get('pokebola'):
        pokemons = pokemons.filter(captura__pokebola=filtros['pokebola'])
    if filtros.get('capturado') == 'sim':
        pokemons = pokemons.filter(capturado=True)
    elif filtros.get('capturado') == 'nao':
        pokemons = pokemons.filter(capturado=False)
    if filtros.get('favorito'):
        pokemons = pokemons.filter(favorito=True)
    if filtros.get('data_inicio'):
        pokemons = pokemons.filter(data_captura__gte=filtros['data_inicio'])
    if filtros.get('data_fim'):
        pokemons = pokemons.filter(data_captura__lte=filtros['data_fim'])

    ordenar = filtros.get('ordenar') or 'nome'
    if ordenar == 'numero':
        return pokemons.order_by('id_pokemon', 'nome')
    if ordenar == 'forca':
        return pokemons.annotate(
            total_stats=F('hp') + F('ataque') + F('defesa') + F('velocidade')
        ).order_by('-total_stats', 'nome')
    if ordenar == 'recentes':
        return pokemons.order_by('-data_captura', '-id')
    return pokemons.order_by('nome', 'id_pokemon')


@login_required
def consultas(request):
    """Busca com filtros (GET) sobre a coleção do usuário logado."""
    meu = _meu_treinador(request)
    colecao = Pokemon.objects.filter(treinador=meu)

    form = ConsultaForm(request.GET or None, tipos=_tipos_da_colecao(colecao))
    # sem parâmetros na URL, a consulta mostra a coleção inteira
    filtrando = bool(request.GET)
    pagina = None
    total = 0

    if not filtrando or form.is_valid():
        filtros = form.cleaned_data if filtrando else {}
        resultado = _aplicar_filtros(
            colecao.select_related('regiao', 'captura'), filtros
        )
        total = resultado.count()
        pagina = Paginator(resultado, POR_PAGINA).get_page(request.GET.get('page'))

    parametros = request.GET.copy()
    parametros.pop('page', None)

    contexto = _base_context()
    contexto.update({
        'form': form,
        'pagina': pagina,
        'total_resultados': total,
        'total_colecao': colecao.count(),
        'filtrando': any(valor for chave, valor in request.GET.items() if chave != 'page'),
        'querystring': parametros.urlencode(),
    })
    return render(request, 'consultas.html', contexto)


def _dados_relatorio(meu):
    """Indicadores agregados da coleção de um treinador (usado na tela e no CSV)."""
    pokemons = Pokemon.objects.filter(treinador=meu)
    total = pokemons.count()
    capturados = pokemons.filter(capturado=True).count()
    fichas = Captura.objects.filter(pokemon__treinador=meu)

    medias = pokemons.aggregate(
        hp=Avg('hp'), ataque=Avg('ataque'),
        defesa=Avg('defesa'), velocidade=Avg('velocidade'),
    )
    medias = {
        chave: round(valor, 1) if valor is not None else None
        for chave, valor in medias.items()
    }

    contagem_tipos = Counter(
        str(tipo).lower()
        for lista in pokemons.values_list('tipos', flat=True)
        for tipo in (lista or [])
        if tipo
    )
    por_tipo = sorted(contagem_tipos.items(), key=lambda item: (-item[1], item[0]))

    rotulos_pokebola = dict(Captura.Pokebola.choices)
    por_pokebola = [
        {'nome': rotulos_pokebola.get(linha['pokebola'], linha['pokebola']), 'total': linha['total']}
        for linha in fichas.exclude(pokebola='')
        .values('pokebola').annotate(total=Count('id')).order_by('-total', 'pokebola')
    ]

    nivel_medio = fichas.aggregate(media=Avg('nivel'))['media']
    if nivel_medio is not None:
        nivel_medio = round(nivel_medio, 1)

    return {
        'total': total,
        'capturados': capturados,
        'nao_capturados': total - capturados,
        'favoritos': pokemons.filter(favorito=True).count(),
        'percentual_capturados': round(capturados * 100 / total) if total else 0,
        'medias': medias,
        'por_regiao': (
            Regiao.objects
            .annotate(total=Count('pokemons', filter=Q(pokemons__treinador=meu)))
            .filter(total__gt=0).order_by('-total', 'numero_inicial')
        ),
        'por_tipo': por_tipo,
        'por_pokebola': por_pokebola,
        'top_habilidades': (
            Habilidade.objects
            .annotate(total=Count('vinculos', filter=Q(vinculos__pokemon__treinador=meu)))
            .filter(total__gt=0).order_by('-total', 'nome')[:5]
        ),
        'mais_fortes': (
            pokemons.annotate(
                total_stats=F('hp') + F('ataque') + F('defesa') + F('velocidade')
            ).order_by('-total_stats', 'nome')[:5]
        ),
        'total_fichas': fichas.count(),
        'nivel_medio': nivel_medio,
        'gerado_em': timezone.now(),
    }


@login_required
def relatorio(request):
    """Relatório do sistema: dados agregados da coleção, com exportação em CSV."""
    meu = _meu_treinador(request)
    contexto = _base_context()
    contexto.update(_dados_relatorio(meu))
    contexto['treinador'] = meu
    return render(request, 'relatorio.html', contexto)


def _celula_csv(valor):
    """Evita que o Excel interprete texto digitado pelo usuário como fórmula."""
    if isinstance(valor, str) and valor[:1] in ('=', '+', '-', '@', '\t', '\r'):
        return "'" + valor
    return valor


@login_required
def exportar_relatorio(request):
    """Baixa o relatório em CSV: `?dados=resumo` (padrão) ou `?dados=pokemons`."""
    meu = _meu_treinador(request)
    tipo_dados = request.GET.get('dados', 'resumo')
    hoje = timezone.localdate().strftime('%Y%m%d')
    if tipo_dados != 'pokemons':
        tipo_dados = 'resumo'

    resposta = HttpResponse(content_type='text/csv; charset=utf-8')
    resposta['Content-Disposition'] = (
        f'attachment; filename="relatorio-{tipo_dados}-{hoje}.csv"'
    )
    resposta.write('\ufeff')  # BOM: o Excel abre os acentos corretamente
    escritor = csv.writer(resposta, delimiter=';')

    if tipo_dados == 'pokemons':
        escritor.writerow([
            'Número', 'Nome', 'Tipos', 'Região', 'Capturado', 'Favorito',
            'HP', 'Ataque', 'Defesa', 'Velocidade', 'Total de atributos',
            'Apelido', 'Nível', 'Pokébola', 'Local da captura', 'Adicionado em',
        ])
        pokemons = (
            Pokemon.objects.filter(treinador=meu)
            .select_related('regiao', 'captura').order_by('id_pokemon', 'nome')
        )
        for pokemon in pokemons:
            ficha = getattr(pokemon, 'captura', None)
            escritor.writerow([_celula_csv(valor) for valor in [
                pokemon.id_pokemon, pokemon.nome, ', '.join(pokemon.tipos or []),
                pokemon.regiao.nome if pokemon.regiao else '',
                'Sim' if pokemon.capturado else 'Não',
                'Sim' if pokemon.favorito else 'Não',
                pokemon.hp, pokemon.ataque, pokemon.defesa, pokemon.velocidade,
                pokemon.total_atributos,
                ficha.apelido if ficha else '',
                ficha.nivel if ficha and ficha.nivel is not None else '',
                ficha.get_pokebola_display() if ficha else '',
                ficha.local if ficha else '',
                pokemon.data_captura.strftime('%d/%m/%Y'),
            ]])
        return resposta

    dados = _dados_relatorio(meu)
    escritor.writerow(['Relatório da coleção', meu.nome])
    escritor.writerow(['Gerado em', timezone.localtime(dados['gerado_em']).strftime('%d/%m/%Y %H:%M')])
    escritor.writerow([])
    escritor.writerow(['Indicador', 'Valor'])
    escritor.writerow(['Pokémon na coleção', dados['total']])
    escritor.writerow(['Capturados', dados['capturados']])
    escritor.writerow(['Não capturados', dados['nao_capturados']])
    escritor.writerow(['Favoritos', dados['favoritos']])
    escritor.writerow(['% capturados', f"{dados['percentual_capturados']}%"])
    escritor.writerow(['Fichas de captura', dados['total_fichas']])
    escritor.writerow(['Nível médio (fichas)', '' if dados['nivel_medio'] is None else dados['nivel_medio']])
    for rotulo, chave in (('HP', 'hp'), ('Ataque', 'ataque'), ('Defesa', 'defesa'), ('Velocidade', 'velocidade')):
        valor = dados['medias'][chave]
        escritor.writerow([f'Média de {rotulo}', '' if valor is None else valor])

    escritor.writerow([])
    escritor.writerow(['Região', 'Pokémon'])
    for regiao in dados['por_regiao']:
        escritor.writerow([regiao.nome, regiao.total])

    escritor.writerow([])
    escritor.writerow(['Tipo', 'Pokémon'])
    for tipo, total in dados['por_tipo']:
        escritor.writerow([tipo.title(), total])

    escritor.writerow([])
    escritor.writerow(['Pokébola', 'Fichas'])
    for linha in dados['por_pokebola']:
        escritor.writerow([linha['nome'], linha['total']])

    escritor.writerow([])
    escritor.writerow(['Habilidade mais comum', 'Pokémon'])
    for habilidade in dados['top_habilidades']:
        escritor.writerow([_celula_csv(habilidade.nome), habilidade.total])

    escritor.writerow([])
    escritor.writerow(['Mais fortes', 'Total de atributos'])
    for pokemon in dados['mais_fortes']:
        escritor.writerow([_celula_csv(pokemon.nome), pokemon.total_stats])
    return resposta
