"""Unit tests for keyword search tools."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest


MOCK_DATASETS = [
    {
        "id": "ds-001",
        "identifier": "px-x-0602010000_109",
        "title": {
            "de": "Arbeitsstätten und Beschäftigte nach Kanton und Grössenklasse",
            "fr": "Etablissements et emplois selon le canton et la classe de taille",
            "en": "Establishments and employment by canton and size class",
        },
        "description": {"fr": "Statistiques des établissements selon le canton."},
        "publisher": {"identifier": "CH1", "name": {"fr": "OFS"}},
        "registrationStatus": "Recorded",
    },
    {
        "id": "ds-002",
        "identifier": "BFS-POP-2023",
        "title": {"de": "Bevölkerungsstatistik", "fr": "Statistique démographique"},
        "description": {"fr": "Population résidente permanente par canton."},
        "publisher": {"identifier": "CH1"},
        "registrationStatus": "Standard",
    },
]

MOCK_CONCEPTS = [
    {
        "id": "concept-001",
        "identifier": "HGDE_KT",
        "name": {"de": "Schweizer Kantone", "fr": "Cantons suisses", "en": "Swiss cantons"},
        "description": {"fr": "Les 26 cantons de la Confédération suisse."},
        "conceptType": "CodeList",
        "codeListEntryValueType": "Numeric",
        "registrationStatus": "Recorded",
        "version": "1.0.0",
        "publisher": {"identifier": "CH1"},
    },
    {
        "id": "concept-002",
        "identifier": "DV_KT_BEZ_GDE_SNAP",
        "name": {"fr": "Cantons, districts et communes (01.01.2024)"},
        "description": {"fr": "Variable reliant la Suisse, ses cantons, districts et communes."},
        "conceptType": "CodeList",
        "codeListEntryValueType": "String",
        "registrationStatus": "Recorded",
        "version": "2024.1.0",
        "publisher": {"identifier": "CH1"},
    },
]


@pytest.mark.asyncio
async def test_search_datasets_finds_match():
    with patch(
        "helpers.i14y_api_client.I14YApiClient.get_all_pages", new_callable=AsyncMock
    ) as mock_pages:
        mock_pages.return_value = MOCK_DATASETS
        from mcp.server.fastmcp import FastMCP
        from tools.search import register

        mcp = FastMCP("test")
        register(mcp)
        tool = next(t for t in mcp._tool_manager.list_tools() if t.name == "search_datasets")
        result = await tool.fn(keyword="canton taille")

    parsed = json.loads(result)
    assert parsed["keyword"] == "canton taille"
    assert parsed["total_scanned"] == 2
    assert len(parsed["matches"]) >= 1
    assert parsed["matches"][0]["id"] == "ds-001"


@pytest.mark.asyncio
async def test_search_datasets_no_match():
    with patch(
        "helpers.i14y_api_client.I14YApiClient.get_all_pages", new_callable=AsyncMock
    ) as mock_pages:
        mock_pages.return_value = MOCK_DATASETS
        from mcp.server.fastmcp import FastMCP
        from tools.search import register

        mcp = FastMCP("test")
        register(mcp)
        tool = next(t for t in mcp._tool_manager.list_tools() if t.name == "search_datasets")
        result = await tool.fn(keyword="xxxxnotfound")

    parsed = json.loads(result)
    assert parsed["matches"] == []


@pytest.mark.asyncio
async def test_search_datasets_respects_max_results():
    with patch(
        "helpers.i14y_api_client.I14YApiClient.get_all_pages", new_callable=AsyncMock
    ) as mock_pages:
        mock_pages.return_value = MOCK_DATASETS
        from mcp.server.fastmcp import FastMCP
        from tools.search import register

        mcp = FastMCP("test")
        register(mcp)
        tool = next(t for t in mcp._tool_manager.list_tools() if t.name == "search_datasets")
        result = await tool.fn(keyword="canton", max_results=1)

    parsed = json.loads(result)
    assert len(parsed["matches"]) <= 1


@pytest.mark.asyncio
async def test_search_concepts_finds_canton():
    with patch(
        "helpers.i14y_api_client.I14YApiClient.get_all_pages", new_callable=AsyncMock
    ) as mock_pages:
        mock_pages.return_value = MOCK_CONCEPTS
        from mcp.server.fastmcp import FastMCP
        from tools.search import register

        mcp = FastMCP("test")
        register(mcp)
        tool = next(t for t in mcp._tool_manager.list_tools() if t.name == "search_concepts")
        result = await tool.fn(keyword="cantons suisses")

    parsed = json.loads(result)
    assert len(parsed["matches"]) >= 1
    assert parsed["matches"][0]["id"] == "concept-001"


@pytest.mark.asyncio
async def test_find_concept_for_variable_canton():
    with patch(
        "helpers.i14y_api_client.I14YApiClient.get_all_pages", new_callable=AsyncMock
    ) as mock_pages:
        mock_pages.return_value = MOCK_CONCEPTS
        from mcp.server.fastmcp import FastMCP
        from tools.search import register

        mcp = FastMCP("test")
        register(mcp)
        tool = next(
            t for t in mcp._tool_manager.list_tools() if t.name == "find_concept_for_variable"
        )
        result = await tool.fn(variable_name="Canton")

    parsed = json.loads(result)
    assert parsed["variable_name"] == "Canton"
    assert len(parsed["candidates"]) >= 1
    assert "tip" in parsed
    # HGDE_KT should rank first (name matches "canton" exactly in all languages)
    assert parsed["candidates"][0]["identifier"] == "HGDE_KT"


@pytest.mark.asyncio
async def test_find_concept_for_variable_includes_metadata():
    with patch(
        "helpers.i14y_api_client.I14YApiClient.get_all_pages", new_callable=AsyncMock
    ) as mock_pages:
        mock_pages.return_value = MOCK_CONCEPTS
        from mcp.server.fastmcp import FastMCP
        from tools.search import register

        mcp = FastMCP("test")
        register(mcp)
        tool = next(
            t for t in mcp._tool_manager.list_tools() if t.name == "find_concept_for_variable"
        )
        result = await tool.fn(variable_name="Canton")

    parsed = json.loads(result)
    candidate = parsed["candidates"][0]
    assert candidate["conceptType"] == "CodeList"
    assert candidate["codeListEntryValueType"] == "Numeric"
    assert candidate["registrationStatus"] == "Recorded"
    assert candidate["version"] == "1.0.0"
