from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path("buscar_dados_pokemon/", views.buscar_pokemon, name='buscar_dados_pokemon'),
    path("salvar_pokemon/", views.salvar_pokemon, name="salvar_pokemon"),
    path("listar_pokemons/", views.listar_pokemons, name="listar_pokemons")
]