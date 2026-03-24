"""MCP tools for I14Y Catalogs (DCAT-AP exports)."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

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
