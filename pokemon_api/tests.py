from datetime import date

from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from .models import Captura, Habilidade, Pokemon, PokemonHabilidade, Regiao, Treinador
from .views import _pokemon_da_api


def criar_pokemon(**kwargs):
    """Cria um Pokémon. `habilidades` aceita nomes ou pares (nome, oculta)."""
    habilidades = kwargs.pop('habilidades', ['static'])
    dados = {
        'nome': 'pikachu',
        'id_pokemon': 25,
        'tipos': ['electric'],
        'hp': 35,
        'ataque': 55,
        'defesa': 40,
        'velocidade': 90,
    }
    dados.update(kwargs)
    pokemon = Pokemon.objects.create(**dados)
    pokemon.definir_habilidades([
        item if isinstance(item, tuple) else (item, False) for item in habilidades
    ])
    return pokemon


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


# ---------------------------------------------------------------------------
# Relação 1:1 — Pokémon <-> Captura (ficha de captura)
# ---------------------------------------------------------------------------

class CapturaModelTest(TestCase):
    def test_ficha_e_acessivel_pelos_dois_lados(self):
        pokemon = criar_pokemon()
        ficha = Captura.objects.create(pokemon=pokemon, apelido='Pika', nivel=12)
        self.assertEqual(pokemon.captura, ficha)
        self.assertEqual(ficha.pokemon, pokemon)

    def test_pokemon_so_pode_ter_uma_ficha(self):
        pokemon = criar_pokemon()
        Captura.objects.create(pokemon=pokemon)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Captura.objects.create(pokemon=pokemon)

    def test_excluir_pokemon_remove_a_ficha(self):
        pokemon = criar_pokemon()
        Captura.objects.create(pokemon=pokemon)
        pokemon.delete()
        self.assertEqual(Captura.objects.count(), 0)

    def test_nivel_precisa_estar_entre_1_e_100(self):
        pokemon = criar_pokemon()
        for invalido in (0, 101):
            with self.assertRaises(ValidationError):
                Captura(pokemon=pokemon, nivel=invalido).full_clean()
        Captura(pokemon=pokemon, nivel=100).full_clean()

    def test_str(self):
        ficha = Captura.objects.create(pokemon=criar_pokemon())
        self.assertEqual(str(ficha), 'Ficha de pikachu')


class DetalhesPokemonTest(TestCase):
    def test_tela_exibe_dados_do_pokemon_e_da_ficha(self):
        ash = Treinador.objects.create(nome='Ash', cidade_natal='Pallet')
        pokemon = criar_pokemon(treinador=ash, capturado=True)
        Captura.objects.create(
            pokemon=pokemon, apelido='Pika', nivel=42, pokebola='great',
            local='Floresta de Viridian', data_encontro=date(2026, 3, 9),
        )

        resposta = self.client.get(reverse('detalhes_pokemon', args=[pokemon.pk]))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'pikachu')
        self.assertContains(resposta, 'Pallet')
        self.assertContains(resposta, 'Pika')
        self.assertContains(resposta, '42')
        self.assertContains(resposta, 'Great Ball')
        self.assertContains(resposta, 'Floresta de Viridian')
        self.assertContains(resposta, '09/03/2026')

    def test_sem_ficha_mostra_chamada_para_preencher(self):
        pokemon = criar_pokemon()
        resposta = self.client.get(reverse('detalhes_pokemon', args=[pokemon.pk]))
        self.assertEqual(resposta.status_code, 200)
        self.assertIsNone(resposta.context['captura'])
        self.assertContains(resposta, 'ainda não tem ficha de captura')

    def test_tela_lista_habilidades_com_oculta_e_slot(self):
        pokemon = criar_pokemon(habilidades=[('static', False), ('lightning-rod', True)])
        resposta = self.client.get(reverse('detalhes_pokemon', args=[pokemon.pk]))
        self.assertContains(resposta, 'Static')
        self.assertContains(resposta, 'Lightning Rod')
        self.assertContains(resposta, 'Oculta')
        self.assertContains(resposta, 'Slot 2')

    def test_pokemon_inexistente_retorna_404(self):
        self.assertEqual(self.client.get(reverse('detalhes_pokemon', args=[999])).status_code, 404)

    def test_card_da_colecao_linka_para_detalhes(self):
        pokemon = criar_pokemon()
        resposta = self.client.get(reverse('listar_pokemons'))
        self.assertContains(resposta, reverse('detalhes_pokemon', args=[pokemon.pk]))


