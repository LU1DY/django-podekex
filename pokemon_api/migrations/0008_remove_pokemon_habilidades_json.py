from django.db import migrations


class Migration(migrations.Migration):
    """Etapa 3/3: remove a coluna JSON antiga, já copiada para o N:N."""

    dependencies = [
        ('pokemon_api', '0007_migrar_habilidades_json'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pokemon',
            name='habilidades_json',
        ),
    ]
