from django.contrib import admin

from .models import Habilidade, Pokemon, PokemonHabilidade, Regiao, Treinador

admin.site.register(Regiao)
admin.site.register(Treinador)
admin.site.register(Habilidade)
admin.site.register(Pokemon)
admin.site.register(PokemonHabilidade)
