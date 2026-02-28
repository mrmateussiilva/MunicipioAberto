"""Orchestration service that maps API responses to Django models."""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal

from apps.contratos.services import ContratoService
from apps.empresas.services import EmpresaService
from apps.municipios.models import Municipio
from apps.municipios.services import MunicipioService

from .clients.pncp import PNCPClient
from .clients.schemas import PNCPContratoSchema, TransparenciaContratoSchema
from .clients.transparencia import TransparenciaClient

logger = logging.getLogger(__name__)

_FALLBACK_POPULACAO = 1  # Placeholder when population is unknown from API


class IngestaoAPIService:
    """
    Orchestrates the ingestion of data from external public APIs
    into the Django database models (Municipio, Empresa, Contrato).
    """

    # ── Portal da Transparência ───────────────────────────────────────────────

    def ingerir_contratos_transparencia(
        self,
        codigo_ibge: str,
        paginas: int | None = None,
        municipio_nome: str = "",
        estado_uf: str = "BR",
    ) -> int:
        """
        Fetches contracts from the Portal da Transparência for a given
        municipality (by IBGE code) and saves them to the database.

        Returns the number of contracts created or retrieved.
        """
        total = 0
        municipio = self._obter_ou_criar_municipio(codigo_ibge, municipio_nome, estado_uf)

        client = TransparenciaClient()
        try:
            for schema in client.contratos(codigo_ibge=codigo_ibge, paginas=paginas):
                try:
                    self._salvar_contrato_transparencia(schema, municipio)
                    total += 1
                except Exception as exc:  # noqa: BLE001
                    logger.error("Erro ao salvar contrato Transparência %s: %s", schema.numero, exc)
        finally:
            client.close()

        logger.info("Ingestão Transparência concluída: %d contratos para IBGE %s.", total, codigo_ibge)
        return total

    def _salvar_contrato_transparencia(
        self,
        schema: TransparenciaContratoSchema,
        municipio: Municipio,
    ) -> None:
        cnpj = schema.cnpj_fornecedor.replace(".", "").replace("/", "").replace("-", "")
        if not cnpj or not schema.nome_fornecedor:
            logger.debug("Contrato sem CNPJ/fornecedor, pulando: %s", schema.numero)
            return

        empresa = EmpresaService.obter_ou_criar(
            nome=schema.nome_fornecedor[:255],
            cnpj=schema.cnpj_fornecedor[:18],
            data_abertura=date(2000, 1, 1),  # API doesn't provide this field
            municipio=municipio,
        )

        data_assinatura = schema.data_assinatura_date or date(2000, 1, 1)
        data_publicacao = schema.data_publicacao_date or data_assinatura
        numero = schema.numero or str(schema.id or "SEM-NUMERO")

        ContratoService.criar(
            municipio=municipio,
            empresa=empresa,
            objeto=schema.objeto[:500] if schema.objeto else "Sem descrição",
            valor=schema.valor_inicial or Decimal("0"),
            data_assinatura=data_assinatura,
            data_publicacao=data_publicacao,
            fonte_dados=schema.url_documento or "https://portaldatransparencia.gov.br",
            numero_processo=numero[:100],
        )

    # ── PNCP ─────────────────────────────────────────────────────────────────

    def ingerir_contratos_pncp(
        self,
        cnpj_orgao: str,
        municipio_nome: str = "",
        estado_uf: str = "BR",
        codigo_ibge: str = "0000000",
        paginas: int | None = None,
        data_inicio: str = "",
        data_fim: str = "",
    ) -> int:
        """
        Fetches contracts from PNCP for a given organ (by CNPJ)
        and saves them to the database.
        """
        total = 0
        municipio = self._obter_ou_criar_municipio(codigo_ibge, municipio_nome, estado_uf)

        client = PNCPClient()
        try:
            for schema in client.contratos_por_orgao(
                cnpj_orgao,
                paginas=paginas,
                data_inicio=data_inicio,
                data_fim=data_fim,
            ):
                try:
                    self._salvar_contrato_pncp(schema, municipio)
                    total += 1
                except Exception as exc:  # noqa: BLE001
                    logger.error("Erro ao salvar contrato PNCP %s: %s", schema.numero_contrato, exc)
        finally:
            client.close()

        logger.info("Ingestão PNCP concluída: %d contratos para CNPJ %s.", total, cnpj_orgao)
        return total

    def _salvar_contrato_pncp(
        self,
        schema: PNCPContratoSchema,
        municipio: Municipio,
    ) -> None:
        ni = schema.ni_fornecedor
        if not ni or not schema.nome_razao_social_fornecedor:
            logger.debug("Contrato PNCP sem NI/fornecedor, pulando: %s", schema.numero_contrato)
            return

        # NI can be CNPJ (14 digits) or CPF (11 digits); pad CNPJ format
        cnpj = ni[:18]

        empresa = EmpresaService.obter_ou_criar(
            nome=schema.nome_razao_social_fornecedor[:255],
            cnpj=cnpj,
            data_abertura=date(2000, 1, 1),
            municipio=municipio,
        )

        data_assinatura = schema.data_assinatura_date or date(2000, 1, 1)
        data_publicacao = schema.data_publicacao_date or data_assinatura
        numero = schema.numero_controle_pncp or schema.numero_contrato or "SEM-NUMERO"

        ContratoService.criar(
            municipio=municipio,
            empresa=empresa,
            objeto=schema.objeto[:500] if schema.objeto else "Sem descrição",
            valor=schema.valor_global or Decimal("0"),
            data_assinatura=data_assinatura,
            data_publicacao=data_publicacao,
            fonte_dados="https://pncp.gov.br",
            numero_processo=numero[:100],
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _obter_ou_criar_municipio(
        self,
        codigo_ibge: str,
        nome: str,
        estado: str,
    ) -> Municipio:
        return MunicipioService.obter_ou_criar(
            nome=nome or f"Município IBGE {codigo_ibge}",
            estado=estado[:2] if estado else "BR",
            codigo_ibge=codigo_ibge,
            populacao=_FALLBACK_POPULACAO,
        )
