import requests


def buscar_dados_pokemon(pokemon):
    """Consulta a PokéAPI. Devolve o JSON ou None se não encontrar / falhar."""
    url = f'https://pokeapi.co/api/v2/pokemon/{str(pokemon).strip().lower()}'
    try:
        resposta = requests.get(url, timeout=10)
    except requests.RequestException:
        return None
    return resposta.json() if resposta.status_code == 200 else None
