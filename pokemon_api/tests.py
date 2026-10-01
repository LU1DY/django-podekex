from django.test import TestCase
from django.urls import reverse

from .models import Habilidade, Pokemon, Regiao, Treinador


def criar_pokemon(**kwargs):
    dados = {
        'nome': 'pikachu',
        'id_pokemon': 25,
        'tipos': ['electric'],
        'habilidades': ['static'],
        'hp': 35,
        'ataque': 55,
        'defesa': 40,
        'velocidade': 90,
    }
    dados.update(kwargs)
    return Pokemon.objects.create(**dados)


class RegiaoModelTest(TestCase):
    def test_regioes_iniciais_existem(self):
        self.assertEqual(Regiao.objects.count(), 9)

    def test_por_numero_retorna_regiao_correta(self):
        self.assertEqual(Regiao.por_numero(1).nome, 'Kanto')
        self.assertEqual(Regiao.por_numero(151).nome, 'Kanto')
        self.assertEqual(Regiao.por_numero(152).nome, 'Johto')
        self.assertEqual(Regiao.por_numero(1025).nome, 'Paldea')

    def test_por_numero_fora_do_intervalo(self):
        self.assertIsNone(Regiao.por_numero(5000))


class PokemonModelTest(TestCase):
    def test_regiao_definida_automaticamente(self):
        pokemon = criar_pokemon(id_pokemon=25)
        self.assertEqual(pokemon.regiao.nome, 'Kanto')

    def test_regiao_aceita_numero_como_texto(self):
        pokemon = criar_pokemon(id_pokemon='252')
        self.assertEqual(pokemon.regiao.nome, 'Hoenn')

    def test_total_atributos(self):
        pokemon = criar_pokemon()
        self.assertEqual(pokemon.total_atributos, 220)

    def test_str_formata_numero(self):
        self.assertEqual(str(criar_pokemon()), '#025 pikachu')

    def test_habilidades_sao_catalogadas(self):
        criar_pokemon(habilidades=['static', 'lightning-rod'])
        self.assertEqual(
            set(Habilidade.objects.values_list('nome', flat=True)),
            {'static', 'lightning-rod'},
        )


class RelacionamentoTreinadorTest(TestCase):
    def test_treinador_tem_varios_pokemons(self):
        ash = Treinador.objects.create(nome='Ash', cidade_natal='Pallet')
        criar_pokemon(nome='pikachu', id_pokemon=25, treinador=ash)
        criar_pokemon(nome='charmander', id_pokemon=4, treinador=ash)
        self.assertEqual(ash.pokemons.count(), 2)

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
        ash = Treinador.objects.create(nome='Ash')
        criar_pokemon(nome='pikachu', id_pokemon=25, tipos=['electric'],
                      capturado=True, favorito=True, treinador=ash)
        criar_pokemon(nome='charizard', id_pokemon=6, tipos=['fire', 'flying'],
                      capturado=True)
        criar_pokemon(nome='chikorita', id_pokemon=152, tipos=['grass'])

        resposta = self.client.get(reverse('home'))
        contexto = resposta.context

        self.assertEqual(contexto['total_colecao'], 3)
        self.assertEqual(contexto['total_capturados'], 2)
        self.assertEqual(contexto['total_favoritos'], 1)
        self.assertEqual(contexto['tipos_descobertos'], 4)
        self.assertEqual(contexto['total_treinadores'], 1)
        self.assertEqual(contexto['sem_treinador'], 2)
        self.assertEqual(contexto['mais_forte'].nome, 'pikachu')

    def test_agrupamento_por_regiao(self):
        criar_pokemon(nome='pikachu', id_pokemon=25)
        criar_pokemon(nome='eevee', id_pokemon=133)
        criar_pokemon(nome='chikorita', id_pokemon=152)

        resposta = self.client.get(reverse('home'))
        totais = {r.nome: r.total for r in resposta.context['por_regiao']}

        self.assertEqual(totais, {'Kanto': 2, 'Johto': 1})

    def test_pagina_exibe_nome_do_pokemon_recente(self):
        criar_pokemon(nome='bulbasaur', id_pokemon=1)
        resposta = self.client.get(reverse('home'))
        self.assertContains(resposta, 'bulbasaur')
