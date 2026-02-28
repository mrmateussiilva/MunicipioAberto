from __future__ import annotations

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("contratos", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Indicador",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tipo", models.CharField(max_length=100)),
                ("score", models.DecimalField(decimal_places=2, max_digits=8)),
                ("descricao", models.TextField()),
                ("data_calculo", models.DateField(auto_now_add=True)),
                (
                    "contrato",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="indicadores",
                        to="contratos.contrato",
                    ),
                ),
            ],
            options={
                "verbose_name": "Indicador",
                "verbose_name_plural": "Indicadores",
                "ordering": ["-data_calculo", "-id"],
            },
        ),
        migrations.AddIndex(
            model_name="indicador",
            index=models.Index(fields=["tipo"], name="analise_ind_tipo_267c92_idx"),
        ),
        migrations.AddIndex(
            model_name="indicador",
            index=models.Index(fields=["data_calculo"], name="analise_ind_data_ca_7dba3d_idx"),
        ),
    ]
