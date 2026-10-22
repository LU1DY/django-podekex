from django.contrib import admin
from .models import Captura, Habilidade, Pokemon, PokemonHabilidade, Regiao, Treinador


@admin.register(Regiao)
class RegiaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'numero_inicial', 'numero_final')


@admin.register(Treinador)
class TreinadorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cidade_natal', 'data_cadastro')
    search_fields = ('nome',)


class PokemonHabilidadeInline(admin.TabularInline):
    model = PokemonHabilidade
    extra = 1
    autocomplete_fields = ('habilidade',)


class CapturaInline(admin.StackedInline):
    model = Captura
    extra = 0


@admin.register(Habilidade)
class HabilidadeAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)


@admin.register(Pokemon)
class PokemonAdmin(admin.ModelAdmin):
    list_display = ('nome', 'id_pokemon', 'treinador', 'regiao', 'capturado', 'favorito')
    list_filter = ('regiao', 'treinador', 'capturado', 'favorito')
    search_fields = ('nome',)
    inlines = (CapturaInline, PokemonHabilidadeInline)
