"""Client for IBGE Localidades API.

Docs:
    https://servicodados.ibge.gov.br/api/docs/localidades
"""

from __future__ import annotations

import os
import unicodedata

from .base import BaseAPIClient

_BASE_URL = os.getenv(
    "IBGE_LOCALIDADES_BASE_URL",
    "https://servicodados.ibge.gov.br/api/v1/localidades",
)


def _normalizar_nome_municipio(valor: str) -> str:
    texto = unicodedata.normalize("NFKD", valor or "")
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return " ".join(texto.lower().strip().split())


class IBGEClient(BaseAPIClient):
    """Minimal client for municipality lookup by city name and UF."""

    base_url = _BASE_URL

    def municipios_por_uf(self, uf: str) -> list[dict]:
        """Return all municipalities for a given federative unit."""
        data = self._get(f"/estados/{uf.upper()}/municipios")
        return data if isinstance(data, list) else []

    def buscar_municipio_por_nome(self, nome: str, uf: str) -> dict | None:
        """Return the municipality payload matching a city name inside a UF."""
        nome_normalizado = _normalizar_nome_municipio(nome)

        for item in self.municipios_por_uf(uf):
            if _normalizar_nome_municipio(item.get("nome", "")) == nome_normalizado:
                return item
        return None

