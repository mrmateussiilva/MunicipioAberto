"""Unit tests for PNCPClient."""

from __future__ import annotations

import httpx
import pytest

from apps.ingestion.clients.pncp import PNCPClient

CONTRATO_FIXTURE = {
    "numeroControlePNCP": "00394460000141-2024-000001/1",
    "numeroContratoEmpenho": "CT-PNCP-001",
    "objeto": "Contratação de serviços de TI",
    "valorGlobal": 250000.50,
    "dataAssinatura": "2024-03-01",
    "dataPublicacaoPncp": "2024-03-05",
    "nomeRazaoSocialFornecedor": "Tech Solutions SA",
    "niFornecedor": "98765432000111",
    "nomeUnidadeOrgao": "Ministério da Educação",
    "codigoUnidadeOrgao": "00394460000141",
    "unidadeOrgao": {
        "codigoUnidade": "26246",
        "nomeUnidade": "Campus Colatina",
        "codigoIbge": 3201506,
        "municipioNome": "Colatina",
        "ufSigla": "ES",
        "ufNome": "Espirito Santo",
    },
}

ITEM_FIXTURE = {
    "numeroItem": 1,
    "descricao": "Servidor rack 2U",
    "quantidade": 10,
    "valorUnitario": 15000.00,
    "valorTotal": 150000.00,
}


def _make_transport(pages: list):
    call_idx = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_idx
        page = pages[call_idx] if call_idx < len(pages) else {}
        call_idx += 1
        return httpx.Response(200, json=page)

    return httpx.MockTransport(handler)


class TestPNCPClient:

    def test_contratos_por_orgao_yields_schemas(self):
        client = PNCPClient()
        client._client = httpx.Client(
            base_url=client.base_url,
            transport=_make_transport([
                {"data": [CONTRATO_FIXTURE]},
                {"data": []},
            ])
        )

        contratos = list(client.contratos_por_orgao("00394460000141"))
        assert len(contratos) == 1
        c = contratos[0]
        assert c.numero_contrato == "CT-PNCP-001"
        assert float(c.valor_global) == 250000.50
        assert c.ni_fornecedor == "98765432000111"
        assert c.unidade_orgao is not None
        assert c.unidade_orgao.codigo_ibge == 3201506

    def test_contratos_date_parsing(self):
        client = PNCPClient()
        client._client = httpx.Client(
            base_url=client.base_url,
            transport=_make_transport([
                {"data": [CONTRATO_FIXTURE]},
                {"data": []},
            ])
        )

        contratos = list(client.contratos_por_orgao("00394460000141"))
        c = contratos[0]
        assert c.data_assinatura_date is not None
        assert c.data_assinatura_date.year == 2024
        assert c.data_assinatura_date.month == 3

    def test_itens_contrato_yields_items(self):
        client = PNCPClient()
        client._client = httpx.Client(
            base_url=client.base_url,
            transport=_make_transport([
                {"data": [ITEM_FIXTURE]},
                {"data": []},
            ])
        )

        itens = list(client.itens_contrato("00394460000141", 2024, 1))
        assert len(itens) == 1
        assert itens[0].numero_item == 1
        assert float(itens[0].valor_total) == 150000.00

    def test_contratos_recentes(self):
        client = PNCPClient()
        client._client = httpx.Client(
            base_url=client.base_url,
            transport=_make_transport([
                {"data": [CONTRATO_FIXTURE]},
                {"data": []},
            ])
        )

        contratos = list(client.contratos_recentes("20240101", "20240131"))
        assert len(contratos) == 1
