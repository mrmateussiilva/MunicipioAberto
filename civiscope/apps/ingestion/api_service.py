"""Orchestration service that maps API responses to Django models."""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal

from apps.contratos.services import ContratoService
from apps.empresas.services import EmpresaService
from apps.municipios.models import Municipio
from apps.municipios.services import MunicipioService

from .clients.ibge import IBGEClient
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
        codigo_orgao: str = "",
        codigo_ibge: str = "",
        paginas: int | None = None,
        municipio_nome: str = "",
        estado_uf: str = "BR",
    ) -> int:
        """
        Fetches contracts from the Portal da Transparência for a given
        municipality (by IBGE code) and saves them to the database.

        Returns the number of contracts created or retrieved.
        """
        if not codigo_orgao:
            raise ValueError(
                "A API de contratos do Portal da Transparência exige codigoOrgao. "
                "Sincronização por município/UF não é suportada por esse endpoint."
            )

        total = 0
        municipio = self._obter_ou_criar_municipio(codigo_ibge, municipio_nome, estado_uf)

        client = TransparenciaClient()
        try:
            for schema in client.contratos(codigo_orgao=codigo_orgao, paginas=paginas):
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
        codigo_ibge: str = "",
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

    def ingerir_contratos_pncp_por_municipio(
        self,
        *,
        municipio_nome: str,
        estado_uf: str,
        codigo_ibge: str = "",
        paginas: int | None = 1,
        data_inicio: str = "",
        data_fim: str = "",
    ) -> int:
        """Busca contratos no PNCP por intervalo e filtra pelo município do órgão."""
        total = 0
        municipio = self._obter_ou_criar_municipio(
            codigo_ibge,
            municipio_nome,
            estado_uf,
        )

        ano_atual = date.today().year
        data_inicio = data_inicio or f"{ano_atual}0101"
        data_fim = data_fim or f"{ano_atual}1231"

        client = PNCPClient()
        try:
            for schema in client.contratos_recentes(
                data_inicio=data_inicio,
                data_fim=data_fim,
                paginas=paginas,
            ):
                unidade = schema.unidade_orgao
                if not unidade:
                    continue

                codigo_match = (
                    str(unidade.codigo_ibge) == municipio.codigo_ibge
                    if unidade.codigo_ibge is not None
                    else False
                )
                cidade_match = (
                    unidade.municipio_nome.strip().lower() == municipio.nome.strip().lower()
                    and unidade.uf_sigla.strip().upper() == municipio.estado
                )

                if not (codigo_match or cidade_match):
                    continue

                try:
                    self._salvar_contrato_pncp(schema, municipio)
                    total += 1
                except Exception as exc:  # noqa: BLE001
                    logger.error(
                        "Erro ao salvar contrato PNCP %s para %s/%s: %s",
                        schema.numero_contrato,
                        municipio.nome,
                        municipio.estado,
                        exc,
                    )
        finally:
            client.close()

        logger.info(
            "Ingestão PNCP por município concluída: %d contratos para %s/%s.",
            total,
            municipio.nome,
            municipio.estado,
        )
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

    # ── Ingestão Unificada ────────────────────────────────────────────────────

    def ingerir_tudo_por_municipio(
        self,
        municipio_nome: str,
        estado_uf: str,
        codigo_ibge: str = "",
        paginas: int | None = 1,
        data_inicio: str = "",
        data_fim: str = "",
    ) -> dict[str, int]:
        """Ingere dados de TODAS as fontes para um município.

        Resolve automaticamente o código IBGE (se não fornecido) e coleta
        contratos do PNCP e do Portal da Transparência.

        Returns:
            Dict com totais por fonte, ex: ``{"pncp": 15, "transparencia": 42}``.
        """
        resultados: dict[str, int] = {"pncp": 0, "transparencia": 0}

        # 1. Resolver identidade do município
        codigo_ibge, nome_oficial, estado = self._resolver_identidade_municipio(
            codigo_ibge=codigo_ibge,
            nome=municipio_nome,
            estado=estado_uf,
        )
        municipio = self._obter_ou_criar_municipio(codigo_ibge, nome_oficial, estado)

        logger.info(
            "Ingestão unificada iniciada para %s/%s (IBGE: %s).",
            municipio.nome,
            municipio.estado,
            municipio.codigo_ibge,
        )

        # 2. PNCP — descobrir órgãos no município e buscar contratos
        try:
            pncp_client = PNCPClient()
            try:
                orgaos_pncp = pncp_client.contratacoes_por_municipio(
                    codigo_ibge=municipio.codigo_ibge,
                    uf=municipio.estado,
                    data_inicio=data_inicio,
                    data_fim=data_fim,
                    paginas=paginas,
                )
            finally:
                pncp_client.close()

            logger.info(
                "%d órgão(s) com contratações no PNCP para %s/%s.",
                len(orgaos_pncp),
                municipio.nome,
                municipio.estado,
            )

            for orgao_info in orgaos_pncp:
                cnpj = orgao_info.get("cnpj", "")
                if not cnpj:
                    continue
                try:
                    total = self.ingerir_contratos_pncp(
                        cnpj_orgao=cnpj,
                        municipio_nome=municipio.nome,
                        estado_uf=municipio.estado,
                        codigo_ibge=municipio.codigo_ibge,
                        paginas=paginas,
                        data_inicio=data_inicio,
                        data_fim=data_fim,
                    )
                    resultados["pncp"] += total
                except Exception as exc:  # noqa: BLE001
                    logger.error(
                        "Erro ao ingerir contratos PNCP do órgão %s: %s",
                        cnpj,
                        exc,
                    )
        except Exception as exc:  # noqa: BLE001
            logger.error("Erro na ingestão PNCP para %s/%s: %s", municipio.nome, municipio.estado, exc)

        # 3. Transparência — descobrir órgãos e buscar contratos
        try:
            client = TransparenciaClient()
            try:
                orgaos = client.orgaos_por_municipio(municipio.codigo_ibge)
            finally:
                client.close()

            logger.info(
                "%d órgão(s) encontrado(s) na Transparência para %s/%s.",
                len(orgaos),
                municipio.nome,
                municipio.estado,
            )

            for orgao in orgaos:
                if not orgao.codigo:
                    continue
                try:
                    total = self.ingerir_contratos_transparencia(
                        codigo_orgao=orgao.codigo,
                        codigo_ibge=municipio.codigo_ibge,
                        municipio_nome=municipio.nome,
                        estado_uf=municipio.estado,
                        paginas=paginas,
                    )
                    resultados["transparencia"] += total
                except Exception as exc:  # noqa: BLE001
                    logger.error(
                        "Erro ao ingerir órgão %s (%s) da Transparência: %s",
                        orgao.codigo,
                        orgao.descricao,
                        exc,
                    )
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Erro ao buscar órgãos na Transparência para %s/%s: %s",
                municipio.nome,
                municipio.estado,
                exc,
            )

        logger.info(
            "Ingestão unificada concluída para %s/%s: PNCP=%d, Transparência=%d.",
            municipio.nome,
            municipio.estado,
            resultados["pncp"],
            resultados["transparencia"],
        )
        return resultados

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _obter_ou_criar_municipio(
        self,
        codigo_ibge: str,
        nome: str,
        estado: str,
    ) -> Municipio:
        codigo_ibge, nome, estado = self._resolver_identidade_municipio(
            codigo_ibge=codigo_ibge,
            nome=nome,
            estado=estado,
        )
        return MunicipioService.obter_ou_criar(
            nome=nome or f"Município IBGE {codigo_ibge}",
            estado=estado[:2] if estado else "BR",
            codigo_ibge=codigo_ibge,
            populacao=_FALLBACK_POPULACAO,
        )

    def _resolver_identidade_municipio(
        self,
        *,
        codigo_ibge: str,
        nome: str,
        estado: str,
    ) -> tuple[str, str, str]:
        codigo_ibge = (codigo_ibge or "").strip()
        nome = (nome or "").strip()
        estado = (estado or "").strip().upper()

        if codigo_ibge:
            municipio = Municipio.objects.filter(codigo_ibge=codigo_ibge).first()
            if municipio:
                return (
                    codigo_ibge,
                    nome or municipio.nome,
                    estado or municipio.estado,
                )
            return (
                codigo_ibge,
                nome or f"Município IBGE {codigo_ibge}",
                estado or "BR",
            )

        if not nome or not estado:
            raise ValueError(
                "Informe o código IBGE ou um par válido de município e UF."
            )
        if estado == "BR":
            raise ValueError(
                "Informe uma UF válida de 2 letras para resolver o município pelo IBGE."
            )

        client = IBGEClient()
        try:
            item = client.buscar_municipio_por_nome(nome=nome, uf=estado)
        finally:
            client.close()

        if not item:
            raise ValueError(
                f"Município '{nome}/{estado}' não encontrado na API de localidades do IBGE."
            )

        codigo = str(item.get("id", "")).strip()
        nome_oficial = str(item.get("nome", nome)).strip() or nome
        if not codigo:
            raise ValueError(
                f"A API do IBGE não retornou um código válido para '{nome}/{estado}'."
            )

        return codigo, nome_oficial, estado
