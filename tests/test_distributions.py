"""Unit tests for get_distribution_content tool."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_stream_response(content: bytes, content_type: str, status_code: int = 200):
    """Build a mock httpx streaming response."""
    mock_response = AsyncMock()
    mock_response.status_code = status_code
    mock_response.headers = {"content-type": content_type}

    def mock_raise_for_status():
        if status_code >= 400:
            import httpx
            request = MagicMock()
            raise httpx.HTTPStatusError(
                f"HTTP {status_code}",
                request=request,
                response=mock_response,
            )

    mock_response.raise_for_status = mock_raise_for_status

    async def aiter_bytes(chunk_size=4096):
        for i in range(0, len(content), chunk_size):
            yield content[i : i + chunk_size]

    mock_response.aiter_bytes = aiter_bytes
    return mock_response


@pytest.mark.asyncio
async def test_get_distribution_content_json():
    payload = {"records": [{"id": 1, "value": "test"}]}
    content = json.dumps(payload).encode()

    mock_cm = AsyncMock()
    mock_cm.__aenter__ = AsyncMock(return_value=_make_stream_response(content, "application/json"))
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient.stream", return_value=mock_cm):
        from mcp.server.fastmcp import FastMCP
        from tools.distributions import register

        mcp = FastMCP("test")
        register(mcp)
        tool = next(t for t in mcp._tool_manager.list_tools() if t.name == "get_distribution_content")
        result = await tool.fn(download_url="https://example.com/data.json")

    parsed = json.loads(result)
    assert parsed["records"][0]["id"] == 1


@pytest.mark.asyncio
async def test_get_distribution_content_csv():
    csv_content = b"id,name,value\n1,Zurich,42\n2,Berne,17\n"

    mock_cm = AsyncMock()
    mock_cm.__aenter__ = AsyncMock(return_value=_make_stream_response(csv_content, "text/csv"))
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient.stream", return_value=mock_cm):
        from mcp.server.fastmcp import FastMCP
        from tools.distributions import register

        mcp = FastMCP("test")
        register(mcp)
        tool = next(t for t in mcp._tool_manager.list_tools() if t.name == "get_distribution_content")
        result = await tool.fn(download_url="https://example.com/data.csv")

    assert "Zurich" in result
    assert "id,name,value" in result


@pytest.mark.asyncio
async def test_get_distribution_content_truncated():
    # 300 KB content, limit 200 KB
    large_content = b"x" * (300 * 1024)

    mock_cm = AsyncMock()
    mock_cm.__aenter__ = AsyncMock(return_value=_make_stream_response(large_content, "text/plain"))
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient.stream", return_value=mock_cm):
        from mcp.server.fastmcp import FastMCP
        from tools.distributions import register

        mcp = FastMCP("test")
        register(mcp)
        tool = next(t for t in mcp._tool_manager.list_tools() if t.name == "get_distribution_content")
        result = await tool.fn(download_url="https://example.com/big.txt", max_kb=200)

    assert "TRUNCATED" in result
    assert len(result.encode()) <= 200 * 1024 + 500  # allow for truncation message


@pytest.mark.asyncio
async def test_get_distribution_content_binary_rejected():
    mock_cm = AsyncMock()
    mock_cm.__aenter__ = AsyncMock(
        return_value=_make_stream_response(b"%PDF-1.4...", "application/pdf")
    )
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient.stream", return_value=mock_cm):
        from mcp.server.fastmcp import FastMCP
        from tools.distributions import register

        mcp = FastMCP("test")
        register(mcp)
        tool = next(t for t in mcp._tool_manager.list_tools() if t.name == "get_distribution_content")
        result = await tool.fn(download_url="https://example.com/doc.pdf")

    parsed = json.loads(result)
    assert "error" in parsed
    assert "binary" in parsed["error"].lower() or "pdf" in parsed["error"].lower()
