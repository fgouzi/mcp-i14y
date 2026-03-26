"""Async HTTP client for the Swiss I14Y CORE API."""

from __future__ import annotations

import json
import logging

import httpx

__all__ = ["CoreApiClient"]

logger = logging.getLogger(__name__)

_CORE_BASE_URL = "https://core.i14y.c.bfs.admin.ch/api"

VERSION = "0.1.0"
USER_AGENT = f"mcp-i14y/{VERSION} (https://github.com/fgouzi/mcp-i14y)"

# Content types returned as plain text (not parsed as JSON)
_PLAIN_TEXT_TYPES = {"text/turtle", "application/rdf+xml", "text/csv", "text/plain"}


def _build_params(**kwargs: object) -> dict[str, str | list]:
    """Build a query-parameter dict, dropping any None values."""
    result: dict[str, str | list] = {}
    for k, v in kwargs.items():
        if v is None:
            continue
        if isinstance(v, list):
            result[k] = [str(i) for i in v if i is not None]
        else:
            result[k] = str(v)
    return result


class CoreApiClient:
    """Reusable async HTTP client for the I14Y CORE API.

    The CORE API (https://core.i14y.c.bfs.admin.ch/api) is publicly accessible
    and provides richer endpoints than the public API, including full-text search,
    identifier-based lookups, and hierarchical codelist navigation.

    Usage::

        async with CoreApiClient() as client:
            data = await client.get("/Catalog/search", query="canton")
    """

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "CoreApiClient":
        self._client = httpx.AsyncClient(
            base_url=_CORE_BASE_URL,
            headers={"User-Agent": USER_AGENT},
            timeout=30.0,
        )
        return self

    async def __aexit__(self, *_: object) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get(self, path: str, **params: object) -> str:
        """Perform a GET request and return the response as a JSON string or plain text.

        Args:
            path: API path relative to the base URL (e.g. "/Catalog/search").
            **params: Query parameters; None values are stripped automatically.
                List values are sent as repeated query parameters.

        Returns:
            JSON-serialised string for JSON responses, or raw text for RDF/TTL/CSV.
        """
        if self._client is None:
            raise RuntimeError("CoreApiClient must be used as an async context manager.")

        query = _build_params(**params)
        logger.debug("CORE GET %s params=%s", path, query)

        try:
            response = await self._client.get(path, params=query)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            return json.dumps(
                {
                    "error": f"I14Y CORE API returned HTTP {exc.response.status_code}",
                    "url": str(exc.request.url),
                }
            )
        except httpx.RequestError as exc:
            return json.dumps({"error": f"Network error while contacting I14Y CORE API: {exc}"})

        content_type = response.headers.get("content-type", "")
        if any(ct in content_type for ct in _PLAIN_TEXT_TYPES):
            return response.text

        try:
            return json.dumps(response.json(), ensure_ascii=False, indent=2)
        except Exception:
            return response.text
