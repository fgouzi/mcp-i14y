"""Unit tests for agents tools."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest


MOCK_AGENTS = json.dumps({
    "data": [
        {
            "id": "agent-uuid-001",
            "identifier": "CH1",
            "name": {"de": "Bundesamt für Statistik", "fr": "Office fédéral de la statistique"},
            "prefLabel": {"de": "BFS", "fr": "OFS"},
            "homePage": "https://www.bfs.admin.ch",
        }
    ],
    "totalItems": 1,
    "page": 1,
    "pageSize": 25,
})

MOCK_AGENT_DETAIL = json.dumps({
    "id": "agent-uuid-001",
    "identifier": "CH1",
    "name": {"de": "Bundesamt für Statistik", "fr": "Office fédéral de la statistique"},
    "description": {"fr": "L'Office fédéral de la statistique est le centre de compétence de la Confédération en matière de statistique."},
    "homePage": "https://www.bfs.admin.ch",
})


@pytest.mark.asyncio
async def test_list_agents():
    with patch("helpers.core_api_client.CoreApiClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = MOCK_AGENTS
        from mcp.server.fastmcp import FastMCP
        from tools.agents import register

        mcp = FastMCP("test")
        register(mcp)
        tool = next(t for t in mcp._tool_manager.list_tools() if t.name == "list_agents")
        result = await tool.fn()

    parsed = json.loads(result)
    assert parsed["totalItems"] == 1
    assert parsed["data"][0]["identifier"] == "CH1"


@pytest.mark.asyncio
async def test_get_agent():
    with patch("helpers.core_api_client.CoreApiClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = MOCK_AGENT_DETAIL
        from mcp.server.fastmcp import FastMCP
        from tools.agents import register

        mcp = FastMCP("test")
        register(mcp)
        tool = next(t for t in mcp._tool_manager.list_tools() if t.name == "get_agent")
        result = await tool.fn(agent_id="agent-uuid-001")

    parsed = json.loads(result)
    assert parsed["id"] == "agent-uuid-001"
    assert parsed["identifier"] == "CH1"
