import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pokemon_api', '0003_alter_pokemon_habilidades_alter_pokemon_tipos'),
    ]

    operations = [
        migrations.CreateModel(
            name='Habilidade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100, unique=True, verbose_name='Nome')),
                ('descricao', models.TextField(blank=True, default='', verbose_name='Descrição')),
            ],
        ),
        migrations.CreateModel(
            name='Regiao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=50, unique=True, verbose_name='Nome')),
            ],
            options={
                'verbose_name': 'Região',
                'verbose_name_plural': 'Regiões',
            },
        ),
        migrations.CreateModel(
            name='Treinador',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100, verbose_name='Nome')),
                ('cidade_natal', models.CharField(blank=True, default='', max_length=100, verbose_name='Cidade natal')),
                ('regiao', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='treinadores', to='pokemon_api.regiao', verbose_name='Região')),
            ],
            options={
                'verbose_name': 'Treinador',
                'verbose_name_plural': 'Treinadores',
            },
        ),
        migrations.AddField(
            model_name='pokemon',
            name='treinador',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pokemons', to='pokemon_api.treinador', verbose_name='Treinador'),
        ),
    ]
