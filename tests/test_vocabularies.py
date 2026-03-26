"""Unit tests for vocabulary tools."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest


MOCK_VOCAB_CONFIGS = json.dumps([
    {
        "id": "936fb77f-0ed4-499e-b43d-65c39318fa38",
        "conceptIdentifier": "DV_DCAT_DATASET_THEME",
        "conceptVersion": "1.1.0",
        "vocabularyIdentifier": "Concept_DATASET_THEME",
    },
    {
        "id": "8d8598b5-bee9-4005-a33f-b2ad4cdf2740",
        "conceptIdentifier": "CL_DCAT_ACCESS_RIGHT",
        "conceptVersion": "1.0.0",
        "vocabularyIdentifier": "RightsStatement_ACCESS_RIGHTS",
    },
])

MOCK_VOCAB_ENTRIES = json.dumps({
    "identifier": "Concept_DATASET_THEME",
    "entries": [
        {
            "code": "AGRI",
            "uri": "http://publications.europa.eu/resource/authority/data-theme/AGRI",
            "label": {"de": "Landwirtschaft", "fr": "Agriculture", "en": "Agriculture"},
        },
        {
            "code": "ECON",
            "uri": "http://publications.europa.eu/resource/authority/data-theme/ECON",
            "label": {"de": "Wirtschaft", "fr": "Économie", "en": "Economy"},
        },
    ],
})


@pytest.mark.asyncio
async def test_list_vocabularies():
    with patch("helpers.core_api_client.CoreApiClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = MOCK_VOCAB_CONFIGS
        from mcp.server.fastmcp import FastMCP
        from tools.vocabularies import register

        mcp = FastMCP("test")
        register(mcp)
        tool = next(t for t in mcp._tool_manager.list_tools() if t.name == "list_vocabularies")
        result = await tool.fn()

    parsed = json.loads(result)
    assert len(parsed) == 2
    assert parsed[0]["vocabularyIdentifier"] == "Concept_DATASET_THEME"


@pytest.mark.asyncio
async def test_get_vocabulary():
    with patch("helpers.core_api_client.CoreApiClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = MOCK_VOCAB_ENTRIES
        from mcp.server.fastmcp import FastMCP
        from tools.vocabularies import register

        mcp = FastMCP("test")
        register(mcp)
        tool = next(t for t in mcp._tool_manager.list_tools() if t.name == "get_vocabulary")
        result = await tool.fn(identifier="Concept_DATASET_THEME")

    parsed = json.loads(result)
    assert parsed["identifier"] == "Concept_DATASET_THEME"
    assert parsed["entries"][0]["code"] == "AGRI"
