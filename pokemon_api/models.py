from django.db import models


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
    habilidades = models.JSONField(default=list)

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
        for nome in self.habilidades or []:
            Habilidade.objects.get_or_create(nome=nome)
