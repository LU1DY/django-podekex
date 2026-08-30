import requests


def buscar_dados_pokemon(pokemon):
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon.lower()}"

    resposta = requests.get(url)

    if resposta.status_code == 200:
        return resposta.json()

    return None
