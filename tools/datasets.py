"""MCP tools for I14Y Datasets."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from helpers.core_api_client import CoreApiClient
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

    @mcp.tool()
    async def get_dataset_by_identifier(identifier: str) -> str:
        """Get a dataset by its human-readable identifier (not UUID).

        Use this when you know the dataset's short identifier (e.g. "px-x-0602010000_109")
        rather than its UUID. More convenient than list_datasets() with a filter.

        Args:
            identifier: The dataset identifier string.

        Returns:
            JSON object with full dataset metadata.
        """
        async with CoreApiClient() as client:
            return await client.get(f"/Datasets/by-identifier/{identifier}")

    @mcp.tool()
    async def check_dataset_has_structure(dataset_id: str) -> str:
        """Check whether a dataset has a structural model defined on I14Y.

        Use this before calling get_dataset_structure() to avoid errors on
        datasets with no model. Useful for filtering a list of datasets to
        only those with documented schemas.

        Args:
            dataset_id: The unique identifier (UUID) of the dataset.

        Returns:
            JSON boolean — true if a structure model exists, false otherwise.
        """
        async with CoreApiClient() as client:
            return await client.get(f"/Datasets/{dataset_id}/model/exists")

    @mcp.tool()
    async def get_dataset_model_graph(dataset_id: str) -> str:
        """Get the structural model of a dataset as a schema graph.

        Returns the dataset schema in schemaGraph format — a JSON representation
        of the model as a graph of nodes and edges, suitable for programmatic
        processing and visualisation. Complements get_dataset_structure() which
        returns RDF/JSON-LD formats.

        Only works for datasets that have a structure (use check_dataset_has_structure()
        to verify first).

        Args:
            dataset_id: The unique identifier (UUID) of the dataset.

        Returns:
            JSON object representing the dataset schema as a graph.
        """
        async with CoreApiClient() as client:
            return await client.get(f"/Datasets/{dataset_id}/model/graph")
