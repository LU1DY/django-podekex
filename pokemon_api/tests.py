from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from .forms import PokemonForm
from .models import Pokemon, Regiao, Treinador

DADOS_API = {
    'name': 'bulbasaur',
    'id': 1,
    'types': [{'type': {'name': 'grass'}}, {'type': {'name': 'poison'}}],
    'height': 7,
    'weight': 69,
    'abilities': [{'ability': {'name': 'overgrow'}}, {'ability': {'name': 'chlorophyll'}}],
    'stats': [{'base_stat': 45}, {'base_stat': 49}, {'base_stat': 49},
              {'base_stat': 65}, {'base_stat': 65}, {'base_stat': 45}],
    'sprites': {'front_default': 'https://exemplo.com/1.png'},
}

DADOS_FORM = {
    'nome': 'bulbasaur',
    'id_pokemon': 1,
    'tipos': 'Grass, poison',
    'habilidades': 'overgrow, chlorophyll',
    'altura': '0.7',
    'peso': '6.9',
    'hp': 45,
    'ataque': 49,
    'defesa': 49,
    'velocidade': 45,
    'sprite_url': 'https://exemplo.com/1.png',
    'observacoes': '',
}


def criar_pokemon(**kwargs):
    dados = {'nome': 'pikachu', 'id_pokemon': 25, 'tipos': ['electric']}
    dados.update(kwargs)
    return Pokemon.objects.create(**dados)


class RelacionamentosTest(TestCase):
    def test_treinador_tem_varios_pokemons(self):
        ash = Treinador.objects.create(nome='Ash')
        criar_pokemon(nome='pikachu', id_pokemon=25, treinador=ash)
        criar_pokemon(nome='charmander', id_pokemon=4, treinador=ash)
        self.assertEqual(ash.pokemons.count(), 2)

    def test_regiao_tem_varios_treinadores(self):
        kanto = Regiao.objects.create(nome='Kanto')
        Treinador.objects.create(nome='Ash', regiao=kanto)
        Treinador.objects.create(nome='Misty', regiao=kanto)
        self.assertEqual(kanto.treinadores.count(), 2)

    def test_excluir_treinador_mantem_pokemon(self):
        ash = Treinador.objects.create(nome='Ash')
        pokemon = criar_pokemon(treinador=ash)
        ash.delete()
        pokemon.refresh_from_db()
        self.assertIsNone(pokemon.treinador)


class DashboardTest(TestCase):
    def test_dashboard_vazio_carrega(self):
        resposta = self.client.get(reverse('home'))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.context['total_colecao'], 0)

    def test_indicadores_refletem_o_banco(self):
        kanto = Regiao.objects.create(nome='Kanto')
        ash = Treinador.objects.create(nome='Ash', regiao=kanto)
        criar_pokemon(nome='pikachu', tipos=['electric'], capturado=True, favorito=True, treinador=ash)
        criar_pokemon(nome='charizard', id_pokemon=6, tipos=['fire', 'flying'], capturado=True)
        criar_pokemon(nome='chikorita', id_pokemon=152, tipos=['grass'])

        contexto = self.client.get(reverse('home')).context

        self.assertEqual(contexto['total_colecao'], 3)
        self.assertEqual(contexto['total_capturados'], 2)
        self.assertEqual(contexto['total_favoritos'], 1)
        self.assertEqual(contexto['tipos_descobertos'], 4)
        self.assertEqual(contexto['total_treinadores'], 1)
        self.assertEqual(contexto['total_regioes'], 1)

    def test_pokemon_por_treinador(self):
        ash = Treinador.objects.create(nome='Ash')
        Treinador.objects.create(nome='Misty')
        criar_pokemon(nome='pikachu', id_pokemon=25, treinador=ash)
        criar_pokemon(nome='charmander', id_pokemon=4, treinador=ash)

        treinadores = self.client.get(reverse('home')).context['treinadores']
        totais = {t.nome: t.total for t in treinadores}

        self.assertEqual(totais, {'Ash': 2, 'Misty': 0})


