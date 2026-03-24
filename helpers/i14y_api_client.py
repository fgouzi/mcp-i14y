"""Async HTTP client for the Swiss I14Y Public API."""

from __future__ import annotations

import json
import logging

import httpx

from helpers.env_config import get_base_url

__all__ = ["I14YApiClient"]

logger = logging.getLogger(__name__)

VERSION = "0.1.0"
USER_AGENT = f"mcp-i14y/{VERSION} (https://github.com/fgouzi/mcp-i14y)"

# Content types returned as plain text (not parsed as JSON)
_PLAIN_TEXT_TYPES = {"text/turtle", "application/rdf+xml", "text/csv", "text/plain"}


def _build_params(**kwargs: object) -> dict[str, str]:
    """Build a query-parameter dict, dropping any None values."""
    return {k: str(v) for k, v in kwargs.items() if v is not None}


class I14YApiClient:
    """Reusable async HTTP client for the I14Y Public API.

    Usage::

        async with I14YApiClient() as client:
            data = await client.get("/datasets", page=1, pageSize=25)
    """

    def __init__(self) -> None:
        self._base_url = get_base_url()
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "I14YApiClient":
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
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
            path: API path relative to the base URL (e.g. "/datasets").
            **params: Query parameters; None values are stripped automatically.

        Returns:
            JSON-serialised string for JSON responses, or raw text for RDF/TTL/CSV.

        Raises:
            RuntimeError: If called outside of an async context manager.
        """
        if self._client is None:
            raise RuntimeError("I14YApiClient must be used as an async context manager.")

        query = _build_params(**params)
        logger.debug("GET %s params=%s", path, query)

        try:
            response = await self._client.get(path, params=query)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            return json.dumps(
                {
                    "error": f"I14Y API returned HTTP {exc.response.status_code}",
                    "url": str(exc.request.url),
                }
            )
        except httpx.RequestError as exc:
            return json.dumps({"error": f"Network error while contacting I14Y API: {exc}"})

        content_type = response.headers.get("content-type", "")
        if any(ct in content_type for ct in _PLAIN_TEXT_TYPES):
            return response.text

        try:
            return json.dumps(response.json(), ensure_ascii=False, indent=2)
        except Exception:
            return response.text
