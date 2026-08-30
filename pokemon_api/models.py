from django.db import models

# Create your models here.

class Pokemon(models.Model):
    nome = models.CharField('Nome', max_length=100)
    id_pokemon = models.IntegerField('Número da Pokédex')
    
    tipos = models.CharField('Tipo primário', max_length=50)

    altura = models.CharField('Altura', max_length=20, blank=True, default='')
    peso = models.CharField('Peso', max_length=20, blank=True, default='')
    habilidades = models.CharField('Habilidade', max_length=150, blank=True, default='')
    
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
        return f'#{self.number:03d} {self.name}'
