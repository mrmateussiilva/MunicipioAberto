from __future__ import annotations

from django.db import models


class Indicador(models.Model):
    contrato = models.ForeignKey(
        "contratos.Contrato",
        on_delete=models.CASCADE,
        related_name="indicadores",
    )
    tipo = models.CharField(max_length=100)
    score = models.DecimalField(max_digits=8, decimal_places=2)
    descricao = models.TextField()
    data_calculo = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ["-data_calculo", "-id"]
        verbose_name = "Indicador"
        verbose_name_plural = "Indicadores"
        indexes = [
            models.Index(fields=["tipo"]),
            models.Index(fields=["data_calculo"]),
        ]

    def __str__(self) -> str:
        return f"{self.tipo} ({self.score})"
