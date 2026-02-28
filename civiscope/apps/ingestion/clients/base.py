"""Base HTTP client with retry, rate-limiting, and structured logging."""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Iterator

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = float(os.getenv("API_REQUEST_TIMEOUT", "30"))
_MAX_RETRIES = int(os.getenv("API_MAX_RETRIES", "3"))
_RATE_LIMIT_DELAY = float(os.getenv("API_RATE_LIMIT_DELAY", "0.5"))  # seconds between requests


class APIError(Exception):
    """Raised when an API call fails after all retries."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class BaseAPIClient:
    """
    Base class for all external API clients.

    Features:
    - Configurable base URL and headers via env vars.
    - Automatic retry with exponential back-off (tenacity).
    - Simple rate-limiting via a small sleep between requests.
    - Structured logging at DEBUG / WARNING / ERROR levels.
    - Transparent pagination helper.
    """

    base_url: str = ""
    default_headers: dict[str, str] = {}

    def __init__(self) -> None:
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Accept": "application/json",
                "User-Agent": "CivisScope/1.0 (dados-publicos)",
                **self.default_headers,
            },
            timeout=_DEFAULT_TIMEOUT,
            follow_redirects=True,
        )
        self._last_request_time: float = 0.0

    def _rate_limit(self) -> None:
        """Ensure a minimum gap between consecutive requests."""
        elapsed = time.monotonic() - self._last_request_time
        if elapsed < _RATE_LIMIT_DELAY:
            time.sleep(_RATE_LIMIT_DELAY - elapsed)
        self._last_request_time = time.monotonic()

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Perform a GET request with retry logic."""
        self._rate_limit()
        url = path if path.startswith("http") else path
        logger.debug("GET %s params=%s", url, params)
        try:
            response = self._client.get(url, params=params)
            response.raise_for_status()
            logger.debug("Response %s bytes=%d", response.status_code, len(response.content))
            # Handle 204 No Content or empty body gracefully
            if response.status_code == 204 or not response.content or not response.content.strip():
                return []
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "HTTP error %s for %s: %s",
                exc.response.status_code,
                exc.request.url,
                exc.response.text[:200],
            )
            if exc.response.status_code == 429:
                # Rate-limited by server — wait longer and retry
                time.sleep(60)
                raise httpx.NetworkError("Rate limited") from exc
            raise APIError(
                f"HTTP {exc.response.status_code} from {exc.request.url}",
                status_code=exc.response.status_code,
            ) from exc
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            logger.warning("Network error for %s: %s", url, exc)
            raise

    def paginate(
        self,
        path: str,
        page_param: str = "pagina",
        size_param: str = "tamanhoPagina",
        page_size: int = 100,
        data_key: str | None = None,
        max_pages: int | None = None,
        extra_params: dict[str, Any] | None = None,
    ) -> Iterator[dict]:
        """
        Generic paginator. Yields individual items from each page.

        Supports two pagination styles:
        - PNCP / Transparência: page number + size.
        - Stops when a page returns an empty data list.
        """
        params: dict[str, Any] = {page_param: 1, size_param: page_size, **(extra_params or {})}
        page = 1

        while True:
            if max_pages and page > max_pages:
                logger.debug("Reached max_pages=%d, stopping pagination.", max_pages)
                break

            params[page_param] = page

            try:
                data = self._get(path, params=params)
            except APIError as exc:
                # PNCP returns 400 "Página X inexistente" when page is out of range
                if exc.status_code == 400:
                    logger.debug("Page %d returned 400 — stopping pagination.", page)
                    break
                raise

            # Unwrap data from a known key, or assume the whole response is a list
            if data_key and isinstance(data, dict):
                items = data.get(data_key) or []
            elif isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                # Try common envelope keys
                for key in ("data", "itens", "contratos", "result", "results"):
                    if key in data:
                        items = data[key]
                        break
                else:
                    items = []
            else:
                items = []

            if not items:
                logger.debug("Empty page %d — stopping pagination.", page)
                break

            logger.info("Page %d — %d items from %s", page, len(items), path)
            yield from items
            page += 1

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "BaseAPIClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()
