from __future__ import annotations

from datetime import date

from .models import Municipio


class MunicipioService:
    """Centraliza operações de escrita para evitar lógica espalhada em views ou commands."""

    @staticmethod
    def obter_ou_criar(
        *,
        nome: str,
        estado: str,
        codigo_ibge: str,
        populacao: int = 0,
        data_criacao: date | None = None,
    ) -> Municipio:
        municipio, _ = Municipio.objects.get_or_create(
            codigo_ibge=codigo_ibge,
            defaults={
                "nome": nome,
                "estado": estado,
                "populacao": populacao,
                "data_criacao": data_criacao or date.today(),
            },
        )
        return municipio