def dados_post_pokemon(**extra):
    dados = {
        'nome': 'bulbasaur', 'id_pokemon': '1', 'tipos': ['grass', 'poison'],
        'altura': '7', 'peso': '69', 'hp': '45', 'ataque': '49', 'defesa': '49',
        'velocidade': '45', 'sprite_url': '', 'observacoes': '',
        'habilidade_nome': ['overgrow', 'chlorophyll'], 'habilidade_oculta': ['0', '1'],
    }
    dados.update(extra)
    return dados


class FichaDeCapturaNoFormularioTest(TestCase):
    def test_criar_pokemon_com_ficha(self):
        resposta = self.client.post(reverse('salvar_pokemon'), dados_post_pokemon(**{
            'captura-apelido': 'Bulbi', 'captura-nivel': '15',
            'captura-pokebola': 'ultra', 'captura-local': 'Pallet',
            'captura-data_encontro': '2026-05-01',
        }))
        self.assertRedirects(resposta, reverse('listar_pokemons'))
        ficha = Pokemon.objects.get(nome='bulbasaur').captura
        self.assertEqual((ficha.apelido, ficha.nivel, ficha.pokebola), ('Bulbi', 15, 'ultra'))
        self.assertEqual(ficha.data_encontro, date(2026, 5, 1))

    def test_ficha_vazia_nao_e_criada(self):
        self.client.post(reverse('salvar_pokemon'), dados_post_pokemon())
        self.assertEqual(Pokemon.objects.count(), 1)
        self.assertEqual(Captura.objects.count(), 0)

    def test_editar_atualiza_a_ficha_existente(self):
        pokemon = criar_pokemon()
        Captura.objects.create(pokemon=pokemon, apelido='Antigo', nivel=5)
        self.client.post(reverse('editar_pokemon', args=[pokemon.pk]), dados_post_pokemon(
            nome='pikachu', id_pokemon='25',
            **{'captura-apelido': 'Novo', 'captura-nivel': '30'},
        ))
        self.assertEqual(Captura.objects.count(), 1)
        ficha = Captura.objects.get()
        self.assertEqual((ficha.apelido, ficha.nivel), ('Novo', 30))

    def test_editar_com_ficha_toda_vazia_remove_a_ficha(self):
        pokemon = criar_pokemon()
        Captura.objects.create(pokemon=pokemon, apelido='Pika', nivel=5)
        self.client.post(reverse('editar_pokemon', args=[pokemon.pk]),
                         dados_post_pokemon(nome='pikachu', id_pokemon='25'))
        self.assertEqual(Captura.objects.count(), 0)

    def test_nivel_invalido_nao_salva_e_mantem_o_que_foi_digitado(self):
        resposta = self.client.post(reverse('salvar_pokemon'), dados_post_pokemon(**{
            'captura-nivel': '150',
        }))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(Pokemon.objects.count(), 0)
        self.assertContains(resposta, 'O nível máximo é 100.')
        self.assertContains(resposta, 'bulbasaur')
        self.assertContains(resposta, 'chlorophyll')

    def test_edicao_com_nivel_invalido_nao_altera_nada_e_reexibe_o_formulario(self):
        pokemon = criar_pokemon(habilidades=['static'])
        resposta = self.client.post(reverse('editar_pokemon', args=[pokemon.pk]), dados_post_pokemon(
            nome='raichu', id_pokemon='26', **{'captura-nivel': '0'},
        ))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'O nível mínimo é 1.')
        self.assertContains(resposta, 'Editar Pokémon')
        self.assertContains(resposta, 'value="raichu"')
        pokemon.refresh_from_db()
        self.assertEqual(pokemon.nome, 'pikachu')
        self.assertEqual(list(pokemon.habilidades.values_list('nome', flat=True)), ['static'])

    def test_formulario_de_edicao_traz_a_ficha_preenchida(self):
        pokemon = criar_pokemon()
        Captura.objects.create(pokemon=pokemon, apelido='Pika', local='Cerulean')
        resposta = self.client.get(reverse('editar_pokemon', args=[pokemon.pk]))
        self.assertContains(resposta, 'value="Pika"')
        self.assertContains(resposta, 'value="Cerulean"')