class PokemonFormTest(TestCase):
    def test_tipos_e_habilidades_viram_lista(self):
        form = PokemonForm(DADOS_FORM)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['tipos'], ['grass', 'poison'])
        self.assertEqual(form.cleaned_data['habilidades'], ['overgrow', 'chlorophyll'])

    def test_exige_ao_menos_um_tipo(self):
        form = PokemonForm({**DADOS_FORM, 'tipos': ' , '})
        self.assertFalse(form.is_valid())
        self.assertIn('tipos', form.errors)

    def test_numero_da_pokedex_deve_ser_positivo(self):
        form = PokemonForm({**DADOS_FORM, 'id_pokemon': 0})
        self.assertFalse(form.is_valid())
        self.assertIn('id_pokemon', form.errors)

    def test_atributos_nao_podem_ser_negativos(self):
        form = PokemonForm({**DADOS_FORM, 'hp': -1})
        self.assertFalse(form.is_valid())
        self.assertIn('hp', form.errors)

    def test_edicao_mostra_listas_separadas_por_virgula(self):
        pokemon = criar_pokemon(tipos=['fire', 'flying'])
        form = PokemonForm(instance=pokemon)
        self.assertEqual(form.initial['tipos'], 'fire, flying')


class CrudPokemonTest(TestCase):
    def test_formulario_de_cadastro_carrega_vazio(self):
        resposta = self.client.get(reverse('salvar_pokemon'))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Cadastrar Pokémon')

    @patch('pokemon_api.views.buscar_dados_pokemon', return_value=DADOS_API)
    def test_formulario_vem_preenchido_com_dados_da_api(self, _):
        resposta = self.client.get(reverse('salvar_pokemon'), {'id_pokemon': 1})
        self.assertContains(resposta, 'bulbasaur')
        self.assertContains(resposta, 'grass, poison')

    def test_cadastrar_pokemon(self):
        resposta = self.client.post(reverse('salvar_pokemon'), DADOS_FORM)
        self.assertRedirects(resposta, reverse('listar_pokemons'))
        pokemon = Pokemon.objects.get()
        self.assertEqual(pokemon.nome, 'bulbasaur')
        self.assertEqual(pokemon.tipos, ['grass', 'poison'])

    def test_cadastro_invalido_nao_salva_e_mostra_erro(self):
        resposta = self.client.post(reverse('salvar_pokemon'), {**DADOS_FORM, 'nome': ''})
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'erro-campo')
        self.assertEqual(Pokemon.objects.count(), 0)

    def test_listar_mostra_os_pokemons_salvos(self):
        criar_pokemon(nome='bulbasaur', id_pokemon=1)
        criar_pokemon(nome='charmander', id_pokemon=4)
        resposta = self.client.get(reverse('listar_pokemons'))
        self.assertContains(resposta, 'bulbasaur')
        self.assertContains(resposta, 'charmander')

    def test_editar_pokemon(self):
        pokemon = criar_pokemon()
        dados = {**DADOS_FORM, 'nome': 'raichu', 'id_pokemon': 26, 'favorito': 'on'}
        resposta = self.client.post(reverse('editar_pokemon', args=[pokemon.pk]), dados)
        self.assertRedirects(resposta, reverse('listar_pokemons'))
        pokemon.refresh_from_db()
        self.assertEqual(pokemon.nome, 'raichu')
        self.assertTrue(pokemon.favorito)

    def test_tela_de_edicao_carrega_os_dados(self):
        pokemon = criar_pokemon(nome='pikachu')
        resposta = self.client.get(reverse('editar_pokemon', args=[pokemon.pk]))
        self.assertContains(resposta, 'Editar Pokémon')
        self.assertContains(resposta, 'pikachu')

    def test_editar_pokemon_inexistente_retorna_404(self):
        resposta = self.client.get(reverse('editar_pokemon', args=[999]))
        self.assertEqual(resposta.status_code, 404)

    def test_remover_pede_confirmacao_e_depois_exclui(self):
        pokemon = criar_pokemon()
        url = reverse('remover_pokemon', args=[pokemon.pk])

        resposta = self.client.get(url)
        self.assertContains(resposta, 'Sim, remover')
        self.assertEqual(Pokemon.objects.count(), 1)

        resposta = self.client.post(url)
        self.assertRedirects(resposta, reverse('listar_pokemons'))
        self.assertEqual(Pokemon.objects.count(), 0)

