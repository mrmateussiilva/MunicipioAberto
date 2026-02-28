from __future__ import annotations

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("empresas", "0001_initial"),
        ("municipios", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Contrato",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("objeto", models.TextField()),
                ("valor", models.DecimalField(decimal_places=2, max_digits=16)),
                ("data_assinatura", models.DateField()),
                ("data_publicacao", models.DateField()),
                ("fonte_dados", models.URLField(max_length=500)),
                ("numero_processo", models.CharField(max_length=100)),
                (
                    "empresa",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="contratos",
                        to="empresas.empresa",
                    ),
                ),
                (
                    "municipio",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="contratos",
                        to="municipios.municipio",
                    ),
                ),
            ],
            options={
                "verbose_name": "Contrato",
                "verbose_name_plural": "Contratos",
                "ordering": ["-data_assinatura"],
            },
        ),
        migrations.AddIndex(
            model_name="contrato",
            index=models.Index(fields=["municipio", "empresa"], name="contratos_c_muni_id_9f8c33_idx"),
        ),
        migrations.AddIndex(
            model_name="contrato",
            index=models.Index(fields=["data_assinatura"], name="contratos_c_data_as_012b62_idx"),
        ),
        migrations.AddIndex(
            model_name="contrato",
            index=models.Index(fields=["numero_processo"], name="contratos_c_numero__f24f8a_idx"),
        ),
    ]
