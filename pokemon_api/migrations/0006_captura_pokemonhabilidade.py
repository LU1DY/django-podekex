import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """Etapa 1/3: cria a ficha de captura (1:1) e a tabela intermediária (N:N).

    O JSON antigo de habilidades é apenas renomeado para `habilidades_json`;
    os dados são copiados na 0007 e a coluna removida na 0008.
    """

    dependencies = [
        ('pokemon_api', '0005_popular_regioes_e_habilidades'),
    ]

    operations = [
        migrations.RenameField(
            model_name='pokemon',
            old_name='habilidades',
            new_name='habilidades_json',
        ),
        migrations.CreateModel(
            name='PokemonHabilidade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('oculta', models.BooleanField(default=False, verbose_name='Habilidade oculta')),
                ('ordem', models.PositiveSmallIntegerField(default=1, verbose_name='Ordem (slot)')),
                ('habilidade', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vinculos', to='pokemon_api.habilidade', verbose_name='Habilidade')),
                ('pokemon', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vinculos', to='pokemon_api.pokemon', verbose_name='Pokémon')),
            ],
            options={
                'verbose_name': 'Habilidade do Pokémon',
                'verbose_name_plural': 'Habilidades dos Pokémon',
                'ordering': ['ordem', 'id'],
            },
        ),
        migrations.AddConstraint(
            model_name='pokemonhabilidade',
            constraint=models.UniqueConstraint(fields=('pokemon', 'habilidade'), name='unique_pokemon_habilidade'),
        ),
        migrations.AddField(
            model_name='pokemon',
            name='habilidades',
            field=models.ManyToManyField(blank=True, related_name='pokemons', through='pokemon_api.PokemonHabilidade', to='pokemon_api.habilidade', verbose_name='Habilidades'),
        ),
        migrations.CreateModel(
            name='Captura',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('apelido', models.CharField(blank=True, default='', max_length=50, verbose_name='Apelido')),
                ('nivel', models.PositiveSmallIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100)], verbose_name='Nível')),
                ('pokebola', models.CharField(blank=True, choices=[('pokeball', 'Poké Ball'), ('great', 'Great Ball'), ('ultra', 'Ultra Ball'), ('master', 'Master Ball'), ('premier', 'Premier Ball'), ('outra', 'Outra')], default='', max_length=20, verbose_name='Pokébola usada')),
                ('local', models.CharField(blank=True, default='', max_length=100, verbose_name='Local da captura')),
                ('data_encontro', models.DateField(blank=True, null=True, verbose_name='Data do encontro')),
                ('pokemon', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='captura', to='pokemon_api.pokemon', verbose_name='Pokémon')),
            ],
            options={
                'verbose_name': 'Ficha de captura',
                'verbose_name_plural': 'Fichas de captura',
            },
        ),
    ]
