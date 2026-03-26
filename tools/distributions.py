"""MCP tool for reading the content of a DCAT distribution."""

from __future__ import annotations

import json
import logging

import httpx

from mcp.server.fastmcp import FastMCP

__all__ = ["register"]

logger = logging.getLogger(__name__)

VERSION = "0.1.0"
USER_AGENT = f"mcp-i14y/{VERSION} (https://github.com/fgouzi/mcp-i14y)"

# Content types that are safe to read as text
_TEXT_TYPES = {
    "application/json",
    "application/ld+json",
    "application/geo+json",
    "text/csv",
    "text/plain",
    "text/xml",
    "application/xml",
    "application/rdf+xml",
    "text/turtle",
    "application/sparql-results+json",
    "application/sparql-results+xml",
}

# Content types that are binary and cannot be meaningfully returned to an LLM
_BINARY_TYPES = {
    "application/pdf",
    "application/zip",
    "application/gzip",
    "application/x-tar",
    "application/octet-stream",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument",
    "image/",
    "audio/",
    "video/",
}


def _is_binary(content_type: str) -> bool:
    ct = content_type.split(";")[0].strip().lower()
    return any(ct.startswith(bt) for bt in _BINARY_TYPES)


def _is_text(content_type: str) -> bool:
    ct = content_type.split(";")[0].strip().lower()
    return ct.startswith("text/") or any(ct == t for t in _TEXT_TYPES)


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_distribution_content(
        download_url: str,
        max_kb: int = 200,
    ) -> str:
        """Fetch and return the content of a DCAT distribution file.

        Use this after get_dataset() to read the actual data behind a distribution.
        The distribution's downloadUrl.uri (from the get_dataset response) should
        be passed directly as download_url.

        Supports text-based formats: JSON, CSV, XML, RDF/Turtle, GeoJSON, etc.
        Binary formats (PDF, ZIP, Excel, images) are rejected with an error message.
        Content is truncated to max_kb kilobytes if the file is larger.

        Typical workflow:
            1. dataset = get_dataset(dataset_id)
            2. url = dataset["distributions"][0]["downloadUrl"]["uri"]
            3. content = get_distribution_content(url)

        Args:
            download_url: The direct download URL of the distribution
                (value of downloadUrl.uri from a distribution object).
            max_kb: Maximum content size to return in kilobytes (default 200 KB).
                Larger files are truncated with a warning appended.

        Returns:
            File content as a string (JSON pretty-printed, CSV/XML as-is),
            or a JSON error object if the URL is unreachable or content is binary.
        """
        max_bytes = max_kb * 1024

        try:
            async with httpx.AsyncClient(
                headers={"User-Agent": USER_AGENT},
                follow_redirects=True,
                timeout=30.0,
            ) as client:
                # Stream the response to avoid downloading huge files entirely
                async with client.stream("GET", download_url) as response:
                    response.raise_for_status()

                    content_type = response.headers.get("content-type", "")

                    if _is_binary(content_type):
                        ct = content_type.split(";")[0].strip()
                        return json.dumps({
                            "error": (
                                f"Binary content type '{ct}' cannot be returned as text. "
                                "Download the file directly from: " + download_url
                            )
                        })

                    chunks: list[bytes] = []
                    total = 0
                    truncated = False

                    async for chunk in response.aiter_bytes(chunk_size=4096):
                        if total + len(chunk) > max_bytes:
                            # Take only what fits
                            remaining = max_bytes - total
                            chunks.append(chunk[:remaining])
                            truncated = True
                            break
                        chunks.append(chunk)
                        total += len(chunk)

                    raw = b"".join(chunks).decode("utf-8", errors="replace")

                    # Pretty-print JSON if applicable
                    ct_base = content_type.split(";")[0].strip().lower()
                    if "json" in ct_base:
                        try:
                            raw = json.dumps(json.loads(raw), ensure_ascii=False, indent=2)
                        except Exception:
                            pass

                    if truncated:
                        raw += (
                            f"\n\n[TRUNCATED — content exceeds {max_kb} KB. "
                            f"Only the first {max_kb} KB are shown. "
                            f"Full file: {download_url}]"
                        )

                    return raw

        except httpx.HTTPStatusError as exc:
            return json.dumps({
                "error": f"HTTP {exc.response.status_code} fetching distribution",
                "url": download_url,
            })
        except httpx.RequestError as exc:
            return json.dumps({
                "error": f"Network error fetching distribution: {exc}",
                "url": download_url,
            })
