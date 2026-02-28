"""Pydantic schemas for validating API responses from Brazilian public portals."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator


# ──────────────────────────── Helpers ───────────────────────────────────────

def _parse_br_date(value: str | None) -> date | None:
    """Parse common date formats returned by Brazilian public APIs."""
    if not value:
        return None
    
    # Remove time part if it exists (e.g. 2024-03-01T10:00:00)
    clean_value = str(value).split("T")[0].split(" ")[0].strip()
    
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(clean_value, fmt).date()
        except (ValueError, TypeError):
            continue
    return None


# ──────────────────────────── Portal da Transparência ───────────────────────

class TransparenciaContratoSchema(BaseModel):
    """Contrato do Portal da Transparência."""

    id: int | None = None
    numero: str = Field(default="")
    objeto: str = Field(default="")
    valor_inicial: Decimal = Field(default=Decimal("0"), alias="valorInicial")
    data_assinatura: str | None = Field(default=None, alias="dataAssinatura")
    data_publicacao: str | None = Field(default=None, alias="dataPublicacaoDou")
    url_documento: str | None = Field(default=None, alias="urlDocumento")

    # Órgão / fornecedor embutidos
    nome_fornecedor: str = Field(default="", alias="nomeFornecedor")
    cnpj_fornecedor: str = Field(default="", alias="cnpjFormatado")
    nome_orgao: str = Field(default="", alias="nomeOrgao")
    uf_orgao: str = Field(default="BR", alias="ufOrgao")
    codigo_ibge: str | None = Field(default=None, alias="codigoIBGE")

    model_config = {"populate_by_name": True}

    @property
    def data_assinatura_date(self) -> date | None:
        return _parse_br_date(self.data_assinatura)

    @property
    def data_publicacao_date(self) -> date | None:
        return _parse_br_date(self.data_publicacao) or self.data_assinatura_date

    @field_validator("cnpj_fornecedor", mode="before")
    @classmethod
    def normalise_cnpj(cls, v: Any) -> str:
        if v is None:
            return ""
        return str(v).strip()

    @field_validator("valor_inicial", mode="before")
    @classmethod
    def coerce_decimal(cls, v: Any) -> Decimal:
        try:
            return Decimal(str(v))
        except Exception:
            return Decimal("0")


class TransparenciaLicitacaoSchema(BaseModel):
    numero: str = Field(default="")
    objeto: str = Field(default="")
    valor_estimado: Decimal = Field(default=Decimal("0"), alias="valorEstimado")
    data_abertura: str | None = Field(default=None, alias="dataAbertura")
    nome_orgao: str = Field(default="", alias="nomeOrgao")
    uf_orgao: str = Field(default="BR", alias="ufOrgao")

    model_config = {"populate_by_name": True}

    @field_validator("valor_estimado", mode="before")
    @classmethod
    def coerce_decimal(cls, v: Any) -> Decimal:
        try:
            return Decimal(str(v))
        except Exception:
            return Decimal("0")


# ──────────────────────────── PNCP / OCDS ───────────────────────────────────

class PNCPItemSchema(BaseModel):
    numero_item: int = Field(alias="numeroItem")
    descricao: str = Field(default="")
    quantidade: Decimal = Field(default=Decimal("0"))
    valor_unitario: Decimal = Field(default=Decimal("0"), alias="valorUnitario")
    valor_total: Decimal = Field(default=Decimal("0"), alias="valorTotal")

    model_config = {"populate_by_name": True}

    @field_validator("quantidade", "valor_unitario", "valor_total", mode="before")
    @classmethod
    def coerce_decimal(cls, v: Any) -> Decimal:
        try:
            return Decimal(str(v))
        except Exception:
            return Decimal("0")


class PNCPUnidadeSchema(BaseModel):
    codigo_unidade: str = Field(default="", alias="codigoUnidade")
    nome_unidade: str = Field(default="", alias="nomeUnidade")
    codigo_ibge: int | None = Field(default=None, alias="codigoIbge")
    municipio_nome: str = Field(default="", alias="municipioNome")
    uf_sigla: str = Field(default="", alias="ufSigla")
    uf_nome: str = Field(default="", alias="ufNome")

    model_config = {"populate_by_name": True}


class PNCPContratoSchema(BaseModel):
    numero_controle_pncp: str = Field(default="", alias="numeroControlePNCP")
    numero_contrato: str = Field(default="", alias="numeroContratoEmpenho")
    objeto: str = Field(default="")
    valor_global: Decimal = Field(default=Decimal("0"), alias="valorGlobal")
    data_assinatura: str | None = Field(default=None, alias="dataAssinatura")
    data_publicacao: str | None = Field(default=None, alias="dataPublicacaoPncp")

    nome_razao_social_fornecedor: str = Field(default="", alias="nomeRazaoSocialFornecedor")
    ni_fornecedor: str = Field(default="", alias="niFornecedor")
    nome_orgao: str = Field(default="", alias="nomeUnidadeOrgao")
    codigo_unidade_orgao: str = Field(default="", alias="codigoUnidadeOrgao")
    unidade_orgao: PNCPUnidadeSchema | None = Field(default=None, alias="unidadeOrgao")

    model_config = {"populate_by_name": True}

    @property
    def data_assinatura_date(self) -> date | None:
        return _parse_br_date(self.data_assinatura)

    @property
    def data_publicacao_date(self) -> date | None:
        return _parse_br_date(self.data_publicacao) or self.data_assinatura_date

    @field_validator("valor_global", mode="before")
    @classmethod
    def coerce_decimal(cls, v: Any) -> Decimal:
        try:
            return Decimal(str(v))
        except Exception:
            return Decimal("0")


# ──────────────────────────── Dados Abertos ─────────────────────────────────

class DadosAbertosRecursoSchema(BaseModel):
    id: str = Field(default="")
    name: str = Field(default="")
    description: str = Field(default="")
    url: str = Field(default="")
    format: str = Field(default="")
    created: str | None = None
    last_modified: str | None = None

    model_config = {"populate_by_name": True}


class DadosAbertosDatasetSchema(BaseModel):
    id: str = Field(default="")
    title: str = Field(default="")
    notes: str = Field(default="")
    organization: dict | None = None
    resources: list[DadosAbertosRecursoSchema] = Field(default_factory=list)

    model_config = {"populate_by_name": True}
