from django import template

register = template.Library()

CORES_POR_TIPO = {
    'normal': '#a8a878', 'fire': '#f08030', 'water': '#6890f0', 'electric': '#f8d030',
    'grass': '#78c850', 'ice': '#98d8d8', 'fighting': '#c03028', 'poison': '#a040a0',
    'ground': '#e0c068', 'flying': '#a890f0', 'psychic': '#f85888', 'bug': '#a8b820',
    'rock': '#b8a038', 'ghost': '#705898', 'dragon': '#7038f8', 'dark': '#705848',
    'steel': '#b8b8d0', 'fairy': '#ee99ac',
}

@register.filter
def cor_tipo(tipo):
    """Devolve a cor (hex) de um tipo, para colorir a bolinha da badge."""
    if not tipo:
        return '#a8a878'
    return CORES_POR_TIPO.get(tipo.lower(), '#a8a878')