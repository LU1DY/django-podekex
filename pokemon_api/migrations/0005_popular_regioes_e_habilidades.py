from django.db import migrations

REGIOES = [
    ('Kanto', 1, 151),
    ('Johto', 152, 251),
    ('Hoenn', 252, 386),
    ('Sinnoh', 387, 493),
    ('Unova', 494, 649),
    ('Kalos', 650, 721),
    ('Alola', 722, 809),
    ('Galar', 810, 905),
    ('Paldea', 906, 1025),
]


def popular(apps, schema_editor):
    Regiao = apps.get_model('pokemon_api', 'Regiao')
    Habilidade = apps.get_model('pokemon_api', 'Habilidade')
    Pokemon = apps.get_model('pokemon_api', 'Pokemon')

    for nome, inicio, fim in REGIOES:
        Regiao.objects.get_or_create(
            nome=nome,
            defaults={'numero_inicial': inicio, 'numero_final': fim},
        )

    for pokemon in Pokemon.objects.all():
        regiao = Regiao.objects.filter(
            numero_inicial__lte=pokemon.id_pokemon,
            numero_final__gte=pokemon.id_pokemon,
        ).first()
        if regiao:
            pokemon.regiao = regiao
            pokemon.save(update_fields=['regiao'])
        for nome in pokemon.habilidades or []:
            Habilidade.objects.get_or_create(nome=nome)


def desfazer(apps, schema_editor):
    apps.get_model('pokemon_api', 'Regiao').objects.all().delete()
    apps.get_model('pokemon_api', 'Habilidade').objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('pokemon_api', '0004_regiao_treinador_habilidade'),
    ]

    operations = [
        migrations.RunPython(popular, desfazer),
    ]
