from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction


class Regiao(models.Model):
    nome = models.CharField('Nome', max_length=50, unique=True)
    numero_inicial = models.PositiveIntegerField('Primeiro número da Pokédex')
    numero_final = models.PositiveIntegerField('Último número da Pokédex')

    class Meta:
        ordering = ['numero_inicial']
        verbose_name = 'Região'
        verbose_name_plural = 'Regiões'

    def __str__(self):
        return self.nome

    @classmethod
    def por_numero(cls, numero):
        return cls.objects.filter(
            numero_inicial__lte=numero, numero_final__gte=numero
        ).first()


class Treinador(models.Model):
    nome = models.CharField('Nome', max_length=100)
    cidade_natal = models.CharField('Cidade natal', max_length=100, blank=True, default='')
    data_cadastro = models.DateField('Cadastrado em', auto_now_add=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Treinador'
        verbose_name_plural = 'Treinadores'

    def __str__(self):
        return self.nome


class Habilidade(models.Model):
    nome = models.CharField('Nome', max_length=100, unique=True)
    descricao = models.TextField('Descrição', blank=True, default='')

    class Meta:
        ordering = ['nome']
        verbose_name = 'Habilidade'
        verbose_name_plural = 'Habilidades'

    def __str__(self):
        return self.nome

    @classmethod
    def obter_ou_criar(cls, nome):
        """Devolve a habilidade com esse nome (ignorando maiúsculas) ou a cria."""
        nome = ' '.join(str(nome).split())
        existente = cls.objects.filter(nome__iexact=nome).first()
        return existente or cls.objects.create(nome=nome)


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

    def __str__(self):
        return f'#{int(self.id_pokemon):03d} {self.nome}'

    @property
    def total_atributos(self):
        return self.hp + self.ataque + self.defesa + self.velocidade

    def save(self, *args, **kwargs):
        if self.regiao_id is None and self.id_pokemon:
            self.regiao = Regiao.por_numero(int(self.id_pokemon))
        super().save(*args, **kwargs)

    @transaction.atomic
    def definir_habilidades(self, itens):
        """Substitui as habilidades do Pokémon.

        `itens` é uma lista de pares (nome, oculta). A posição na lista vira o
        campo `ordem`; nomes repetidos (ignorando maiúsculas) são descartados e
        habilidades novas entram automaticamente no catálogo.
        """
        vinculos = []
        vistos = set()
        for nome, oculta in itens:
            nome = ' '.join(str(nome).split())
            if not nome or nome.lower() in vistos:
                continue
            vistos.add(nome.lower())
            vinculos.append(PokemonHabilidade(
                pokemon=self,
                habilidade=Habilidade.obter_ou_criar(nome),
                oculta=bool(oculta),
                ordem=len(vinculos) + 1,
            ))
        self.vinculos.all().delete()
        PokemonHabilidade.objects.bulk_create(vinculos)


class PokemonHabilidade(models.Model):
    """Tabela intermediária (through) do N:N entre Pokémon e Habilidade."""

    pokemon = models.ForeignKey(
        Pokemon,
        verbose_name='Pokémon',
        on_delete=models.CASCADE,
        related_name='vinculos',
    )
    habilidade = models.ForeignKey(
        Habilidade,
        verbose_name='Habilidade',
        on_delete=models.CASCADE,
        related_name='vinculos',
    )
    oculta = models.BooleanField('Habilidade oculta', default=False)
    ordem = models.PositiveSmallIntegerField('Ordem (slot)', default=1)

    class Meta:
        ordering = ['ordem', 'id']
        verbose_name = 'Habilidade do Pokémon'
        verbose_name_plural = 'Habilidades dos Pokémon'
        constraints = [
            models.UniqueConstraint(
                fields=['pokemon', 'habilidade'],
                name='unique_pokemon_habilidade',
            ),
        ]

    def __str__(self):
        return f'{self.pokemon.nome} → {self.habilidade.nome}'


class Captura(models.Model):
    """Ficha de captura: relação 1:1 com Pokémon (um Pokémon, uma ficha)."""

    class Pokebola(models.TextChoices):
        POKEBOLA = 'pokeball', 'Poké Ball'
        GREAT = 'great', 'Great Ball'
        ULTRA = 'ultra', 'Ultra Ball'
        MASTER = 'master', 'Master Ball'
        PREMIER = 'premier', 'Premier Ball'
        OUTRA = 'outra', 'Outra'

    pokemon = models.OneToOneField(
        Pokemon,
        verbose_name='Pokémon',
        on_delete=models.CASCADE,
        related_name='captura',
    )
    apelido = models.CharField('Apelido', max_length=50, blank=True, default='')
    nivel = models.PositiveSmallIntegerField(
        'Nível',
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    pokebola = models.CharField(
        'Pokébola usada',
        max_length=20,
        choices=Pokebola.choices,
        blank=True,
        default='',
    )
    local = models.CharField('Local da captura', max_length=100, blank=True, default='')
    data_encontro = models.DateField('Data do encontro', null=True, blank=True)

    class Meta:
        verbose_name = 'Ficha de captura'
        verbose_name_plural = 'Fichas de captura'

    def __str__(self):
        return f'Ficha de {self.pokemon.nome}'
