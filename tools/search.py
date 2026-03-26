"""MCP tools for full-text search across I14Y resources (via CORE API)."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from helpers.core_api_client import CoreApiClient

__all__ = ["register"]

_VALID_TYPES = {"Dataset", "DataService", "PublicService", "Concept", "MappingTable"}


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def catalog_search(
        query: str,
        types: list[str] | None = None,
        publishers: list[str] | None = None,
        statuses: list[str] | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> str:
        """Search across all I14Y resources using full-text search (server-side).

        Searches datasets, concepts, data services, public services, and mapping
        tables in a single call. Results are ranked by the I14Y CORE search engine.

        This replaces manual pagination + client-side filtering — use this tool
        whenever you need to find a resource by name, subject, or keyword.

        Args:
            query: Free-text search query (any language).
            types: Filter by resource type(s). Valid values:
                "Dataset", "DataService", "PublicService", "Concept", "MappingTable".
                Omit to search all types.
            publishers: Filter by publisher identifier(s), e.g. ["CH1"] for OFS/BFS.
            statuses: Filter by registration status(es), e.g. ["Recorded", "Standard"].
            page: Page number (starts at 1).
            page_size: Results per page (default 25).

        Returns:
            JSON array of matching resources, each with id, identifier, type,
            title/name, description, publisher, and registrationStatus.
        """
        if types:
            invalid = [t for t in types if t not in _VALID_TYPES]
            if invalid:
                return (
                    f'{{"error": "Invalid type(s): {invalid}. '
                    f'Valid values: {sorted(_VALID_TYPES)}"}}'
                )
        async with CoreApiClient() as client:
            return await client.get(
                "/Catalog/search",
                query=query,
                types=types,
                publishers=publishers,
                statuses=statuses,
                page=page,
                pageSize=page_size,
            )