# ---------------------------------------------------------------------------
# Relação N:N com through — Pokémon <-> Habilidade (PokemonHabilidade)
# ---------------------------------------------------------------------------

class PokemonHabilidadeModelTest(TestCase):
    def test_definir_habilidades_grava_ordem_e_flag_oculta(self):
        pokemon = criar_pokemon(habilidades=[('static', False), ('lightning-rod', True)])
        vinculos = list(pokemon.vinculos.select_related('habilidade'))
        self.assertEqual(
            [(v.habilidade.nome, v.ordem, v.oculta) for v in vinculos],
            [('static', 1, False), ('lightning-rod', 2, True)],
        )

    def test_habilidades_do_pokemon_via_m2m(self):
        pokemon = criar_pokemon(habilidades=['static', 'lightning-rod'])
        self.assertEqual(
            set(pokemon.habilidades.values_list('nome', flat=True)),
            {'static', 'lightning-rod'},
        )

    def test_habilidade_e_compartilhada_entre_pokemons(self):
        criar_pokemon(nome='pikachu', id_pokemon=25, habilidades=['static'])
        criar_pokemon(nome='raichu', id_pokemon=26, habilidades=['static'])
        static = Habilidade.objects.get(nome='static')
        self.assertEqual(Habilidade.objects.count(), 1)
        self.assertEqual(static.pokemons.count(), 2)

    def test_definir_substitui_as_habilidades_anteriores(self):
        pokemon = criar_pokemon(habilidades=['static'])
        pokemon.definir_habilidades([('lightning-rod', True)])
        self.assertEqual(list(pokemon.habilidades.values_list('nome', flat=True)), ['lightning-rod'])
        self.assertEqual(PokemonHabilidade.objects.filter(pokemon=pokemon).count(), 1)

    def test_nomes_repetidos_ou_vazios_sao_descartados(self):
        pokemon = criar_pokemon(habilidades=['static', 'Static', '  ', 'static '])
        self.assertEqual(pokemon.vinculos.count(), 1)

    def test_reaproveita_habilidade_existente_sem_diferenciar_caixa(self):
        existente = Habilidade.objects.create(nome='Static', descricao='Paralisa')
        pokemon = criar_pokemon(habilidades=['static'])
        self.assertEqual(Habilidade.objects.count(), 1)
        self.assertEqual(pokemon.habilidades.get(), existente)

    def test_mesmo_vinculo_nao_pode_repetir_no_banco(self):
        pokemon = criar_pokemon(habilidades=['static'])
        habilidade = Habilidade.objects.get(nome='static')
        with self.assertRaises(IntegrityError), transaction.atomic():
            PokemonHabilidade.objects.create(pokemon=pokemon, habilidade=habilidade)

    def test_excluir_pokemon_mantem_a_habilidade_no_catalogo(self):
        pokemon = criar_pokemon(habilidades=['static'])
        pokemon.delete()
        self.assertEqual(PokemonHabilidade.objects.count(), 0)
        self.assertTrue(Habilidade.objects.filter(nome='static').exists())

    def test_excluir_habilidade_desfaz_vinculos_e_mantem_pokemon(self):
        pokemon = criar_pokemon(habilidades=['static', 'lightning-rod'])
        Habilidade.objects.get(nome='static').delete()
        self.assertEqual(list(pokemon.habilidades.values_list('nome', flat=True)), ['lightning-rod'])
        self.assertTrue(Pokemon.objects.filter(pk=pokemon.pk).exists())


