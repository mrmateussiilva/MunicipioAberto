from __future__ import annotations

from django.db import models


class Municipio(models.Model):
    """Representa um município com identificação pública estável."""

    nome = models.CharField(max_length=255)
    estado = models.CharField(max_length=2)
    codigo_ibge = models.CharField(max_length=7, unique=True)
    populacao = models.PositiveIntegerField()
    data_criacao = models.DateField()

    class Meta:
        ordering = ["estado", "nome"]
        verbose_name = "Município"
        verbose_name_plural = "Municípios"

    def __str__(self) -> str:
        return f"{self.nome}/{self.estado}"
