import csv

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, F, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ConsultaForm, PerfilForm, PokemonForm, RegistroForm
from .models import Habilidade, Pokemon, PokemonHabilidade, Regiao, Treinador
from .services import buscar_dados_pokemon

SOMA_ATRIBUTOS = F('hp') + F('ataque') + F('defesa') + F('velocidade')


def _treinador(request):
    """Perfil de treinador do usuário logado (criado se não existir, ex.: superusuário)."""
    treinador, _ = Treinador.objects.get_or_create(
        usuario=request.user,
        defaults={'nome': request.user.first_name or request.user.username},
    )
    return treinador


def _pokemon_da_api(dados):
    """Converte o JSON da PokéAPI nos campos usados pelo sistema."""
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
        'sprite_url': dados['sprites']['front_default'] or '',
    }


# ---------------------------------------------------------------------------
# Busca na API (livre) e salvar (exige login)
# ---------------------------------------------------------------------------

def buscar_pokemon(request):
    """Qualquer visitante pode buscar. Aceita GET (?pokemon=) e POST."""
    consulta = (request.POST.get('pokemon') or request.GET.get('pokemon') or '').strip()
    pokemon = erro = None
    if consulta:
        dados = buscar_dados_pokemon(consulta)
        if dados is None:
            erro = f'Nenhum Pokémon encontrado com o nome ou número "{consulta}".'
        else:
            pokemon = _pokemon_da_api(dados)
    return render(request, 'buscar_dados_pokemon.html', {
        'pokemon': pokemon, 'erro': erro, 'consulta': consulta,
    })


@login_required
def salvar_pokemon(request):
    """Salva na coleção do usuário logado o Pokémon buscado na API."""
    if request.method != 'POST':
        return redirect('buscar_dados_pokemon')

    dados = buscar_dados_pokemon(request.POST.get('id_pokemon', ''))
    if dados is None:
        messages.error(request, 'Não foi possível obter esse Pokémon na PokéAPI.')
        return redirect('buscar_dados_pokemon')

    info = _pokemon_da_api(dados)
    treinador = _treinador(request)
    if Pokemon.objects.filter(treinador=treinador, id_pokemon=info['id_pokemon']).exists():
        messages.info(request, f'{info["nome"].title()} já está na sua coleção.')
        return redirect('listar_pokemons')

    habilidades = info.pop('habilidades')
    regiao = Regiao.objects.filter(
        numero_inicial__lte=info['id_pokemon'], numero_final__gte=info['id_pokemon']
    ).first()
    pokemon = Pokemon.objects.create(treinador=treinador, regiao=regiao, **info)
    for item in habilidades:
        habilidade, _ = Habilidade.objects.get_or_create(nome=item['nome'])
        PokemonHabilidade.objects.create(
            pokemon=pokemon, habilidade=habilidade, oculta=item['oculta']
        )

    messages.success(request, f'{pokemon.nome.title()} foi adicionado à sua coleção.')
    return redirect('listar_pokemons')


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def home(request):
    if not request.user.is_authenticated:
        return redirect('buscar_dados_pokemon')

    pokemons = Pokemon.objects.filter(treinador=_treinador(request))
    favoritos = pokemons.filter(favorito=True)
    tipos = {tipo for lista in pokemons.values_list('tipos', flat=True) for tipo in lista}

    return render(request, 'home.html', {
        'total': pokemons.count(),
        'total_capturados': pokemons.filter(capturado=True).count(),
        'total_favoritos': favoritos.count(),
        'total_tipos': len(tipos),
        'por_regiao': Regiao.objects.filter(pokemons__in=pokemons)
            .annotate(total=Count('pokemons')).order_by('-total', 'numero_inicial'),
        'favoritos': favoritos[:3],
        'recentes': pokemons.select_related('regiao').order_by('-data_captura', '-id')[:5],
    })


# ---------------------------------------------------------------------------
# CRUD de Pokémon (cada usuário só acessa os seus; de outro treinador dá 404)
# ---------------------------------------------------------------------------

def _meu_pokemon(request, pk):
    return get_object_or_404(Pokemon, pk=pk, treinador__usuario=request.user)


@login_required
def listar_pokemons(request):
    pokemons = Pokemon.objects.filter(treinador__usuario=request.user)
    return render(request, 'listar_pokemons.html', {
        'pokemons': pokemons.select_related('regiao').order_by('-data_captura', '-id'),
    })


@login_required
def detalhes_pokemon(request, pk):
    pokemon = _meu_pokemon(request, pk)
    return render(request, 'detalhes_pokemon.html', {
        'pokemon': pokemon,
        'vinculos': pokemon.vinculos.select_related('habilidade'),
        'total_atributos': pokemon.hp + pokemon.ataque + pokemon.defesa + pokemon.velocidade,
    })


@login_required
def editar_pokemon(request, pk):
    pokemon = _meu_pokemon(request, pk)
    form = PokemonForm(request.POST or None, instance=pokemon)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'{pokemon.nome.title()} foi atualizado.')
        return redirect('listar_pokemons')
    return render(request, 'form_pokemon.html', {'form': form, 'pokemon': pokemon})


