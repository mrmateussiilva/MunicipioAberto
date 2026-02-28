from __future__ import annotations

from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Socio(models.Model):
    nome = models.CharField(max_length=255)
    cpf = models.CharField(max_length=14, null=True, blank=True)
    empresa = models.ForeignKey(
        "empresas.Empresa",
        on_delete=models.CASCADE,
        related_name="socios",
    )
    percentual_participacao = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))],
    )

    class Meta:
        ordering = ["nome"]
        verbose_name = "Sócio"
        verbose_name_plural = "Sócios"

    def __str__(self) -> str:
        return self.nome
