"""MCP tools for I14Y Concepts (codelists, data dictionaries)."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from helpers.i14y_api_client import I14YApiClient

__all__ = ["register"]


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_concepts(
        publisher_identifier: str | None = None,
        concept_identifier: str | None = None,
        version: str | None = None,
        registration_status: str | None = None,
        publication_level: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> str:
        """List data concepts (codelists, data dictionaries) on the Swiss I14Y platform.

        Concepts are reusable data definitions that ensure semantic interoperability
        across Swiss government systems. They include codelists (e.g. country codes,
        canton codes), date formats, numeric ranges, and string patterns.

        Args:
            publisher_identifier: Filter by the publishing organisation's identifier.
            concept_identifier: Filter by the concept's own identifier.
            version: Filter by concept version string.
            registration_status: One of Initial, Candidate, Recorded, Qualified,
                Standard, PreferredStandard, Superseded, Retired.
            publication_level: "Internal" or "Public".
            page: Page number (starts at 1).
            page_size: Number of results per page (default 25).

        Returns:
            JSON string with paginated concept results.
        """
        async with I14YApiClient() as client:
            return await client.get(
                "/concepts",
                publisherIdentifier=publisher_identifier,
                conceptIdentifier=concept_identifier,
                version=version,
                registrationStatus=registration_status,
                publicationLevel=publication_level,
                page=page,
                pageSize=page_size,
            )

    @mcp.tool()
    async def get_concept(
        concept_id: str,
        include_codelist_entries: bool = False,
    ) -> str:
        """Get detailed metadata for a specific data concept.

        Args:
            concept_id: The unique identifier of the concept.
            include_codelist_entries: If True, embed all codelist entries in the response.
                Use get_concept_codelist for large codelists to avoid oversized responses.

        Returns:
            JSON string with concept metadata and optionally its codelist entries.
        """
        async with I14YApiClient() as client:
            return await client.get(
                f"/concepts/{concept_id}",
                includeCodeListEntries=str(include_codelist_entries).lower(),
            )

    @mcp.tool()
    async def get_concept_codelist(
        concept_id: str,
        format: str = "json",
    ) -> str:
        """Export all codelist entries for a concept.

        Use this tool to retrieve the full set of valid values defined by a codelist
        concept (e.g. all canton codes, all country codes).

        Args:
            concept_id: The unique identifier of the concept.
            format: Export format — "json" (default) or "csv".

        Returns:
            Codelist entries as a JSON array or CSV text.
        """
        valid = {"json", "csv"}
        if format not in valid:
            return f'{{"error": "Invalid format \'{format}\'. Valid values: json, csv"}}'
        async with I14YApiClient() as client:
            return await client.get(
                f"/concepts/{concept_id}/codelist-entries/exports/{format}"
            )
