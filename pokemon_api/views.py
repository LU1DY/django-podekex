from django.shortcuts import render, redirect
from .services import buscar_dados_pokemon
from .models import Pokemon
# Create your views here.

def buscar_pokemon(request):
    erro = None
    pokemon = None
    if request.method == "POST":

        id_nome = request.POST.get("pokemon")

        if id_nome:
            dados = buscar_dados_pokemon(id_nome)
            pokemon = {
                "nome": dados['name'], 
                "id_pokemon": dados['id'], 
                
                "tipos": [t["type"]["name"] for t in dados["types"]],
                
                "altura": dados["height"],
                "peso": dados["weight"],
                "habilidades": [habilidade["ability"]["name"] for habilidade in dados["abilities"]],
                
                "hp": dados["stats"][0]["base_stat"], 
                "ataque": dados["stats"][1]["base_stat"], 
                "defesa": dados["stats"][2]["base_stat"], 
                "velocidade": dados["stats"][5]["base_stat"], 
                "sprite_url": dados["sprites"]["front_default"]
                }
            
    else:
        print("Erro ao buscar pokemon!")

    return render(request, "buscar_dados_pokemon.html", {"pokemon": pokemon, "erro": erro})

# C - POST 
def salvar_pokemon(request):
    pokemon = None  
    if request.method == "POST":
        nome = request.POST.get("nome")
        id_pokemon = request.POST.get("id_pokemon")
        tipos = request.POST.get("tipos")
        habilidades = request.POST.get("habilidades")
        altura = request.POST.get("altura", 0)
        peso = request.POST.get("peso", 0)

        hp = request.POST.get("hp", 0)
        ataque = request.POST.get("ataque", 0)
        defesa = request.POST.get("defesa", 0)
        velocidade = request.POST.get("velocidade", 0)

        sprite_url = request.POST.get("sprite_url", "")
        observacoes = request.POST.get("observacoes", "")

        capturado = "capturado" in request.POST
        favorito = "favorito" in request.POST

        if nome and id_pokemon:
            Pokemon.objects.create(
                nome=nome,
                id_pokemon=id_pokemon,
                tipos=tipos,
                habilidades=habilidades,
                altura=altura,
                peso=peso,
                hp=hp,
                ataque=ataque,
                defesa=defesa,
                velocidade=velocidade,
                sprite_url=sprite_url,
                observacoes=observacoes,
                capturado=capturado,
                favorito=favorito
            )
            return redirect('buscar_dados_pokemon')

    else:
        id_pokemon = request.GET.get("id_pokemon")

        if id_pokemon:
            dados = buscar_dados_pokemon(id_pokemon)
            if dados:
                  pokemon = {
                    "nome": dados['name'], 
                    "id_pokemon": dados['id'], 
                    
                    "tipos": [t["type"]["name"] for t in dados["types"]],
                    
                    "altura": dados["height"],
                    "peso": dados["weight"],
                    "habilidades": [habilidade["ability"]["name"] for habilidade in dados["abilities"]],
                    
                    "hp": dados["stats"][0]["base_stat"], 
                    "ataque": dados["stats"][1]["base_stat"], 
                    "defesa": dados["stats"][2]["base_stat"], 
                    "velocidade": dados["stats"][5]["base_stat"], 
                    "sprite_url": dados["sprites"]["front_default"]
                }

    return render(request, "form_add_pokemon.html", {"pokemon": pokemon})

# R - READ
def listar_pokemons(request):
    pokemons = Pokemon.objects.all()
    return render(request, "listar_pokemons.html", {'pokemons': pokemons})
    
# U - UPDATE 
def editar_pokemon(request):
    return

# D - DELETE
def remover_pokemon(request):
    return
