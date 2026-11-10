from django.db import migrations

REGIOES = [
    ('Kanto', 1, 151), ('Johto', 152, 251), ('Hoenn', 252, 386),
    ('Sinnoh', 387, 493), ('Unova', 494, 649), ('Kalos', 650, 721),
    ('Alola', 722, 809), ('Galar', 810, 905), ('Paldea', 906, 1025),
]


def popular(apps, schema_editor):
    Regiao = apps.get_model('pokemon_api', 'Regiao')
    for nome, inicio, fim in REGIOES:
        Regiao.objects.get_or_create(
            nome=nome, defaults={'numero_inicial': inicio, 'numero_final': fim}
        )


class Migration(migrations.Migration):
    dependencies = [('pokemon_api', '0001_initial')]
    operations = [migrations.RunPython(popular, migrations.RunPython.noop)]