@login_required
def remover_pokemon(request, pk):
    pokemon = _meu_pokemon(request, pk)
    if request.method == 'POST':
        pokemon.delete()
        messages.success(request, f'{pokemon.nome.title()} foi removido da sua coleção.')
    return redirect('listar_pokemons')


# ---------------------------------------------------------------------------
# Consultas e relatório
# ---------------------------------------------------------------------------

@login_required
def consultas(request):
    colecao = Pokemon.objects.filter(treinador__usuario=request.user)
    form = ConsultaForm(request.GET or None)
    resultado = colecao

    if form.is_valid():
        filtros = form.cleaned_data
        if filtros['q']:
            busca = filtros['q'].strip().lstrip('#')
            condicao = Q(nome__icontains=busca)
            if busca.isdigit():
                condicao |= Q(id_pokemon=int(busca))
            resultado = resultado.filter(condicao)
        if filtros['tipo']:
            tipo = filtros['tipo'].strip().lower()
            ids = [pk for pk, lista in resultado.values_list('pk', 'tipos') if tipo in lista]
            resultado = resultado.filter(pk__in=ids)
        if filtros['regiao']:
            resultado = resultado.filter(regiao=filtros['regiao'])
        if filtros['data_inicio']:
            resultado = resultado.filter(data_captura__gte=filtros['data_inicio'])
        if filtros['data_fim']:
            resultado = resultado.filter(data_captura__lte=filtros['data_fim'])
    elif request.GET:
        resultado = colecao.none()

    return render(request, 'consultas.html', {
        'form': form,
        'pokemons': resultado.select_related('regiao').order_by('nome'),
        'filtrando': bool(request.GET),
    })


def _dados_relatorio(usuario):
    pokemons = Pokemon.objects.filter(treinador__usuario=usuario)
    total = pokemons.count()
    capturados = pokemons.filter(capturado=True).count()

    tipos = {}
    for lista in pokemons.values_list('tipos', flat=True):
        for tipo in lista:
            tipos[tipo] = tipos.get(tipo, 0) + 1

    return {
        'total': total,
        'capturados': capturados,
        'favoritos': pokemons.filter(favorito=True).count(),
        'percentual': round(capturados * 100 / total) if total else 0,
        'medias': pokemons.aggregate(
            hp=Avg('hp'), ataque=Avg('ataque'), defesa=Avg('defesa'), velocidade=Avg('velocidade')
        ),
        'por_regiao': Regiao.objects.filter(pokemons__in=pokemons)
            .annotate(total=Count('pokemons')).order_by('-total', 'numero_inicial'),
        'por_tipo': sorted(tipos.items(), key=lambda item: (-item[1], item[0])),
        'mais_fortes': pokemons.annotate(soma=SOMA_ATRIBUTOS).order_by('-soma', 'nome')[:5],
    }


@login_required
def relatorio(request):
    return render(request, 'relatorio.html', _dados_relatorio(request.user))


@login_required
def exportar_relatorio(request):
    dados = _dados_relatorio(request.user)
    resposta = HttpResponse(content_type='text/csv; charset=utf-8')
    resposta['Content-Disposition'] = 'attachment; filename="relatorio.csv"'
    resposta.write('\ufeff')  # BOM: o Excel abre os acentos corretamente
    escritor = csv.writer(resposta, delimiter=';')

    escritor.writerow(['Indicador', 'Valor'])
    escritor.writerow(['Pokémon na coleção', dados['total']])
    escritor.writerow(['Capturados', dados['capturados']])
    escritor.writerow(['Favoritos', dados['favoritos']])
    for rotulo, chave in (('HP', 'hp'), ('Ataque', 'ataque'), ('Defesa', 'defesa'), ('Velocidade', 'velocidade')):
        valor = dados['medias'][chave]
        escritor.writerow([f'Média de {rotulo}', '' if valor is None else round(valor, 1)])

    escritor.writerow([])
    escritor.writerow(['Região', 'Pokémon'])
    for regiao in dados['por_regiao']:
        escritor.writerow([regiao.nome, regiao.total])

    escritor.writerow([])
    escritor.writerow(['Tipo', 'Pokémon'])
    for tipo, total in dados['por_tipo']:
        escritor.writerow([tipo.title(), total])
    return resposta


# ---------------------------------------------------------------------------
# Cadastro e perfil
# ---------------------------------------------------------------------------

def registrar(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = RegistroForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.save())
        messages.success(request, 'Conta criada com sucesso.')
        return redirect('home')
    return render(request, 'registro.html', {'form': form})


@login_required
def perfil(request):
    pokemons = Pokemon.objects.filter(treinador__usuario=request.user)
    return render(request, 'perfil.html', {
        'treinador': _treinador(request),
        'total': pokemons.count(),
        'total_capturados': pokemons.filter(capturado=True).count(),
        'total_favoritos': pokemons.filter(favorito=True).count(),
    })


@login_required
def editar_perfil(request):
    form = PerfilForm(request.POST or None, instance=_treinador(request))
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Perfil atualizado.')
        return redirect('perfil')
    return render(request, 'perfil_form.html', {'form': form})
