"""Unit tests for DadosAbertosClient."""

from __future__ import annotations

import httpx
import pytest

from apps.ingestion.clients.dados_abertos import DadosAbertosClient

DATASET_FIXTURE = {
    "id": "abc-123",
    "title": "Contratos Municipais 2024",
    "notes": "Dataset de contratos públicos",
    "organization": {"name": "municipio-sp"},
    "resources": [
        {
            "id": "res-001",
            "name": "contratos_jan_2024.csv",
            "description": "Contratos de janeiro de 2024",
            "url": "https://dados.gov.br/files/contratos_jan_2024.csv",
            "format": "CSV",
        }
    ],
}


def _make_search_transport(results: list[dict], total_count: int = 1):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"result": {"count": total_count, "results": results}},
        )
    return httpx.MockTransport(handler)


def _make_show_transport(dataset: dict):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"result": dataset})
    return httpx.MockTransport(handler)


class TestDadosAbertosClient:

    def test_buscar_datasets_yields_schemas(self):
        client = DadosAbertosClient()
        client._client = httpx.Client(
            base_url=client.base_url,
            transport=_make_search_transport([DATASET_FIXTURE])
        )

        datasets = list(client.buscar_datasets("contratos municipais", rows=10))
        assert len(datasets) == 1
        ds = datasets[0]
        assert ds.id == "abc-123"
        assert ds.title == "Contratos Municipais 2024"
        assert len(ds.resources) == 1
        assert ds.resources[0].format == "CSV"

    def test_buscar_datasets_empty_result(self):
        client = DadosAbertosClient()
        client._client = httpx.Client(
            base_url=client.base_url,
            transport=_make_search_transport([])
        )

        datasets = list(client.buscar_datasets("inexistente"))
        assert datasets == []

    def test_recursos_do_dataset_returns_list(self):
        client = DadosAbertosClient()
        client._client = httpx.Client(
            base_url=client.base_url,
            transport=_make_show_transport(DATASET_FIXTURE)
        )

        recursos = client.recursos_do_dataset("abc-123")
        assert len(recursos) == 1
        assert recursos[0].name == "contratos_jan_2024.csv"
        assert recursos[0].url.endswith(".csv")

    def test_listar_organizacoes(self):
        orgs = ["municipio-sp", "governo-federal", "mec"]

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"result": orgs})

        client = DadosAbertosClient()
        client._client = httpx.Client(
            base_url=client.base_url,
            transport=httpx.MockTransport(handler)
        )

        result = client.listar_organizacoes()
        assert result == orgs
