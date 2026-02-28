"""Integration tests for IngestaoAPIService (simulated end-to-end)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from apps.ingestion.clients.schemas import PNCPContratoSchema, TransparenciaContratoSchema


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_transparencia_schema(**overrides) -> TransparenciaContratoSchema:
    defaults = dict(
        id=1,
        numero="CT-2024-001",
        objeto="Fornecimento de material",
        valorInicial=10000.00,
        dataAssinatura="2024-01-10",
        dataPublicacaoDou="2024-01-15",
        nomeFornecedor="Empresa Teste Ltda",
        cnpjFormatado="12.345.678/0001-90",
        ufOrgao="SP",
    )
    defaults.update(overrides)
    return TransparenciaContratoSchema.model_validate(defaults)


def _make_pncp_schema(**overrides) -> PNCPContratoSchema:
    defaults = dict(
        numeroControlePNCP="ORG-2024-001",
        numeroContratoEmpenho="CT-001",
        objeto="Serviços de TI",
        valorGlobal=50000.00,
        dataAssinatura="2024-02-01",
        nomeRazaoSocialFornecedor="TI Corp SA",
        niFornecedor="98765432000111",
    )
    defaults.update(overrides)
    return PNCPContratoSchema.model_validate(defaults)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestIngestaoAPIService:

    @patch("apps.ingestion.api_service.TransparenciaClient")
    def test_ingerir_contratos_transparencia(self, MockClient):
        from apps.ingestion.api_service import IngestaoAPIService

        schema = _make_transparencia_schema()
        instance = MockClient.return_value.__enter__.return_value = MagicMock()
        instance.contratos.return_value = iter([schema])
        MockClient.return_value.contratos.return_value = iter([schema])

        service = IngestaoAPIService()

        # Override client on the service instance
        mock_client = MagicMock()
        mock_client.contratos.return_value = iter([schema])

        with patch.object(service, "_obter_ou_criar_municipio") as mock_mun, \
             patch("apps.ingestion.api_service.TransparenciaClient", return_value=mock_client), \
             patch("apps.ingestion.api_service.EmpresaService") as mock_emp, \
             patch("apps.ingestion.api_service.ContratoService") as mock_cont:

            mock_municipio = MagicMock()
            mock_mun.return_value = mock_municipio
            mock_emp.obter_ou_criar.return_value = MagicMock()
            mock_cont.criar.return_value = MagicMock()

            total = service.ingerir_contratos_transparencia(
                codigo_ibge="3550308",
                municipio_nome="São Paulo",
                estado_uf="SP",
                paginas=1,
            )

        assert total == 1
        mock_cont.criar.assert_called_once()

    @patch("apps.ingestion.api_service.PNCPClient")
    def test_ingerir_contratos_pncp(self, MockClient):
        from apps.ingestion.api_service import IngestaoAPIService

        schema = _make_pncp_schema()
        mock_client = MagicMock()
        mock_client.contratos_por_orgao.return_value = iter([schema])

        service = IngestaoAPIService()

        with patch.object(service, "_obter_ou_criar_municipio") as mock_mun, \
             patch("apps.ingestion.api_service.PNCPClient", return_value=mock_client), \
             patch("apps.ingestion.api_service.EmpresaService") as mock_emp, \
             patch("apps.ingestion.api_service.ContratoService") as mock_cont:

            mock_mun.return_value = MagicMock()
            mock_emp.obter_ou_criar.return_value = MagicMock()
            mock_cont.criar.return_value = MagicMock()

            total = service.ingerir_contratos_pncp(
                cnpj_orgao="00394460000141",
                paginas=1,
            )

        assert total == 1
        mock_cont.criar.assert_called_once()

    def test_schema_transparencia_date_handling(self):
        schema = _make_transparencia_schema(dataAssinatura=None, dataPublicacaoDou=None)
        assert schema.data_assinatura_date is None
        assert schema.data_publicacao_date is None

    def test_schema_pncp_decimal_coercion(self):
        schema = _make_pncp_schema(valorGlobal="abc")
        assert schema.valor_global == Decimal("0")

    def test_schema_transparencia_decimal_coercion(self):
        schema = _make_transparencia_schema(valorInicial=None)
        assert schema.valor_inicial == Decimal("0")