class HabilidadesNoFormularioTest(TestCase):
    def test_criar_pokemon_com_habilidades_normais_e_ocultas(self):
        self.client.post(reverse('salvar_pokemon'), dados_post_pokemon())
        pokemon = Pokemon.objects.get(nome='bulbasaur')
        self.assertEqual(
            [(v.habilidade.nome, v.ordem, v.oculta) for v in pokemon.vinculos.select_related('habilidade')],
            [('overgrow', 1, False), ('chlorophyll', 2, True)],
        )

    def test_linhas_em_branco_sao_ignoradas(self):
        self.client.post(reverse('salvar_pokemon'), dados_post_pokemon(
            habilidade_nome=['', 'overgrow', ''], habilidade_oculta=['0', '0', '1'],
        ))
        pokemon = Pokemon.objects.get(nome='bulbasaur')
        self.assertEqual(list(pokemon.habilidades.values_list('nome', flat=True)), ['overgrow'])

    def test_editar_troca_as_habilidades(self):
        pokemon = criar_pokemon(habilidades=['static'])
        self.client.post(reverse('editar_pokemon', args=[pokemon.pk]), dados_post_pokemon(
            nome='pikachu', id_pokemon='25',
            habilidade_nome=['lightning-rod'], habilidade_oculta=['1'],
        ))
        vinculo = pokemon.vinculos.select_related('habilidade').get()
        self.assertEqual((vinculo.habilidade.nome, vinculo.oculta), ('lightning-rod', True))

    def test_formulario_de_edicao_traz_habilidades_atuais(self):
        pokemon = criar_pokemon(habilidades=[('static', False), ('lightning-rod', True)])
        resposta = self.client.get(reverse('editar_pokemon', args=[pokemon.pk]))
        self.assertContains(resposta, 'value="static"')
        self.assertContains(resposta, 'value="lightning-rod"')
        self.assertContains(resposta, '<option value="1" selected>Oculta</option>', html=True)

    def test_catalogo_aparece_como_sugestao(self):
        Habilidade.objects.create(nome='intimidate')
        resposta = self.client.get(reverse('salvar_pokemon'))
        self.assertContains(resposta, '<option value="intimidate">', html=False)


class PokemonDaApiTest(TestCase):
    def test_habilidades_da_api_levam_o_flag_oculta(self):
        dados = {
            'name': 'bulbasaur', 'id': 1, 'height': 7, 'weight': 69,
            'types': [{'type': {'name': 'grass'}}],
            'abilities': [
                {'ability': {'name': 'overgrow'}, 'is_hidden': False, 'slot': 1},
                {'ability': {'name': 'chlorophyll'}, 'is_hidden': True, 'slot': 3},
            ],
            'stats': [{'base_stat': valor} for valor in (45, 49, 49, 65, 65, 45)],
            'sprites': {'front_default': 'https://exemplo.test/1.png'},
        }
        pokemon = _pokemon_da_api(dados)
        self.assertEqual(pokemon['habilidades'], [
            {'nome': 'overgrow', 'oculta': False},
            {'nome': 'chlorophyll', 'oculta': True},
        ])
        self.assertEqual(pokemon['velocidade'], 45)


# ---------------------------------------------------------------------------
# CRUD 2 — Habilidade
# ---------------------------------------------------------------------------

class ListarHabilidadesTest(TestCase):
    def test_lista_vazia_mostra_estado_vazio(self):
        resposta = self.client.get(reverse('listar_habilidades'))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Catálogo vazio')

    def test_lista_mostra_quantos_pokemons_usam_cada_habilidade(self):
        criar_pokemon(nome='pikachu', id_pokemon=25, habilidades=['static'])
        criar_pokemon(nome='raichu', id_pokemon=26, habilidades=['static'])
        Habilidade.objects.create(nome='intimidate')
        resposta = self.client.get(reverse('listar_habilidades'))
        totais = {h.nome: h.total_pokemons for h in resposta.context['habilidades']}
        self.assertEqual(totais, {'static': 2, 'intimidate': 0})

    def test_busca_filtra_por_nome_e_descricao(self):
        Habilidade.objects.create(nome='static', descricao='Paralisa ao contato')
        Habilidade.objects.create(nome='blaze', descricao='Reforça golpes de fogo')
        por_nome = self.client.get(reverse('listar_habilidades'), {'q': 'stat'})
        por_descricao = self.client.get(reverse('listar_habilidades'), {'q': 'fogo'})
        self.assertEqual([h.nome for h in por_nome.context['habilidades']], ['static'])
        self.assertEqual([h.nome for h in por_descricao.context['habilidades']], ['blaze'])

    def test_busca_sem_resultado(self):
        Habilidade.objects.create(nome='static')
        resposta = self.client.get(reverse('listar_habilidades'), {'q': 'zzz'})
        self.assertContains(resposta, 'Nenhum resultado')

    def test_sidebar_tem_link_para_habilidades(self):
        resposta = self.client.get(reverse('home'))
        self.assertContains(resposta, reverse('listar_habilidades'))


