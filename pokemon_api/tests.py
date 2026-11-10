from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .forms import RegistroForm
from .models import Pokemon, PokemonHabilidade, Regiao, Treinador

SENHA = 'SenhaForte#123'

DADOS_API = {
    'id': 25,
    'name': 'pikachu',
    'types': [{'type': {'name': 'electric'}}],
    'height': 4,
    'weight': 60,
    'abilities': [
        {'ability': {'name': 'static'}, 'is_hidden': False},
        {'ability': {'name': 'lightning-rod'}, 'is_hidden': True},
    ],
    'stats': [{'base_stat': v} for v in (35, 55, 40, 50, 50, 90)],
    'sprites': {'front_default': 'https://exemplo.com/25.png'},
}


def criar_usuario(username='ash'):
    usuario = User.objects.create_user(username, password=SENHA)
    treinador = Treinador.objects.create(usuario=usuario, nome=username.title())
    return usuario, treinador


def criar_pokemon(treinador, **kwargs):
    dados = {'nome': 'pikachu', 'id_pokemon': 25, 'tipos': ['electric'], 'hp': 35}
    dados.update(kwargs)
    return Pokemon.objects.create(treinador=treinador, **dados)


# ---------------------------------------------------------------- unitários

class ModelsTest(TestCase):
    def test_regioes_iniciais_existem(self):
        self.assertEqual(Regiao.objects.count(), 9)
        self.assertTrue(Regiao.objects.filter(nome='Kanto', numero_inicial=1, numero_final=151).exists())

    def test_pokemon_tem_valores_padrao(self):
        _, treinador = criar_usuario()
        pokemon = criar_pokemon(treinador)
        self.assertFalse(pokemon.favorito)
        self.assertFalse(pokemon.capturado)
        self.assertIsNotNone(pokemon.data_captura)

    def test_excluir_treinador_mantem_pokemon(self):
        _, treinador = criar_usuario()
        pokemon = criar_pokemon(treinador)
        treinador.delete()
        pokemon.refresh_from_db()
        self.assertIsNone(pokemon.treinador)

    def test_formulario_de_registro_cria_treinador(self):
        form = RegistroForm({
            'username': 'misty', 'nome': 'Misty', 'cidade_natal': 'Cerulean',
            'password1': SENHA, 'password2': SENHA,
        })
        self.assertTrue(form.is_valid(), form.errors)
        usuario = form.save()
        self.assertEqual(usuario.treinador.nome, 'Misty')


# ---------------------------------------------------------------- interface

class BuscaPublicaTest(TestCase):
    @patch('pokemon_api.views.buscar_dados_pokemon', return_value=DADOS_API)
    def test_visitante_pode_buscar(self, _):
        resposta = self.client.get(reverse('buscar_dados_pokemon'), {'pokemon': 'pikachu'})
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'pikachu')
        self.assertContains(resposta, 'Entrar para salvar')

    @patch('pokemon_api.views.buscar_dados_pokemon', return_value=None)
    def test_busca_sem_resultado_mostra_erro(self, _):
        resposta = self.client.get(reverse('buscar_dados_pokemon'), {'pokemon': 'xxxx'})
        self.assertContains(resposta, 'Nenhum Pokémon encontrado')

    @patch('pokemon_api.views.buscar_dados_pokemon', return_value=DADOS_API)
    def test_logado_ve_botao_de_salvar(self, _):
        usuario, _ = criar_usuario()
        self.client.force_login(usuario)
        resposta = self.client.get(reverse('buscar_dados_pokemon'), {'pokemon': 'pikachu'})
        self.assertContains(resposta, 'Adicionar à minha coleção')


class SalvarPokemonTest(TestCase):
    def test_salvar_exige_login(self):
        resposta = self.client.post(reverse('salvar_pokemon'), {'id_pokemon': 25})
        self.assertRedirects(resposta, f"{reverse('login')}?next={reverse('salvar_pokemon')}")
        self.assertEqual(Pokemon.objects.count(), 0)

    @patch('pokemon_api.views.buscar_dados_pokemon', return_value=DADOS_API)
    def test_salvar_grava_pokemon_regiao_e_habilidades(self, _):
        usuario, treinador = criar_usuario()
        self.client.force_login(usuario)
        self.client.post(reverse('salvar_pokemon'), {'id_pokemon': 25})
        pokemon = Pokemon.objects.get()
        self.assertEqual(pokemon.treinador, treinador)
        self.assertEqual(pokemon.regiao.nome, 'Kanto')
        self.assertEqual(pokemon.tipos, ['electric'])
        self.assertEqual(pokemon.habilidades.count(), 2)
        self.assertTrue(PokemonHabilidade.objects.get(habilidade__nome='lightning-rod').oculta)

    @patch('pokemon_api.views.buscar_dados_pokemon', return_value=DADOS_API)
    def test_nao_duplica_pokemon_na_colecao(self, _):
        usuario, _ = criar_usuario()
        self.client.force_login(usuario)
        for _ in range(2):
            self.client.post(reverse('salvar_pokemon'), {'id_pokemon': 25})
        self.assertEqual(Pokemon.objects.count(), 1)


