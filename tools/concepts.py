"""MCP tools for I14Y Concepts (codelists, data dictionaries)."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from helpers.core_api_client import CoreApiClient
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

    @mcp.tool()
    async def get_concept_by_identifier(identifier: str) -> str:
        """Get concept(s) by their human-readable identifier (e.g. "HGDE_KT").

        Unlike get_concept() which requires a UUID, this tool accepts the
        short identifier string visible in the I14Y platform and URLs.
        Returns all versions of the concept with that identifier.

        Args:
            identifier: The concept identifier string (e.g. "HGDE_KT", "CL_NOGA").

        Returns:
            JSON array of concepts matching the identifier, with full metadata.
        """
        async with CoreApiClient() as client:
            return await client.get(f"/Concepts/identifier/{identifier}")

    @mcp.tool()
    async def get_codelist_entries(
        concept_id: str,
        page: int = 1,
        page_size: int = 100,
    ) -> str:
        """Get paginated codelist entries with full annotations for a concept.

        Returns richer data than get_concept_codelist() — includes annotations,
        descriptions, and hierarchical metadata for each entry. Suitable for
        browsing large codelists page by page.

        Args:
            concept_id: The unique identifier (UUID) of the concept.
            page: Page number (starts at 1).
            page_size: Results per page (default 100).

        Returns:
            JSON object with paginated codelist entries including code, label,
            description, and any annotations.
        """
        async with CoreApiClient() as client:
            return await client.get(
                f"/Concepts/{concept_id}/codelist-entries",
                page=page,
                pageSize=page_size,
            )

    @mcp.tool()
    async def get_codelist_entry_by_code(concept_id: str, code: str) -> str:
        """Get a single codelist entry by its code value.

        Use this to look up the label and metadata for a specific code,
        e.g. find what canton code "1" means in HGDE_KT.

        Args:
            concept_id: The unique identifier (UUID) of the concept.
            code: The code value to look up (e.g. "1", "CH", "A").

        Returns:
            JSON object with the matching codelist entry (code, label, description).
        """
        async with CoreApiClient() as client:
            return await client.get(
                f"/Concepts/{concept_id}/codelist-entries/by-code",
                code=code,
            )

    @mcp.tool()
    async def get_codelist_entries_children(
        concept_id: str,
        parent_code: str,
        page: int = 1,
        page_size: int = 100,
    ) -> str:
        """Get all child entries of a parent code in a hierarchical codelist.

        For codelists with a parent-child hierarchy (e.g. NUTS regions,
        Swiss commune/district/canton hierarchy), this returns all direct
        children of a given parent code.

        Args:
            concept_id: The unique identifier (UUID) of the concept.
            parent_code: The parent code whose children to retrieve.
            page: Page number (starts at 1).
            page_size: Results per page (default 100).

        Returns:
            JSON object with paginated child codelist entries.
        """
        async with CoreApiClient() as client:
            return await client.get(
                f"/Concepts/{concept_id}/codelist-entries/children-of",
                parentCode=parent_code,
                page=page,
                pageSize=page_size,
            )

    @mcp.tool()
    async def search_codelist_entries(
        concept_id: str,
        query: str,
        language: str = "fr",
        page: int = 1,
        page_size: int = 25,
    ) -> str:
        """Search for entries within a specific codelist by label or code.

        Use this to find specific codes within a large codelist without
        fetching all entries. For example, find the code for "Zurich" in
        the canton codelist, or search for a specific NOGA sector.

        Args:
            concept_id: The unique identifier (UUID) of the concept.
            query: Search term to match against entry labels or codes.
            language: Language for label matching — "fr", "de", "it", or "en" (default "fr").
            page: Page number (starts at 1).
            page_size: Results per page (default 25).

        Returns:
            JSON object with matching codelist entries ranked by relevance.
        """
        async with CoreApiClient() as client:
            return await client.get(
                f"/Concepts/{concept_id}/codelist-entries/search",
                language=language,
                query=query,
                page=page,
                pageSize=page_size,
            )