class CriarHabilidadeTest(TestCase):
    def test_formulario_carrega(self):
        self.assertEqual(self.client.get(reverse('criar_habilidade')).status_code, 200)

    def test_cria_e_redireciona_para_a_lista(self):
        resposta = self.client.post(reverse('criar_habilidade'), {
            'nome': 'intimidate', 'descricao': 'Reduz o ataque do oponente',
        })
        self.assertRedirects(resposta, reverse('listar_habilidades'))
        self.assertEqual(Habilidade.objects.get().descricao, 'Reduz o ataque do oponente')

    def test_nome_e_obrigatorio(self):
        resposta = self.client.post(reverse('criar_habilidade'), {'nome': '  ', 'descricao': 'x'})
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Informe o nome da habilidade.')
        self.assertEqual(Habilidade.objects.count(), 0)

    def test_nome_duplicado_e_recusado_ignorando_caixa(self):
        Habilidade.objects.create(nome='static')
        resposta = self.client.post(reverse('criar_habilidade'), {'nome': 'STATIC'})
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Já existe uma habilidade com esse nome.')
        self.assertEqual(Habilidade.objects.count(), 1)

    def test_espacos_extras_sao_normalizados(self):
        self.client.post(reverse('criar_habilidade'), {'nome': '  lightning   rod '})
        self.assertEqual(Habilidade.objects.get().nome, 'lightning rod')


class DetalhesHabilidadeTest(TestCase):
    def test_exibe_pokemons_que_possuem_a_habilidade(self):
        criar_pokemon(nome='pikachu', id_pokemon=25, habilidades=[('static', False)])
        criar_pokemon(nome='raichu', id_pokemon=26, habilidades=[('static', True)])
        criar_pokemon(nome='eevee', id_pokemon=133, habilidades=['run-away'])
        static = Habilidade.objects.get(nome='static')

        resposta = self.client.get(reverse('detalhes_habilidade', args=[static.pk]))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'pikachu')
        self.assertContains(resposta, 'raichu')
        self.assertNotContains(resposta, 'eevee')
        self.assertContains(resposta, 'Oculta')

    def test_sem_pokemons_mostra_estado_vazio(self):
        habilidade = Habilidade.objects.create(nome='intimidate')
        resposta = self.client.get(reverse('detalhes_habilidade', args=[habilidade.pk]))
        self.assertContains(resposta, 'Nenhum Pokémon ainda')

    def test_inexistente_retorna_404(self):
        self.assertEqual(self.client.get(reverse('detalhes_habilidade', args=[999])).status_code, 404)


class EditarHabilidadeTest(TestCase):
    def setUp(self):
        self.habilidade = Habilidade.objects.create(nome='static', descricao='antiga')
        self.url = reverse('editar_habilidade', args=[self.habilidade.pk])

    def test_formulario_vem_preenchido(self):
        resposta = self.client.get(self.url)
        self.assertContains(resposta, 'value="static"')
        self.assertContains(resposta, 'antiga')

    def test_atualiza_e_vai_para_o_detalhe(self):
        resposta = self.client.post(self.url, {'nome': 'static', 'descricao': 'nova descrição'})
        self.assertRedirects(resposta, reverse('detalhes_habilidade', args=[self.habilidade.pk]))
        self.habilidade.refresh_from_db()
        self.assertEqual(self.habilidade.descricao, 'nova descrição')

    def test_manter_o_proprio_nome_e_permitido(self):
        resposta = self.client.post(self.url, {'nome': 'Static', 'descricao': ''})
        self.assertEqual(resposta.status_code, 302)

    def test_renomear_para_nome_de_outra_habilidade_e_recusado(self):
        Habilidade.objects.create(nome='blaze')
        resposta = self.client.post(self.url, {'nome': 'blaze', 'descricao': ''})
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Já existe uma habilidade com esse nome.')
        self.habilidade.refresh_from_db()
        self.assertEqual(self.habilidade.nome, 'static')

    def test_vinculos_sobrevivem_ao_renomear(self):
        pokemon = criar_pokemon(habilidades=['static'])
        habilidade = Habilidade.objects.get(nome='static')
        self.client.post(reverse('editar_habilidade', args=[habilidade.pk]),
                         {'nome': 'estática', 'descricao': ''})
        self.assertEqual(list(pokemon.habilidades.values_list('nome', flat=True)), ['estática'])


