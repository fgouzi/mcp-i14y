"""MCP tools for I14Y Datasets."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from helpers.i14y_api_client import I14YApiClient

__all__ = ["register"]


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_datasets(
        publisher_identifier: str | None = None,
        registration_status: str | None = None,
        publication_level: str | None = None,
        access_rights: str | None = None,
        dataset_identifier: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> str:
        """List datasets from the Swiss I14Y interoperability platform.

        Supports filtering by publisher, registration status, publication level,
        access rights, or a specific dataset identifier.

        Args:
            publisher_identifier: Filter by the publishing organisation's identifier.
            registration_status: One of Initial, Candidate, Recorded, Qualified,
                Standard, PreferredStandard, Superseded, Retired.
            publication_level: "Internal" or "Public".
            access_rights: Filter by access restriction code.
            dataset_identifier: Filter by the dataset's own identifier.
            page: Page number (starts at 1).
            page_size: Number of results per page (default 25).

        Returns:
            JSON string with paginated dataset results.
        """
        async with I14YApiClient() as client:
            return await client.get(
                "/datasets",
                publisherIdentifier=publisher_identifier,
                registrationStatus=registration_status,
                publicationLevel=publication_level,
                accessRights=access_rights,
                datasetIdentifier=dataset_identifier,
                page=page,
                pageSize=page_size,
            )

    @mcp.tool()
    async def get_dataset(dataset_id: str) -> str:
        """Get detailed metadata for a specific dataset by its ID.

        Args:
            dataset_id: The unique identifier of the dataset.

        Returns:
            JSON string with full dataset metadata (title, description,
            publisher, themes, distributions, etc.).
        """
        async with I14YApiClient() as client:
            return await client.get(f"/datasets/{dataset_id}")

    @mcp.tool()
    async def get_dataset_structure(
        dataset_id: str,
        format: str = "JsonLd",
    ) -> str:
        """Export the structural schema of a dataset.

        Args:
            dataset_id: The unique identifier of the dataset.
            format: Export format — "JsonLd" (default), "Ttl" (Turtle), or "Rdf" (RDF/XML).

        Returns:
            Dataset structure in the requested format.
        """
        valid = {"JsonLd", "Ttl", "Rdf"}
        if format not in valid:
            return f'{{"error": "Invalid format \'{format}\'. Valid values: {sorted(valid)}"}}'
        async with I14YApiClient() as client:
            return await client.get(f"/datasets/{dataset_id}/structures/exports/{format}")
