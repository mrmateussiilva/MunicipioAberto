from __future__ import annotations

from django.db import models


class Empresa(models.Model):
    nome = models.CharField(max_length=255)
    cnpj = models.CharField(max_length=18, unique=True)
    data_abertura = models.DateField()
    municipio = models.ForeignKey(
        "municipios.Municipio",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="empresas",
    )

    class Meta:
        ordering = ["nome"]
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"

    def __str__(self) -> str:
        return f"{self.nome} ({self.cnpj})"
