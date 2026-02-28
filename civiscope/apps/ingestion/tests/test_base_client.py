"""Tests for the BaseAPIClient and common pagination logic."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from apps.ingestion.clients.base import APIError, BaseAPIClient


class ConcreteClient(BaseAPIClient):
    """Minimal concrete subclass for testing BaseAPIClient."""
    base_url = "https://example.com"


def _mock_transport(responses: list[dict]) -> httpx.MockTransport:
    """Return an httpx transport that serves responses in sequence."""
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        data = responses[min(call_count, len(responses) - 1)]
        call_count += 1
        return httpx.Response(200, json=data)

    return httpx.MockTransport(handler)


class TestBaseAPIClient:

    def test_get_success(self):
        payload = {"foo": "bar"}

        client = ConcreteClient()
        client._client = httpx.Client(
            base_url=client.base_url,
            transport=httpx.MockTransport(lambda r: httpx.Response(200, json=payload))
        )

        result = client._get("/test")
        assert result == payload

    def test_get_raises_api_error_on_4xx(self):
        client = ConcreteClient()
        client._client = httpx.Client(
            base_url=client.base_url,
            transport=httpx.MockTransport(lambda r: httpx.Response(404, json={"detail": "not found"}))
        )

        with pytest.raises(APIError) as exc_info:
            client._get("/not-found")

        assert exc_info.value.status_code == 404

    def test_paginate_stops_on_empty(self):
        pages = [
            [{"id": 1}, {"id": 2}],
            [{"id": 3}],
            [],  # Stop signal
        ]
        call_idx = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_idx
            response = httpx.Response(200, json=pages[call_idx])
            call_idx += 1
            return response

        client = ConcreteClient()
        client._client = httpx.Client(
            base_url=client.base_url,
            transport=httpx.MockTransport(handler)
        )

        items = list(client.paginate("/items", page_size=2))
        assert len(items) == 3
        assert items[0] == {"id": 1}

    def test_paginate_respects_max_pages(self):
        pages = [
            [{"id": i} for i in range(10)],
            [{"id": i} for i in range(10, 20)],
            [{"id": i} for i in range(20, 30)],
        ]
        call_idx = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_idx
            response = httpx.Response(200, json=pages[call_idx])
            call_idx = min(call_idx + 1, len(pages) - 1)
            return response

        client = ConcreteClient()
        client._client = httpx.Client(
            base_url=client.base_url,
            transport=httpx.MockTransport(handler)
        )

        items = list(client.paginate("/items", max_pages=2, page_size=10))
        assert len(items) == 20

    def test_rate_limit_respected(self):
        """Rate limiting should insert a small sleep between calls."""
        client = ConcreteClient()
        client._client = httpx.Client(
            base_url=client.base_url,
            transport=httpx.MockTransport(lambda r: httpx.Response(200, json={}))
        )

        with patch("apps.ingestion.clients.base.time.sleep") as mock_sleep:
            # Simulate last request was "just now"
            import time
            client._last_request_time = time.monotonic()
            client._rate_limit()
            mock_sleep.assert_called_once()

    def test_context_manager_closes_client(self):
        with ConcreteClient() as client:
            assert client._client is not None
        # After exit, the internal client is closed (no exception)
