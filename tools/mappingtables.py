"""MCP tools for I14Y MappingTables.

A MappingTable defines a correspondence between two codelists (source → target),
allowing semantic alignment across different classification systems. For example,
mapping old canton codes to new ones, or aligning a Swiss codelist to a European standard.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from helpers.i14y_api_client import I14YApiClient

__all__ = ["register"]


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_mappingtables(
        publisher_identifier: str | None = None,
        mappingtable_identifier: str | None = None,
        version: str | None = None,
        registration_status: str | None = None,
        publication_level: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> str:
        """List mapping tables registered on the Swiss I14Y platform.

        A mapping table defines a correspondence between two codelists (source → target),
        enabling semantic alignment across different classification systems. For example,
        mapping Swiss canton codes to NUTS regional codes, or aligning one version of
        a codelist to another.

        Args:
            publisher_identifier: Filter by the publishing organisation's identifier.
            mappingtable_identifier: Filter by the mapping table's own identifier.
            version: Filter by version string.
            registration_status: One of Initial, Candidate, Recorded, Qualified,
                Standard, PreferredStandard, Superseded, Retired.
            publication_level: "Internal" or "Public".
            page: Page number (starts at 1).
            page_size: Number of results per page (default 25).

        Returns:
            JSON string with paginated mapping table results including name, description,
            source and target codelist URIs, publisher, and registration status.
        """
        async with I14YApiClient() as client:
            return await client.get(
                "/mappingtables",
                publisherIdentifier=publisher_identifier,
                mappingTableIdentifier=mappingtable_identifier,
                version=version,
                registrationStatus=registration_status,
                publicationLevel=publication_level,
                page=page,
                pageSize=page_size,
            )

    @mcp.tool()
    async def get_mappingtable(mappingtable_id: str) -> str:
        """Get detailed metadata for a specific mapping table by its ID.

        Returns the full mapping table record including its name, description, version,
        publisher, source codelist URI, target codelist URI, registration status,
        validity period, and responsible persons.

        Args:
            mappingtable_id: The unique identifier (UUID) of the mapping table.

        Returns:
            JSON string with full mapping table metadata.
        """
        async with I14YApiClient() as client:
            return await client.get(f"/mappingtables/{mappingtable_id}")

    @mcp.tool()
    async def get_mappingtable_relations(
        mappingtable_id: str,
        format: str = "Json",
    ) -> str:
        """Export all mapping relations (value correspondences) for a mapping table.

        Each relation pairs a value from the source codelist with its equivalent
        in the target codelist. Use this to retrieve the complete mapping, e.g.
        all old code → new code pairs.

        Args:
            mappingtable_id: The unique identifier (UUID) of the mapping table.
            format: Export format — "Json" (default) or "Csv".

        Returns:
            Mapping relations as a JSON array or CSV text.
        """
        valid = {"Json", "Csv"}
        if format not in valid:
            return f'{{"error": "Invalid format \'{format}\'. Valid values: Json, Csv"}}'
        async with I14YApiClient() as client:
            return await client.get(
                f"/mappingtables/{mappingtable_id}/relations/exports/{format}"
            )
