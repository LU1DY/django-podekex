<<<<<<< HEAD
from django.db.models import Avg, Count, F
from django.shortcuts import get_object_or_404, redirect, render

=======
from django.contrib import messages
from django.db import transaction
from django.db.models import Avg, Count, F, Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CapturaForm, HabilidadeForm
>>>>>>> 1eed28a (feat(semana 3): adiciona crud 2 de treinadores e relacionamentos no banco de dados)
from .models import Habilidade, Pokemon, Regiao, Treinador
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


def _pokemon_da_api(dados):
    return {
        'nome': dados['name'],
        'id_pokemon': dados['id'],
        'tipos': [t['type']['name'] for t in dados['types']],
        'altura': dados['height'],
        'peso': dados['weight'],
<<<<<<< HEAD
        'habilidades': [item['ability']['name'] for item in dados['abilities']],
=======
        'habilidades': [
            {'nome': item['ability']['name'], 'oculta': item.get('is_hidden', False)}
            for item in dados['abilities']
        ],
>>>>>>> 1eed28a (feat(semana 3): adiciona crud 2 de treinadores e relacionamentos no banco de dados)
        'hp': dados['stats'][0]['base_stat'],
        'ataque': dados['stats'][1]['base_stat'],
        'defesa': dados['stats'][2]['base_stat'],
        'velocidade': dados['stats'][5]['base_stat'],
        'sprite_url': dados['sprites']['front_default'],
    }

<<<<<<< HEAD
=======

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


def _preencher_pokemon(pokemon, post):
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
    pokemon.treinador_id = post.get('treinador') or None


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


def _contexto_form_pokemon(pokemon, habilidades, captura_form, **extra):
    contexto = _base_context()
    contexto.update({
        'pokemon': pokemon,
        'habilidades_form': habilidades,
        'captura_form': captura_form,
        'catalogo_habilidades': Habilidade.objects.values_list('nome', flat=True),
        'treinadores': Treinador.objects.all(),
    })
    contexto.update(extra)
    return contexto

>>>>>>> 1eed28a (feat(semana 3): adiciona crud 2 de treinadores e relacionamentos no banco de dados)

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


def home(request):
    pokemons = Pokemon.objects.select_related('treinador', 'regiao').all()
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
        Regiao.objects.annotate(total=Count('pokemons'))
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
        'sem_treinador': pokemons.filter(treinador__isnull=True).count(),
        'mais_forte': mais_forte,
        'recentes': pokemons.order_by('-data_captura', '-id')[:5],
        'favoritos': favoritos[:3],
    })
    return render(request, 'home.html', contexto)


# C - CREATE
def salvar_pokemon(request):
    pokemon = None
<<<<<<< HEAD

    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        id_pokemon = request.POST.get('id_pokemon')
        tipos = [item.strip() for item in request.POST.getlist('tipos') if item.strip()]
        habilidades = [item.strip() for item in request.POST.getlist('habilidades') if item.strip()]

        if nome and id_pokemon:
            Pokemon.objects.create(
                nome=nome,
                id_pokemon=id_pokemon,
                tipos=tipos,
                habilidades=habilidades,
                altura=request.POST.get('altura', ''),
                peso=request.POST.get('peso', ''),
                hp=request.POST.get('hp') or 0,
                ataque=request.POST.get('ataque') or 0,
                defesa=request.POST.get('defesa') or 0,
                velocidade=request.POST.get('velocidade') or 0,
                sprite_url=request.POST.get('sprite_url', ''),
                observacoes=request.POST.get('observacoes', ''),
                capturado='capturado' in request.POST,
                favorito='favorito' in request.POST,
                treinador_id=request.POST.get('treinador') or None,
            )
            return redirect('listar_pokemons')
=======
    habilidades = []
    captura_form = CapturaForm(prefix='captura')

    if request.method == 'POST':
        captura_form = CapturaForm(request.POST, prefix='captura')
        nome = request.POST.get('nome', '').strip()
        id_pokemon = request.POST.get('id_pokemon')

        if nome and id_pokemon and captura_form.is_valid():
            with transaction.atomic():
                novo = Pokemon()
                _preencher_pokemon(novo, request.POST)
                novo.save()
                _salvar_relacionados(novo, request.POST, captura_form)
            messages.success(request, f'{novo.nome} foi adicionado à sua coleção.')
            return redirect('listar_pokemons')

        pokemon = _pokemon_do_post(request.POST)
        habilidades = _habilidades_do_post(request.POST)
