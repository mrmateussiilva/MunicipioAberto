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


class Vereador(models.Model):
    """Representa um vereador eleito em um município."""

    municipio = models.ForeignKey(
        Municipio, on_delete=models.CASCADE, related_name="vereadores"
    )
    nome_urna = models.CharField(max_length=255)
    nome_completo = models.CharField(max_length=255)
    partido_sigla = models.CharField(max_length=20)
    partido_numero = models.IntegerField(null=True, blank=True)
    coligacao = models.CharField(max_length=255, null=True, blank=True)
    foto_url = models.URLField(max_length=500, null=True, blank=True)
    status_eleicao = models.CharField(max_length=100)  # Ex: Eleito por QP
    is_reeleito = models.BooleanField(default=False)
    
    # Performance Legislativa (Métricas)
    projetos_aprovados = models.IntegerField(default=0)
    total_projetos = models.IntegerField(default=0)
    ano_eleicao = models.IntegerField(default=2024)

    class Meta:
        verbose_name = "Vereador"
        verbose_name_plural = "Vereadores"
        ordering = ["nome_urna"]
        unique_together = ('municipio', 'nome_completo', 'ano_eleicao')

    def __str__(self) -> str:
        return f"{self.nome_urna} ({self.partido_sigla})"


class ProjetoLei(models.Model):
    municipio = models.ForeignKey(Municipio, on_delete=models.CASCADE, related_name="projetos_lei")
    titulo = models.CharField(max_length=255)
    descricao = models.TextField(null=True, blank=True)
    autor = models.ForeignKey(Vereador, on_delete=models.CASCADE, related_name="projetos_autorados")
    data_apresentacao = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=100, default="Em tramitação")
    
    # Geolocalização
    logradouro = models.CharField(max_length=255, null=True, blank=True)
    bairro = models.CharField(max_length=100, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return self.titulo


class VotoProjeto(models.Model):
    TIPOS_VOTO = [
        ('SIM', 'Sim'),
        ('NAO', 'Não'),
        ('ABSTENCAO', 'Abstenção'),
    ]
    projeto = models.ForeignKey(ProjetoLei, on_delete=models.CASCADE, related_name="votos")
    vereador = models.ForeignKey(Vereador, on_delete=models.CASCADE, related_name="histórico_votos")
    tipo_voto = models.CharField(max_length=20, choices=TIPOS_VOTO)

    class Meta:
        unique_together = ('projeto', 'vereador')
