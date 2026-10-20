from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .services import buscar_dados_pokemon, montar_pokemon
from django.db.models import Count
from .forms import PokemonForm
from .models import Pokemon, Treinador, Regiao
# Create your views here.

def buscar_pokemon(request):
    erro = None
    pokemon = None
    if request.method == "POST":

        id_nome = request.POST.get("pokemon")

        if id_nome:
            dados = buscar_dados_pokemon(id_nome)

            if dados is None:
                erro = f'Nenhum Pokémon encontrado com o nome ou número "{id_nome}".'
            else:
                pokemon = montar_pokemon(dados)

    else:
        print("Erro ao buscar pokemon!")

    return render(request, "buscar_dados_pokemon.html", {"pokemon": pokemon, "erro": erro})
def home(request):
    pokemons = Pokemon.objects.all()

    favoritos = pokemons.filter(favorito=True)

    tipos = set()
    for lista in pokemons.values_list('tipos', flat=True):
        tipos.update(lista)

    treinadores = Treinador.objects.select_related('regiao').annotate(total=Count('pokemons'))

    contexto = {
        'total_colecao': pokemons.count(),
        'total_capturados': pokemons.filter(capturado=True).count(),
        'total_favoritos': favoritos.count(),
        'tipos_descobertos': len(tipos),
        'total_treinadores': Treinador.objects.count(),
        'total_regioes': Regiao.objects.count(),
        'treinadores': treinadores.order_by('-total', 'nome'),
        'favoritos': favoritos[:3],
    }
    return render(request, 'home.html', contexto)

# C - POST
def salvar_pokemon(request):
    if request.method == "POST":
        form = PokemonForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Pokémon adicionado à coleção.")
            return redirect('listar_pokemons')
    else:
        inicial = {}
        id_pokemon = request.GET.get("id_pokemon")

        if id_pokemon:
            dados = buscar_dados_pokemon(id_pokemon)
            if dados:
                inicial = montar_pokemon(dados)

        form = PokemonForm(initial=inicial)

    return render(request, "form_pokemon.html", {"form": form})

# R - READ
def listar_pokemons(request):
    pokemons = Pokemon.objects.select_related('treinador')

    return render(request, "listar_pokemons.html", {'pokemons': pokemons})

# U - UPDATE
def editar_pokemon(request, pk):
    pokemon = get_object_or_404(Pokemon, pk=pk)

    if request.method == "POST":
        form = PokemonForm(request.POST, instance=pokemon)
        if form.is_valid():
            form.save()
            messages.success(request, "Pokémon atualizado.")
            return redirect("listar_pokemons")
    else:
        form = PokemonForm(instance=pokemon)

    return render(request, "form_pokemon.html", {'titulo': pokemon.nome, 'form': form})

# D - DELETE
def remover_pokemon(request, pk):
    pokemon = get_object_or_404(Pokemon, pk=pk)

    if request.method == "POST":
        pokemon.delete()
        messages.success(request, "Pokémon removido da coleção.")
        return redirect("listar_pokemons")

    return render(request, "confirmar_exclusao.html", {"pokemon": pokemon})
