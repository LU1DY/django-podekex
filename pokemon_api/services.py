import requests


def buscar_dados_pokemon(pokemon):
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon.lower()}"

    resposta = requests.get(url)

    if resposta.status_code == 200:
        return resposta.json()

    return None

def montar_pokemon(dados):
    return {
        "nome": dados["name"],
        "id_pokemon": dados["id"],
        "tipos": [t["type"]["name"] for t in dados["types"]],
        "altura": dados["height"],
        "peso": dados["weight"],
        "habilidades": [h["ability"]["name"] for h in dados["abilities"]],
        "hp": dados["stats"][0]["base_stat"],
        "ataque": dados["stats"][1]["base_stat"],
        "defesa": dados["stats"][2]["base_stat"],
        "velocidade": dados["stats"][5]["base_stat"],
        "sprite_url": dados["sprites"]["front_default"],
    }
