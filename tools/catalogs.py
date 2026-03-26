"""MCP tools for I14Y Catalogs (DCAT-AP exports)."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from helpers.core_api_client import CoreApiClient
from helpers.i14y_api_client import I14YApiClient

__all__ = ["register"]


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_catalog(
        catalog_id: str,
        format: str = "ttl",
    ) -> str:
        """Export a catalog from the Swiss I14Y platform in DCAT-AP format.

        Catalogs aggregate datasets, data services, and other resources published
        by an organisation. The export is DCAT-AP (EU Application Profile for
        Data Catalogs) compliant.

        Args:
            catalog_id: The unique identifier of the catalog.
            format: Export format — "ttl" (Turtle, default) or "rdf" (RDF/XML).

        Returns:
            Catalog data as Turtle or RDF/XML text.
        """
        valid = {"ttl", "rdf"}
        if format not in valid:
            return f'{{"error": "Invalid format \'{format}\'. Valid values: ttl, rdf"}}'
        async with I14YApiClient() as client:
            return await client.get(f"/catalogs/{catalog_id}/dcat/exports/{format}")

    @mcp.tool()
    async def list_catalogs(
        page: int = 1,
        page_size: int = 25,
    ) -> str:
        """List all DCAT catalogs registered on the I14Y platform.

        A catalog aggregates datasets, data services, and other resources
        published by an organisation. Use this to discover available catalogs
        before exporting one with get_catalog().

        Args:
            page: Page number (starts at 1).
            page_size: Results per page (default 25).

        Returns:
            JSON object with paginated catalog list.
        """
        async with CoreApiClient() as client:
            return await client.get("/DcatCatalogs", page=page, pageSize=page_size)

    @mcp.tool()
    async def get_catalog_records(
        catalog_id: str,
        page: int = 1,
        page_size: int = 25,
    ) -> str:
        """Get all catalog records (resource entries) from a specific DCAT catalog.

        Catalog records link a catalog to the datasets and data services it contains,
        with provenance metadata (when the record was added, modified, etc.).

        Args:
            catalog_id: The unique identifier (UUID) of the catalog.
            page: Page number (starts at 1).
            page_size: Results per page (default 25).

        Returns:
            JSON object with paginated catalog records.
        """
        async with CoreApiClient() as client:
            return await client.get(
                f"/DcatCatalogs/{catalog_id}/records",
                page=page,
                pageSize=page_size,
            )

    @mcp.tool()
    async def get_catalog_themes(
        catalog_id: str,
        page: int = 1,
        page_size: int = 100,
    ) -> str:
        """Get all themes used within a specific DCAT catalog.

        Returns the controlled vocabulary themes (from the EU Data Theme vocabulary)
        assigned to resources in this catalog. Useful for understanding the thematic
        coverage of a catalog and for RDF/DCAT alignment.

        Args:
            catalog_id: The unique identifier (UUID) of the catalog.
            page: Page number (starts at 1).
            page_size: Results per page (default 100).

        Returns:
            JSON object with themes used in the catalog.
        """
        async with CoreApiClient() as client:
            return await client.get(
                f"/DcatCatalogs/{catalog_id}/themes",
                page=page,
                pageSize=page_size,
            )
