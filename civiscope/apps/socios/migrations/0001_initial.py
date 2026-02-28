from __future__ import annotations

from decimal import Decimal

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("empresas", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Socio",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome", models.CharField(max_length=255)),
                ("cpf", models.CharField(blank=True, max_length=14, null=True)),
                (
                    "percentual_participacao",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=5,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0")),
                            django.core.validators.MaxValueValidator(Decimal("100")),
                        ],
                    ),
                ),
                (
                    "empresa",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="socios",
                        to="empresas.empresa",
                    ),
                ),
            ],
            options={
                "verbose_name": "Sócio",
                "verbose_name_plural": "Sócios",
                "ordering": ["nome"],
            },
        ),
    ]
