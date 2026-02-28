from __future__ import annotations

from django.db import models


class Contrato(models.Model):
    municipio = models.ForeignKey(
        "municipios.Municipio",
        on_delete=models.CASCADE,
        related_name="contratos",
    )
    empresa = models.ForeignKey(
        "empresas.Empresa",
        on_delete=models.CASCADE,
        related_name="contratos",
    )
    objeto = models.TextField()
    valor = models.DecimalField(max_digits=16, decimal_places=2)
    data_assinatura = models.DateField()
    data_publicacao = models.DateField()
    fonte_dados = models.URLField(max_length=500)
    numero_processo = models.CharField(max_length=100)
    
    # Geolocalização
    logradouro = models.CharField(max_length=255, null=True, blank=True)
    bairro = models.CharField(max_length=100, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        ordering = ["-data_assinatura"]
        verbose_name = "Contrato"
        verbose_name_plural = "Contratos"
        indexes = [
            models.Index(fields=["municipio", "empresa"]),
            models.Index(fields=["data_assinatura"]),
            models.Index(fields=["numero_processo"]),
        ]

    def __str__(self) -> str:
        return f"{self.numero_processo} - {self.empresa.nome}"
