from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),

    # Busca na API: livre, sem login
    path('buscar_dados_pokemon/', views.buscar_pokemon, name='buscar_dados_pokemon'),

    # CRUD de Pokémon: exige login
    path('salvar_pokemon/', views.salvar_pokemon, name='salvar_pokemon'),
    path('listar_pokemons/', views.listar_pokemons, name='listar_pokemons'),
    path('<int:pk>/detalhes_pokemon/', views.detalhes_pokemon, name='detalhes_pokemon'),
    path('<int:pk>/editar_pokemon/', views.editar_pokemon, name='editar_pokemon'),
    path('<int:pk>/remover_pokemon/', views.remover_pokemon, name='remover_pokemon'),

    path('consultas/', views.consultas, name='consultas'),
    path('relatorio/', views.relatorio, name='relatorio'),
    path('relatorio/exportar/', views.exportar_relatorio, name='exportar_relatorio'),

    # Autenticação e perfil
    path('login/', auth_views.LoginView.as_view(
        template_name='login.html', redirect_authenticated_user=True,
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('cadastrar/', views.registrar, name='registrar'),
    path('perfil/', views.perfil, name='perfil'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
]
