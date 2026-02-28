"""Client for PNCP — Portal Nacional de Contratações Públicas.

Docs: https://pncp.gov.br/api/pncp/swagger-ui/index.html

Env vars:
    PNCP_BASE_URL  — optional override (default: https://pncp.gov.br/api/pncp/v1)
"""

from __future__ import annotations

import logging
import os
from typing import Iterator

from pydantic import ValidationError

from .base import BaseAPIClient
from .schemas import PNCPContratoSchema, PNCPItemSchema

logger = logging.getLogger(__name__)

_BASE_URL = os.getenv("PNCP_BASE_URL", "https://pncp.gov.br/api/consulta/v1")


class PNCPClient(BaseAPIClient):
    """
    Client for PNCP following the Open Contracting Data Standard (OCDS) style.

    Usage::

        with PNCPClient() as client:
            for contrato in client.contratos_por_orgao("00394460000141", paginas=2):
                print(contrato.numero_contrato, contrato.valor_global)
    """

    base_url = _BASE_URL

    # ── Contratos ────────────────────────────────────────────────────────────

    def contratos_por_orgao(
        self,
        cnpj_orgao: str,
        data_inicio: str = "",
        data_fim: str = "",
        ano: int | None = None,
        paginas: int | None = None,
        tamanho_pagina: int = 50,
    ) -> Iterator[PNCPContratoSchema]:
        """
        Itera sobre contratos de um órgão pelo CNPJ.

        Args:
            cnpj_orgao: CNPJ do órgão (apenas dígitos).
            data_inicio: Data inicial no formato YYYYMMDD (ex: '20240101').
            data_fim: Data final no formato YYYYMMDD (ex: '20241231').
        """
        import datetime
        extra: dict = {"cnpjOrgao": cnpj_orgao}
        if data_inicio:
            extra["dataInicial"] = data_inicio
        else:
            # Default: ano corrente
            year = ano or datetime.date.today().year
            extra["dataInicial"] = f"{year}0101"
        if data_fim:
            extra["dataFinal"] = data_fim
        else:
            year = ano or datetime.date.today().year
            extra["dataFinal"] = f"{year}1231"

        for item in self.paginate(
            "/contratos",
            page_param="pagina",
            size_param="tamanhoPagina",
            page_size=tamanho_pagina,
            data_key="data",
            max_pages=paginas,
            extra_params=extra,
        ):
            try:
                yield PNCPContratoSchema.model_validate(item)
            except ValidationError as exc:
                logger.warning(
                    "Contrato PNCP inválido ignorado: %s — %s",
                    item.get("numeroControlePNCP", "?"),
                    exc,
                )

    def itens_contrato(
        self,
        cnpj_orgao: str,
        ano: int,
        numero_sequencial: int,
    ) -> Iterator[PNCPItemSchema]:
        """Itera sobre itens de um contrato específico no PNCP."""
        # Endpoint: /orgaos/{cnpjOrgao}/compras/{ano}/{sequencial}/itens
        path = f"/orgaos/{cnpj_orgao}/compras/{ano}/{numero_sequencial}/itens"
        for item in self.paginate(path, data_key="data", page_size=50):
            try:
                yield PNCPItemSchema.model_validate(item)
            except ValidationError as exc:
                logger.warning("Item PNCP inválido ignorado: %s", exc)

    def contratos_recentes(
        self,
        data_inicio: str,
        data_fim: str,
        cnpj_orgao: str | None = None,
        paginas: int | None = None,
        tamanho_pagina: int = 50,
    ) -> Iterator[PNCPContratoSchema]:
        """
        Busca contratos em um intervalo de datas (formato YYYYMMDD).

        Example::
            client.contratos_recentes("20240101", "20240131", paginas=5)
        """
        extra: dict = {"dataInicial": data_inicio, "dataFinal": data_fim}
        if cnpj_orgao:
            extra["cnpjOrgao"] = cnpj_orgao

        for item in self.paginate(
            "/contratos",
            page_param="pagina",
            size_param="tamanhoPagina",
            page_size=tamanho_pagina,
            data_key="data",
            max_pages=paginas,
            extra_params=extra,
        ):
            try:
                yield PNCPContratoSchema.model_validate(item)
            except ValidationError as exc:
                logger.warning("Contrato PNCP inválido ignorado: %s", exc)

    # ── Contratações por Município ───────────────────────────────────────────

    def contratacoes_por_municipio(
        self,
        codigo_ibge: str,
        uf: str,
        data_inicio: str = "",
        data_fim: str = "",
        paginas: int | None = 5,
        tamanho_pagina: int = 50,
    ) -> list[dict]:
        """Busca contratações (licitações) publicadas para um município pelo IBGE.

        Usa o endpoint ``/contratacoes/publicacao`` que aceita
        ``codigoMunicipioIbge`` e ``uf`` como filtros nativos.
        Itera sobre as modalidades mais comuns para capturar tudo.

        Retorna lista de dicts com ``cnpj`` (do órgão) e ``objetoCompra``.
        """
        import datetime

        ano_atual = datetime.date.today().year
        data_inicio = data_inicio or f"{ano_atual}0101"
        data_fim = data_fim or f"{ano_atual}1231"

        # Modalidades de contratação mais comuns (IDs do PNCP):
        # 1=Leilão, 2=Diálogo, 3=Concurso, 4=Concorrência,
        # 5=Pregão, 6=Dispensa, 7=Inexigibilidade, 8=Pré-qualificação
        modalidades = [4, 5, 6, 7, 8]

        cnpjs_vistos: set[str] = set()
        resultados: list[dict] = []

        for modalidade in modalidades:
            extra: dict = {
                "dataInicial": data_inicio,
                "dataFinal": data_fim,
                "codigoModalidadeContratacao": modalidade,
                "codigoMunicipioIbge": codigo_ibge,
                "uf": uf.upper(),
            }

            try:
                for item in self.paginate(
                    "/contratacoes/publicacao",
                    page_param="pagina",
                    size_param="tamanhoPagina",
                    page_size=tamanho_pagina,
                    data_key="data",
                    max_pages=paginas,
                    extra_params=extra,
                ):
                    orgao = item.get("orgaoEntidade") or {}
                    cnpj = orgao.get("cnpj", "")
                    if cnpj and cnpj not in cnpjs_vistos:
                        cnpjs_vistos.add(cnpj)
                        resultados.append({
                            "cnpj": cnpj,
                            "razaoSocial": orgao.get("razaoSocial", ""),
                        })
            except Exception as exc:  # noqa: BLE001
                logger.debug(
                    "Modalidade %d sem resultados para IBGE %s: %s",
                    modalidade,
                    codigo_ibge,
                    exc,
                )

        logger.info(
            "%d órgão(s) encontrado(s) no PNCP para IBGE %s/%s.",
            len(resultados),
            codigo_ibge,
            uf,
        )
        return resultados
