from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path("buscar_dados_pokemon/", views.buscar_pokemon, name='buscar_dados_pokemon'),
    path("salvar_pokemon/", views.salvar_pokemon, name="salvar_pokemon"),
    path("listar_pokemons/", views.listar_pokemons, name="listar_pokemons"),
    path("<int:pk>/remover_pokemon/", views.remover_pokemon, name="remover_pokemon"),
    path("<int:pk>/editar_pokemon/", views.editar_pokemon, name="editar_pokemon"),
    path("<int:pk>/detalhes_pokemon/", views.detalhes_pokemon, name="detalhes_pokemon"),

    # CRUD de Habilidade (N:N com through)
    path("listar_habilidades/", views.listar_habilidades, name="listar_habilidades"),
    path("criar_habilidade/", views.criar_habilidade, name="criar_habilidade"),
    path("<int:pk>/detalhes_habilidade/", views.detalhes_habilidade, name="detalhes_habilidade"),
    path("<int:pk>/editar_habilidade/", views.editar_habilidade, name="editar_habilidade"),
    path("<int:pk>/remover_habilidade/", views.remover_habilidade, name="remover_habilidade"),
]