class ColecaoTest(TestCase):
    def setUp(self):
        self.usuario, self.treinador = criar_usuario('ash')
        self.outro_usuario, self.outro_treinador = criar_usuario('gary')
        self.client.force_login(self.usuario)

    def test_paginas_exigem_login(self):
        self.client.logout()
        for nome in ('listar_pokemons', 'consultas', 'relatorio', 'perfil'):
            resposta = self.client.get(reverse(nome))
            self.assertEqual(resposta.status_code, 302, nome)

    def test_lista_mostra_so_a_colecao_do_usuario(self):
        criar_pokemon(self.treinador, nome='pikachu')
        criar_pokemon(self.outro_treinador, nome='eevee', id_pokemon=133)
        resposta = self.client.get(reverse('listar_pokemons'))
        self.assertContains(resposta, 'pikachu')
        self.assertNotContains(resposta, 'eevee')

    def test_pokemon_de_outro_treinador_da_404(self):
        alheio = criar_pokemon(self.outro_treinador)
        for nome in ('detalhes_pokemon', 'editar_pokemon'):
            self.assertEqual(self.client.get(reverse(nome, args=[alheio.pk])).status_code, 404)
        self.client.post(reverse('remover_pokemon', args=[alheio.pk]))
        self.assertTrue(Pokemon.objects.filter(pk=alheio.pk).exists())

    def test_editar_atualiza_observacoes_e_marcas(self):
        pokemon = criar_pokemon(self.treinador)
        self.client.post(reverse('editar_pokemon', args=[pokemon.pk]), {
            'observacoes': 'Meu primeiro', 'favorito': 'on', 'capturado': 'on',
        })
        pokemon.refresh_from_db()
        self.assertEqual(pokemon.observacoes, 'Meu primeiro')
        self.assertTrue(pokemon.favorito and pokemon.capturado)

    def test_remover_pokemon(self):
        pokemon = criar_pokemon(self.treinador)
        self.client.post(reverse('remover_pokemon', args=[pokemon.pk]))
        self.assertFalse(Pokemon.objects.filter(pk=pokemon.pk).exists())

    def test_dashboard_mostra_indicadores(self):
        criar_pokemon(self.treinador, capturado=True, favorito=True)
        resposta = self.client.get(reverse('home'))
        self.assertEqual(resposta.context['total'], 1)
        self.assertEqual(resposta.context['total_capturados'], 1)
        self.assertEqual(resposta.context['total_tipos'], 1)

    def test_dashboard_redireciona_visitante_para_a_busca(self):
        self.client.logout()
        self.assertRedirects(self.client.get(reverse('home')), reverse('buscar_dados_pokemon'))

    def test_consultas_filtram_por_nome_e_tipo(self):
        criar_pokemon(self.treinador, nome='pikachu')
        criar_pokemon(self.treinador, nome='charmander', id_pokemon=4, tipos=['fire'])
        url = reverse('consultas')
        self.assertEqual(len(self.client.get(url, {'q': 'pika'}).context['pokemons']), 1)
        self.assertEqual(len(self.client.get(url, {'q': '4'}).context['pokemons']), 1)
        self.assertEqual(len(self.client.get(url, {'tipo': 'fire'}).context['pokemons']), 1)

    def test_relatorio_e_csv(self):
        criar_pokemon(self.treinador)
        self.assertEqual(self.client.get(reverse('relatorio')).context['total'], 1)
        csv_resposta = self.client.get(reverse('exportar_relatorio'))
        self.assertEqual(csv_resposta['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('Pokémon na coleção;1', csv_resposta.content.decode())

    def test_editar_perfil(self):
        self.client.post(reverse('editar_perfil'), {'nome': 'Ash Ketchum', 'cidade_natal': 'Pallet'})
        self.treinador.refresh_from_db()
        self.assertEqual(self.treinador.nome, 'Ash Ketchum')


class CadastroTest(TestCase):
    def test_cadastro_loga_o_usuario(self):
        resposta = self.client.post(reverse('registrar'), {
            'username': 'brock', 'nome': 'Brock', 'cidade_natal': 'Pewter',
            'password1': SENHA, 'password2': SENHA,
        })
        self.assertRedirects(resposta, reverse('home'))
        self.assertTrue(Treinador.objects.filter(usuario__username='brock').exists())
