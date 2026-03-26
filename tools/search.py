"""MCP tools for keyword-based search across I14Y resources.

The I14Y Public API has no full-text search endpoint. These tools implement
client-side keyword matching across all pages of the list endpoints, providing
a search experience that the base list_* tools cannot offer.
"""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from helpers.i14y_api_client import I14YApiClient

__all__ = ["register"]

_MAX_SCAN = 500  # upper limit on items fetched per search call


def _multilingual_values(obj: dict, *fields: str) -> list[str]:
    """Collect all non-empty string values from multilingual dict fields."""
    values: list[str] = []
    for field in fields:
        val = obj.get(field)
        if isinstance(val, dict):
            values.extend(v for v in val.values() if v)
        elif isinstance(val, str) and val:
            values.append(val)
    return values


def _score(item: dict, keyword: str) -> float:
    """Return a relevance score (higher is better) for an item vs. a keyword.

    Scoring rules:
    - Exact word match in title/name    → 2.0 per language hit
    - Substring match in title/name     → 1.0 per language hit
    - Match in description              → 0.5 per language hit
    - Match in identifier               → 2.0
    """
    kw = keyword.lower()
    score = 0.0

    for val in _multilingual_values(item, "title", "name"):
        v = val.lower()
        if kw == v:
            score += 3.0
        elif f" {kw} " in f" {v} ":
            score += 2.0
        elif kw in v:
            score += 1.0

    for val in _multilingual_values(item, "description"):
        if kw in val.lower():
            score += 0.5

    identifier = item.get("identifier", "")
    if isinstance(identifier, str) and kw in identifier.lower():
        score += 2.0

    return score


def _search_items(items: list[dict], keywords: list[str], max_results: int) -> list[dict]:
    """Score and rank items against all keywords, return top matches."""
    scored: list[tuple[float, dict]] = []
    for item in items:
        total = sum(_score(item, kw) for kw in keywords)
        if total > 0:
            scored.append((total, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:max_results]]


def _summary(item: dict, resource_type: str) -> dict:
    """Build a compact summary dict for a matched resource."""
    result: dict = {
        "id": item.get("id"),
        "identifier": item.get("identifier"),
        "type": resource_type,
    }
    for field in ("title", "name"):
        if item.get(field):
            result[field] = item[field]
            break
    if item.get("description"):
        result["description"] = item["description"]
    if item.get("registrationStatus"):
        result["registrationStatus"] = item["registrationStatus"]
    if item.get("publisher") and isinstance(item["publisher"], dict):
        result["publisher"] = item["publisher"].get("identifier") or item["publisher"].get("name")
    return result


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def search_datasets(
        keyword: str,
        publisher_identifier: str | None = None,
        max_results: int = 10,
    ) -> str:
        """Search datasets by keyword across titles and descriptions (all languages).

        Since the I14Y API has no full-text search endpoint, this tool fetches up
        to 500 datasets progressively and filters them client-side. Returns the
        top matches ranked by relevance.

        Use this instead of list_datasets() when you know a title or subject
        but not the exact identifier.

        Args:
            keyword: Search term(s) — space-separated words are each scored independently.
            publisher_identifier: Optionally restrict to a single publisher (e.g. "CH1" for OFS/BFS).
            max_results: Maximum number of results to return (default 10).

        Returns:
            JSON string with ranked dataset matches including id, title, publisher.
        """
        keywords = [w for w in keyword.lower().split() if w]
        async with I14YApiClient() as client:
            items = await client.get_all_pages(
                "/datasets",
                max_items=_MAX_SCAN,
                publisherIdentifier=publisher_identifier,
            )
        matches = _search_items(items, keywords, max_results)
        return json.dumps(
            {"keyword": keyword, "total_scanned": len(items), "matches": [_summary(m, "dataset") for m in matches]},
            ensure_ascii=False,
            indent=2,
        )

    @mcp.tool()
    async def search_concepts(
        keyword: str,
        publisher_identifier: str | None = None,
        max_results: int = 10,
    ) -> str:
        """Search concepts (codelists, data dictionaries) by keyword.

        Since the I14Y API has no full-text search endpoint, this tool fetches up
        to 500 concepts progressively and filters them client-side. Returns the
        top matches ranked by relevance.

        Use this instead of list_concepts() when you want to find a codelist
        by subject (e.g. "canton", "pays", "secteur").

        Args:
            keyword: Search term(s) — space-separated words are each scored independently.
            publisher_identifier: Optionally restrict to a single publisher (e.g. "CH1" for OFS/BFS).
            max_results: Maximum number of results to return (default 10).

        Returns:
            JSON string with ranked concept matches including id, name, identifier.
        """
        keywords = [w for w in keyword.lower().split() if w]
        async with I14YApiClient() as client:
            items = await client.get_all_pages(
                "/concepts",
                max_items=_MAX_SCAN,
                publisherIdentifier=publisher_identifier,
            )
        matches = _search_items(items, keywords, max_results)
        return json.dumps(
            {"keyword": keyword, "total_scanned": len(items), "matches": [_summary(m, "concept") for m in matches]},
            ensure_ascii=False,
            indent=2,
        )

    @mcp.tool()
    async def find_concept_for_variable(
        variable_name: str,
        publisher_identifier: str | None = None,
    ) -> str:
        """Find I14Y concepts (codelists) that could match a dataset variable name.

        Given a variable name extracted from get_dataset_structure() — such as
        "Canton", "Année", "Secteur économique", "Classe de taille" — this tool
        searches the I14Y concept catalog for codelists that semantically match
        the variable.

        Typical workflow:
            1. get_dataset_structure(dataset_id)  → identify variable names
            2. find_concept_for_variable("Canton") → get candidate concepts
            3. get_concept(concept_id, include_codelist_entries=True) → inspect entries

        Args:
            variable_name: The variable name to look up (any language).
            publisher_identifier: Optionally restrict to a single publisher (e.g. "CH1" for OFS/BFS).

        Returns:
            JSON string with ranked concept candidates including id, name, identifier,
            and entry count metadata.
        """
        keywords = [w for w in variable_name.lower().split() if w]
        async with I14YApiClient() as client:
            items = await client.get_all_pages(
                "/concepts",
                max_items=_MAX_SCAN,
                publisherIdentifier=publisher_identifier,
            )
        matches = _search_items(items, keywords, max_results=5)

        candidates = []
        for m in matches:
            summary = _summary(m, "concept")
            summary["conceptType"] = m.get("conceptType")
            summary["codeListEntryValueType"] = m.get("codeListEntryValueType")
            summary["registrationStatus"] = m.get("registrationStatus")
            summary["version"] = m.get("version")
            candidates.append(summary)

        return json.dumps(
            {
                "variable_name": variable_name,
                "total_scanned": len(items),
                "candidates": candidates,
                "tip": (
                    "Use get_concept(concept_id, include_codelist_entries=True) "
                    "to inspect the entries of the best candidate."
                ),
            },
            ensure_ascii=False,
            indent=2,
        )
