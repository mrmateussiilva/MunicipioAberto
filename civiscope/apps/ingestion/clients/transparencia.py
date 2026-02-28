"""Client for the Portal da Transparência API.

Docs: https://portaldatransparencia.gov.br/api-de-dados
Token: https://portaldatransparencia.gov.br/api-de-dados/cadastrar-email

Required env var:
    TRANSPARENCIA_API_KEY — token obtido no portal acima.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Iterator

from pydantic import ValidationError

from .base import APIError, BaseAPIClient
from .schemas import (
    TransparenciaContratoSchema,
    TransparenciaLicitacaoSchema,
    TransparenciaOrgaoSchema,
)

logger = logging.getLogger(__name__)

_BASE_URL = os.getenv(
    "TRANSPARENCIA_BASE_URL",
    "https://api.portaldatransparencia.gov.br/api-de-dados",
)


class TransparenciaClient(BaseAPIClient):
    """
    Client for the Portal da Transparência REST API.

    Usage::

        with TransparenciaClient() as client:
            for contrato in client.contratos(codigo_ibge="3550308", paginas=2):
                print(contrato.numero, contrato.valor_inicial)
    """

    base_url = _BASE_URL

    def __init__(self, api_key: str | None = None) -> None:
        resolved_key = api_key or os.getenv("TRANSPARENCIA_API_KEY", "")
        self.default_headers = {"chave-api-dados": resolved_key}
        super().__init__()
        if not resolved_key:
            logger.warning(
                "TRANSPARENCIA_API_KEY não configurada. "
                "Obtenha em: https://portaldatransparencia.gov.br/api-de-dados/cadastrar-email"
            )

    # ── Contratos ────────────────────────────────────────────────────────────

    def contratos(
        self,
        codigo_orgao: str | None = None,
        cnpj_fornecedor: str | None = None,
        paginas: int | None = None,
        tamanho_pagina: int = 100,
    ) -> Iterator[TransparenciaContratoSchema]:
        """Itera sobre contratos do Portal da Transparência."""
        extra: dict[str, Any] = {}
        if codigo_orgao:
            extra["codigoOrgao"] = codigo_orgao
        if cnpj_fornecedor:
            extra["cnpjFornecedor"] = cnpj_fornecedor

        for item in self.paginate(
            "/contratos",
            page_param="pagina",
            size_param="tamanhoPagina",
            page_size=tamanho_pagina,
            data_key=None,
            max_pages=paginas,
            extra_params=extra,
        ):
            try:
                yield TransparenciaContratoSchema.model_validate(item)
            except ValidationError as exc:
                logger.warning("Contrato inválido ignorado: %s — %s", item.get("id"), exc)

    # ── Licitações ───────────────────────────────────────────────────────────

    def licitacoes(
        self,
        codigo_ibge: str | None = None,
        paginas: int | None = None,
        tamanho_pagina: int = 100,
    ) -> Iterator[TransparenciaLicitacaoSchema]:
        """Itera sobre licitações do Portal da Transparência."""
        extra: dict[str, Any] = {}
        if codigo_ibge:
            extra["codigoIbge"] = codigo_ibge

        for item in self.paginate(
            "/licitacoes",
            page_param="pagina",
            size_param="tamanhoPagina",
            page_size=tamanho_pagina,
            max_pages=paginas,
            extra_params=extra,
        ):
            try:
                yield TransparenciaLicitacaoSchema.model_validate(item)
            except ValidationError as exc:
                logger.warning("Licitação inválida ignorada: %s", exc)

    # ── Despesas ─────────────────────────────────────────────────────────────

    def despesas(
        self,
        codigo_ibge: str | None = None,
        ano: int | None = None,
        paginas: int | None = None,
        tamanho_pagina: int = 100,
    ) -> Iterator[dict]:
        """Itera sobre despesas do Portal da Transparência (retorna dict bruto)."""
        extra: dict[str, Any] = {}
        if codigo_ibge:
            extra["codigoIbge"] = codigo_ibge
        if ano:
            extra["ano"] = ano

        yield from self.paginate(
            "/despesas/por-municipio",
            page_param="pagina",
            size_param="tamanhoPagina",
            page_size=tamanho_pagina,
            max_pages=paginas,
            extra_params=extra,
        )

    # ── Órgãos ──────────────────────────────────────────────────────────────

    def orgaos_por_municipio(
        self,
        codigo_ibge: str,
        paginas: int | None = 2,
    ) -> list[TransparenciaOrgaoSchema]:
        """Busca órgãos SIAFI sediados em um município (pelo código IBGE).

        Retorna lista de órgãos cujos contratos podem ser consultados
        via ``contratos(codigo_orgao=...)``.
        """
        orgaos: list[TransparenciaOrgaoSchema] = []

        for item in self.paginate(
            "/orgaos-siafi",
            page_param="pagina",
            size_param="tamanhoPagina",
            page_size=100,
            max_pages=paginas,
            extra_params={"codigoIbge": codigo_ibge},
        ):
            try:
                orgaos.append(TransparenciaOrgaoSchema.model_validate(item))
            except ValidationError as exc:
                logger.warning("Órgão inválido ignorado: %s", exc)

        return orgaos
