from django.db.models import Avg, Count, F
from django.shortcuts import get_object_or_404, redirect, render

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
        'habilidades': [item['ability']['name'] for item in dados['abilities']],
        'hp': dados['stats'][0]['base_stat'],
        'ataque': dados['stats'][1]['base_stat'],
        'defesa': dados['stats'][2]['base_stat'],
        'velocidade': dados['stats'][5]['base_stat'],
        'sprite_url': dados['sprites']['front_default'],
    }


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
    else:
        id_pokemon = request.GET.get('id_pokemon')
        if id_pokemon:
            dados = buscar_dados_pokemon(id_pokemon)
            if dados:
                pokemon = _pokemon_da_api(dados)

    contexto = _base_context()
    contexto.update({
        'pokemon': pokemon,
        'treinadores': Treinador.objects.all(),
    })
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


# D - DELETE
def remover_pokemon(request, pk):
    pokemon = get_object_or_404(Pokemon, pk=pk)
    if request.method == 'POST':
        pokemon.delete()
    return redirect('listar_pokemons')
