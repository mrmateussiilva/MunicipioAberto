"""Client for the Portal Brasileiro de Dados Abertos (dados.gov.br).

Docs: https://dados.gov.br/swagger-ui.html

Env vars:
    DADOS_ABERTOS_BASE_URL — optional override
"""

from __future__ import annotations

import logging
import os
from typing import Iterator

from pydantic import ValidationError

from .base import BaseAPIClient
from .schemas import DadosAbertosDatasetSchema, DadosAbertosRecursoSchema

logger = logging.getLogger(__name__)

_BASE_URL = os.getenv("DADOS_ABERTOS_BASE_URL", "https://dados.gov.br/api/3")


class DadosAbertosClient(BaseAPIClient):
    """
    Client for the Portal Brasileiro de Dados Abertos (CKAN-based API).

    Usage::

        with DadosAbertosClient() as client:
            for ds in client.buscar_datasets("contratos municipais"):
                print(ds.title, len(ds.resources))
    """

    base_url = _BASE_URL

    # ── Datasets ─────────────────────────────────────────────────────────────

    def buscar_datasets(
        self,
        query: str,
        rows: int = 20,
        paginas: int | None = None,
    ) -> Iterator[DadosAbertosDatasetSchema]:
        """Busca datasets pelo texto e itera sobre os resultados."""
        max_rows = rows
        start = 0
        page = 0

        while True:
            if paginas and page >= paginas:
                break

            data = self._get(
                "/action/package_search",
                params={"q": query, "rows": max_rows, "start": start},
            )
            results = (data.get("result") or {}).get("results") or []
            if not results:
                break

            for item in results:
                try:
                    yield DadosAbertosDatasetSchema.model_validate(item)
                except ValidationError as exc:
                    logger.warning("Dataset inválido ignorado: %s — %s", item.get("id"), exc)

            start += len(results)
            page += 1

            if len(results) < max_rows:
                break  # Last page

    # ── Recursos ─────────────────────────────────────────────────────────────

    def recursos_do_dataset(self, dataset_id: str) -> list[DadosAbertosRecursoSchema]:
        """Retorna a lista de recursos de um dataset específico."""
        data = self._get(
            "/action/package_show",
            params={"id": dataset_id},
        )
        result = data.get("result") or {}
        recursos = []
        for r in result.get("resources") or []:
            try:
                recursos.append(DadosAbertosRecursoSchema.model_validate(r))
            except ValidationError as exc:
                logger.warning("Recurso inválido ignorado: %s", exc)
        return recursos

    # ── Organizações ─────────────────────────────────────────────────────────

    def listar_organizacoes(self) -> list[str]:
        """Retorna lista de slugs de organizações cadastradas."""
        data = self._get("/action/organization_list")
        return data.get("result") or []
