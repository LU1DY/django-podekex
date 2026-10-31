from django.db import migrations


def json_para_through(apps, schema_editor):
    """Copia a lista de nomes (JSON) para a tabela intermediária."""
    Pokemon = apps.get_model('pokemon_api', 'Pokemon')
    Habilidade = apps.get_model('pokemon_api', 'Habilidade')
    PokemonHabilidade = apps.get_model('pokemon_api', 'PokemonHabilidade')

    for pokemon in Pokemon.objects.all():
        vistos = set()
        for nome in pokemon.habilidades_json or []:
            nome = ' '.join(str(nome).split())
            if not nome or nome.lower() in vistos:
                continue
            vistos.add(nome.lower())
            habilidade = Habilidade.objects.filter(nome__iexact=nome).first()
            if habilidade is None:
                habilidade = Habilidade.objects.create(nome=nome)
            PokemonHabilidade.objects.create(
                pokemon=pokemon,
                habilidade=habilidade,
                ordem=len(vistos),
            )


def through_para_json(apps, schema_editor):
    """Reverso: devolve os nomes (em ordem) para o campo JSON."""
    Pokemon = apps.get_model('pokemon_api', 'Pokemon')
    PokemonHabilidade = apps.get_model('pokemon_api', 'PokemonHabilidade')

    for pokemon in Pokemon.objects.all():
        nomes = list(
            PokemonHabilidade.objects.filter(pokemon=pokemon)
            .order_by('ordem', 'id')
            .values_list('habilidade__nome', flat=True)
        )
        pokemon.habilidades_json = nomes
        pokemon.save(update_fields=['habilidades_json'])


class Migration(migrations.Migration):
    """Etapa 2/3: migra os dados do JSON para o N:N."""

    dependencies = [
        ('pokemon_api', '0006_captura_pokemonhabilidade'),
    ]

    operations = [
        migrations.RunPython(json_para_through, through_para_json),
    ]
