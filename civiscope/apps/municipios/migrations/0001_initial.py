from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies: list[tuple[str, str]] = []

    operations = [
        migrations.CreateModel(
            name="Municipio",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome", models.CharField(max_length=255)),
                ("estado", models.CharField(max_length=2)),
                ("codigo_ibge", models.CharField(max_length=7, unique=True)),
                ("populacao", models.PositiveIntegerField()),
                ("data_criacao", models.DateField()),
            ],
            options={
                "verbose_name": "Município",
                "verbose_name_plural": "Municípios",
                "ordering": ["estado", "nome"],
            },
        ),
    ]