class RemoverHabilidadeTest(TestCase):
    def test_get_mostra_confirmacao_e_nao_exclui(self):
        criar_pokemon(habilidades=['static'])
        habilidade = Habilidade.objects.get(nome='static')
        resposta = self.client.get(reverse('remover_habilidade', args=[habilidade.pk]))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, '1 Pokémon')
        self.assertTrue(Habilidade.objects.filter(pk=habilidade.pk).exists())

    def test_post_exclui_e_desfaz_vinculos(self):
        pokemon = criar_pokemon(habilidades=['static'])
        habilidade = Habilidade.objects.get(nome='static')
        resposta = self.client.post(reverse('remover_habilidade', args=[habilidade.pk]))
        self.assertRedirects(resposta, reverse('listar_habilidades'))
        self.assertFalse(Habilidade.objects.filter(pk=habilidade.pk).exists())
        self.assertEqual(pokemon.vinculos.count(), 0)
        self.assertTrue(Pokemon.objects.filter(pk=pokemon.pk).exists())

    def test_mensagem_de_sucesso_aparece_na_lista(self):
        habilidade = Habilidade.objects.create(nome='intimidate')
        resposta = self.client.post(reverse('remover_habilidade', args=[habilidade.pk]), follow=True)
        self.assertContains(resposta, 'removida')

    def test_inexistente_retorna_404(self):
        self.assertEqual(self.client.post(reverse('remover_habilidade', args=[999])).status_code, 404)


# ---------------------------------------------------------------------------
# Migração de dados: habilidades em JSON -> tabela intermediária
# ---------------------------------------------------------------------------

class MigracaoHabilidadesJsonTest(TransactionTestCase):
    """Garante que as habilidades já salvas em JSON não se perdem na migração."""

    antes = [('pokemon_api', '0006_captura_pokemonhabilidade')]
    depois = [('pokemon_api', '0008_remove_pokemon_habilidades_json')]

    def setUp(self):
        executor = MigrationExecutor(connection)
        executor.migrate(self.antes)
        apps_antigos = executor.loader.project_state(self.antes).apps
        PokemonAntigo = apps_antigos.get_model('pokemon_api', 'Pokemon')
        PokemonAntigo.objects.create(
            nome='snorlax', id_pokemon=143,
            habilidades_json=['immunity', 'thick-fat', 'Immunity'],
        )
        PokemonAntigo.objects.create(nome='ditto', id_pokemon=132, habilidades_json=['limber', 'immunity'])
        PokemonAntigo.objects.create(nome='mew', id_pokemon=151, habilidades_json=[])

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(executor.loader.graph.leaf_nodes())

    def test_dados_do_json_viram_vinculos_ordenados(self):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(self.depois)
        apps_novos = executor.loader.project_state(self.depois).apps
        Pokemon_ = apps_novos.get_model('pokemon_api', 'Pokemon')
        Vinculo = apps_novos.get_model('pokemon_api', 'PokemonHabilidade')
        Habilidade_ = apps_novos.get_model('pokemon_api', 'Habilidade')

        def nomes(pokemon):
            return list(
                Vinculo.objects.filter(pokemon__nome=pokemon)
                .order_by('ordem').values_list('habilidade__nome', flat=True)
            )

        self.assertEqual(nomes('snorlax'), ['immunity', 'thick-fat'])
        self.assertEqual(nomes('ditto'), ['limber', 'immunity'])
        self.assertEqual(nomes('mew'), [])
        self.assertEqual(Habilidade_.objects.filter(nome__iexact='immunity').count(), 1)
        self.assertEqual(Pokemon_.objects.count(), 3)
