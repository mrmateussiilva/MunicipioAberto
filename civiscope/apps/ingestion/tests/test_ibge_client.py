"""Unit tests for IBGEClient."""

from __future__ import annotations

import httpx

from apps.ingestion.clients.ibge import IBGEClient


def _make_transport(payload: list[dict]):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    return httpx.MockTransport(handler)


class TestIBGEClient:

    def test_busca_municipio_por_nome_encontra_por_uf(self):
        client = IBGEClient()
        client._client = httpx.Client(
            base_url=client.base_url,
            transport=_make_transport(
                [
                    {"id": 3201506, "nome": "Colatina"},
                    {"id": 3201605, "nome": "Conceição da Barra"},
                ]
            ),
        )

        item = client.buscar_municipio_por_nome("colatina", "ES")

        assert item is not None
        assert item["id"] == 3201506

    def test_busca_municipio_por_nome_ignora_acentos(self):
        client = IBGEClient()
        client._client = httpx.Client(
            base_url=client.base_url,
            transport=_make_transport(
                [
                    {"id": 3201605, "nome": "Conceição da Barra"},
                ]
            ),
        )

        item = client.buscar_municipio_por_nome("Conceicao da Barra", "ES")

        assert item is not None
        assert item["nome"] == "Conceição da Barra"