>>>>>>> 1eed28a (feat(semana 3): adiciona crud 2 de treinadores e relacionamentos no banco de dados)
    else:
        id_pokemon = request.GET.get('id_pokemon')
        if id_pokemon:
            dados = buscar_dados_pokemon(id_pokemon)
            if dados:
                pokemon = _pokemon_da_api(dados)
<<<<<<< HEAD

    contexto = _base_context()
    contexto.update({
        'pokemon': pokemon,
        'treinadores': Treinador.objects.all(),
    })
=======
                habilidades = pokemon['habilidades']

    contexto = _contexto_form_pokemon(pokemon, habilidades, captura_form)
>>>>>>> 1eed28a (feat(semana 3): adiciona crud 2 de treinadores e relacionamentos no banco de dados)
    return render(request, 'form_pokemon.html', contexto)


# R - READ
def listar_pokemons(request):
    pokemons = Pokemon.objects.select_related('treinador', 'regiao').all()
    tipos = sorted({
        tipo
        for lista in pokemons.values_list('tipos', flat=True)
        for tipo in (lista or [])
        if tipo
    })
    cidades = list(
        Treinador.objects.exclude(cidade_natal='')
        .order_by('cidade_natal')
        .values_list('cidade_natal', flat=True)
        .distinct()
    )

    contexto = _base_context()
    contexto.update({
        'pokemons': pokemons,
        'tipos_disponiveis': tipos,
        'treinadores': Treinador.objects.all(),
        'cidades': cidades,
    })
    return render(request, 'listar_pokemons.html', contexto)


<<<<<<< HEAD
# U - UPDATE
def editar_pokemon(request, pk):
    pokemon = get_object_or_404(Pokemon, pk=pk)

    if request.method == 'POST':
        pokemon.nome = request.POST.get('nome', '').strip()
        pokemon.id_pokemon = request.POST.get('id_pokemon')
        pokemon.tipos = [item.strip() for item in request.POST.getlist('tipos') if item.strip()]
        pokemon.habilidades = [item.strip() for item in request.POST.getlist('habilidades') if item.strip()]
        pokemon.altura = request.POST.get('altura', '')
        pokemon.peso = request.POST.get('peso', '')
        pokemon.hp = request.POST.get('hp') or 0
        pokemon.ataque = request.POST.get('ataque') or 0
        pokemon.defesa = request.POST.get('defesa') or 0
        pokemon.velocidade = request.POST.get('velocidade') or 0
        pokemon.sprite_url = request.POST.get('sprite_url', '')
        pokemon.observacoes = request.POST.get('observacoes', '')
        pokemon.capturado = 'capturado' in request.POST
        pokemon.favorito = 'favorito' in request.POST
        pokemon.treinador_id = request.POST.get('treinador') or None
        pokemon.save()
        return redirect('listar_pokemons')

    contexto = _base_context()
    contexto.update({
        'titulo': pokemon.nome,
        'pokemon': pokemon,
        'treinadores': Treinador.objects.all(),
    })
    return render(request, 'form_pokemon.html', contexto)

=======
# R - READ (detalhe): exibe o Pokémon com os dados do 1:1 e do N:N
def detalhes_pokemon(request, pk):
    pokemon = get_object_or_404(
        Pokemon.objects.select_related('treinador', 'regiao', 'captura'), pk=pk
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
def editar_pokemon(request, pk):
    pokemon = get_object_or_404(Pokemon.objects.select_related('captura'), pk=pk)
    captura = getattr(pokemon, 'captura', None)

    if request.method == 'POST':
        captura_form = CapturaForm(request.POST, instance=captura, prefix='captura')

        if captura_form.is_valid():
            with transaction.atomic():
                _preencher_pokemon(pokemon, request.POST)
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

    contexto = _contexto_form_pokemon(dados, habilidades, captura_form, titulo=titulo)
    return render(request, 'form_pokemon.html', contexto)

>>>>>>> 1eed28a (feat(semana 3): adiciona crud 2 de treinadores e relacionamentos no banco de dados)

# D - DELETE
def remover_pokemon(request, pk):
    pokemon = get_object_or_404(Pokemon, pk=pk)
    if request.method == 'POST':
<<<<<<< HEAD
        pokemon.delete()
    return redirect('listar_pokemons')
=======
        nome = pokemon.nome
        pokemon.delete()
        messages.success(request, f'{nome} foi removido da sua coleção.')
    return redirect('listar_pokemons')


# ---------------------------------------------------------------------------
# CRUD 2 — Habilidade (segunda entidade do N:N Pokémon <-> Habilidade)
# ---------------------------------------------------------------------------

# R - READ (lista)
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
>>>>>>> 1eed28a (feat(semana 3): adiciona crud 2 de treinadores e relacionamentos no banco de dados)
