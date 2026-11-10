from django.conf import settings
from django.db import models


class Regiao(models.Model):
    nome = models.CharField('Nome', max_length=50, unique=True)
    numero_inicial = models.PositiveIntegerField('Primeiro número da Pokédex')
    numero_final = models.PositiveIntegerField('Último número da Pokédex')


class Treinador(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name='Usuário',
        on_delete=models.CASCADE,
        related_name='treinador',
    )
    nome = models.CharField('Nome', max_length=100)
    cidade_natal = models.CharField('Cidade natal', max_length=100, blank=True, default='')
    data_cadastro = models.DateField('Cadastrado em', auto_now_add=True)


class Habilidade(models.Model):
    nome = models.CharField('Nome', max_length=100, unique=True)


class Pokemon(models.Model):
    nome = models.CharField('Nome', max_length=100)
    id_pokemon = models.IntegerField('Número da Pokédex')

    treinador = models.ForeignKey(
        Treinador,
        verbose_name='Treinador',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pokemons',
    )
    regiao = models.ForeignKey(
        Regiao,
        verbose_name='Região',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pokemons',
    )

    tipos = models.JSONField(default=list)

    altura = models.CharField('Altura', max_length=20, blank=True, default='')
    peso = models.CharField('Peso', max_length=20, blank=True, default='')
    habilidades = models.ManyToManyField(
        Habilidade,
        through='PokemonHabilidade',
        verbose_name='Habilidades',
        related_name='pokemons',
        blank=True,
    )

    hp = models.IntegerField('HP', default=0)
    ataque = models.IntegerField('Ataque', default=0)
    defesa = models.IntegerField('Defesa', default=0)
    velocidade = models.IntegerField('Velocidade', default=0)

    sprite_url = models.CharField('Imagem', blank=True, default='')
    observacoes = models.TextField('Observações', blank=True, default='')

    favorito = models.BooleanField('Favorito', default=False)
    capturado = models.BooleanField('Capturado', default=False)

    data_captura = models.DateField('Adicionado em', auto_now_add=True)


class PokemonHabilidade(models.Model):
    """Tabela intermediária (through) do N:N entre Pokémon e Habilidade."""

    pokemon = models.ForeignKey(Pokemon, on_delete=models.CASCADE, related_name='vinculos')
    habilidade = models.ForeignKey(Habilidade, on_delete=models.CASCADE, related_name='vinculos')
    oculta = models.BooleanField('Habilidade oculta', default=False)
