"""Unit tests for the TransparenciaClient."""

from __future__ import annotations

import json

import httpx
import pytest

from apps.ingestion.clients.transparencia import TransparenciaClient

# Sample fixture data matching the Portal da Transparência JSON format
CONTRATO_FIXTURE = {
    "id": 1001,
    "numero": "CT-2024-001",
    "objeto": "Fornecimento de material de escritório",
    "valorInicial": 50000.00,
    "dataAssinatura": "2024-01-15",
    "dataPublicacaoDou": "2024-01-20",
    "urlDocumento": "https://portaldatransparencia.gov.br/contratos/1001",
    "nomeFornecedor": "Papelaria Central Ltda",
    "cnpjFormatado": "12.345.678/0001-90",
    "nomeOrgao": "Prefeitura Municipal",
    "ufOrgao": "SP",
    "codigoIBGE": "3550308",
}

LICITACAO_FIXTURE = {
    "numero": "LIC-2024-001",
    "objeto": "Licitação para serviços de limpeza",
    "valorEstimado": 120000.00,
    "dataAbertura": "2024-02-10",
    "nomeOrgao": "Prefeitura Municipal",
    "ufOrgao": "SP",
}


def _make_transport(pages: list[list[dict]]):
    """Creates a mock transport that returns paginated responses."""
    call_idx = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_idx
        data = pages[call_idx] if call_idx < len(pages) else []
        call_idx += 1
        return httpx.Response(200, json=data)

    return httpx.MockTransport(handler)


class TestTransparenciaClient:

    def test_contratos_yields_valid_schemas(self):
        client = TransparenciaClient(api_key="test-key")
        client._client = httpx.Client(
            base_url=client.base_url,
            transport=_make_transport([[CONTRATO_FIXTURE], []])
        )

        contratos = list(client.contratos(codigo_orgao="26246"))
        assert len(contratos) == 1

        c = contratos[0]
        assert c.numero == "CT-2024-001"
        assert float(c.valor_inicial) == 50000.00
        assert c.nome_fornecedor == "Papelaria Central Ltda"
        assert c.cnpj_fornecedor == "12.345.678/0001-90"

    def test_contratos_date_parsing(self):
        client = TransparenciaClient(api_key="test-key")
        client._client = httpx.Client(
            base_url=client.base_url,
            transport=_make_transport([[CONTRATO_FIXTURE], []])
        )

        contratos = list(client.contratos(codigo_orgao="26246"))
        c = contratos[0]
        assert c.data_assinatura_date is not None
        assert c.data_assinatura_date.year == 2024
        assert c.data_assinatura_date.month == 1
        assert c.data_assinatura_date.day == 15

    def test_contratos_respects_paginas_limit(self):
        pages = [[CONTRATO_FIXTURE], [CONTRATO_FIXTURE], [CONTRATO_FIXTURE]]
        client = TransparenciaClient(api_key="test-key")
        client._client = httpx.Client(
            base_url=client.base_url,
            transport=_make_transport(pages)
        )

        contratos = list(client.contratos(codigo_orgao="26246", paginas=2))
        assert len(contratos) == 2

    def test_contratos_skips_invalid_records(self):
        bad_record = {"id": 999}  # Missing all required fields
        client = TransparenciaClient(api_key="test-key")
        client._client = httpx.Client(
            base_url=client.base_url,
            transport=_make_transport([[CONTRATO_FIXTURE, bad_record], []])
        )

        # Schema validation has defaults, so both should be yielded without crashing
        contratos = list(client.contratos(codigo_orgao="26246"))
        assert len(contratos) == 2

    def test_licitacoes_yields_valid_schemas(self):
        client = TransparenciaClient(api_key="test-key")
        client._client = httpx.Client(
            base_url=client.base_url,
            transport=_make_transport([[LICITACAO_FIXTURE], []])
        )

        licitacoes = list(client.licitacoes(codigo_ibge="3550308"))
        assert len(licitacoes) == 1
        assert licitacoes[0].numero == "LIC-2024-001"
        assert float(licitacoes[0].valor_estimado) == 120000.00
