from __future__ import annotations

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("municipios", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Empresa",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome", models.CharField(max_length=255)),
                ("cnpj", models.CharField(max_length=18, unique=True)),
                ("data_abertura", models.DateField()),
                (
                    "municipio",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="empresas",
                        to="municipios.municipio",
                    ),
                ),
            ],
            options={
                "verbose_name": "Empresa",
                "verbose_name_plural": "Empresas",
                "ordering": ["nome"],
            },
        ),
    ]
