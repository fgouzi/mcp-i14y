"""MCP tools for I14Y DataServices."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from helpers.core_api_client import CoreApiClient
from helpers.i14y_api_client import I14YApiClient

__all__ = ["register"]


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_dataservices(
        publisher_identifier: str | None = None,
        registration_status: str | None = None,
        publication_level: str | None = None,
        access_rights: str | None = None,
        dataservice_identifier: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> str:
        """List data services (APIs) registered on the Swiss I14Y platform.

        Data services are electronic interfaces (APIs) that provide access to
        datasets or functionality published by Swiss federal and cantonal bodies.

        Args:
            publisher_identifier: Filter by the publishing organisation's identifier.
            registration_status: One of Initial, Candidate, Recorded, Qualified,
                Standard, PreferredStandard, Superseded, Retired.
            publication_level: "Internal" or "Public".
            access_rights: Filter by access restriction code.
            dataservice_identifier: Filter by the data service's own identifier.
            page: Page number (starts at 1).
            page_size: Number of results per page (default 25).

        Returns:
            JSON string with paginated data service results.
        """
        async with I14YApiClient() as client:
            return await client.get(
                "/dataservices",
                publisherIdentifier=publisher_identifier,
                registrationStatus=registration_status,
                publicationLevel=publication_level,
                accessRights=access_rights,
                dataserviceIdentifier=dataservice_identifier,
                page=page,
                pageSize=page_size,
            )

    @mcp.tool()
    async def get_dataservice(dataservice_id: str) -> str:
        """Get detailed metadata for a specific data service by its ID.

        Args:
            dataservice_id: The unique identifier of the data service.

        Returns:
            JSON string with full data service metadata (title, description,
            endpoint URL, publisher, themes, etc.).
        """
        async with I14YApiClient() as client:
            return await client.get(f"/dataservices/{dataservice_id}")

    @mcp.tool()
    async def get_dataservice_by_identifier(identifier: str) -> str:
        """Get a data service by its human-readable identifier (not UUID).

        Args:
            identifier: The data service identifier string.

        Returns:
            JSON object with full data service metadata.
        """
        async with CoreApiClient() as client:
            return await client.get(f"/DataServices/by-identifier/{identifier}")
