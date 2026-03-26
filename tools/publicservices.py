"""MCP tools for I14Y PublicServices."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from helpers.core_api_client import CoreApiClient
from helpers.i14y_api_client import I14YApiClient

__all__ = ["register"]


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_publicservices(
        publisher_identifier: str | None = None,
        registration_status: str | None = None,
        publication_level: str | None = None,
        access_rights: str | None = None,
        publicservice_identifier: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> str:
        """List public services registered on the Swiss I14Y platform.

        Public services are administrative services offered by Swiss federal,
        cantonal, or communal bodies to citizens, businesses, or other organisations.

        Args:
            publisher_identifier: Filter by the publishing organisation's identifier.
            registration_status: One of Initial, Candidate, Recorded, Qualified,
                Standard, PreferredStandard, Superseded, Retired.
            publication_level: "Internal" or "Public".
            access_rights: Filter by access restriction code.
            publicservice_identifier: Filter by the public service's own identifier.
            page: Page number (starts at 1).
            page_size: Number of results per page (default 25).

        Returns:
            JSON string with paginated public service results.
        """
        async with I14YApiClient() as client:
            return await client.get(
                "/publicservices",
                publisherIdentifier=publisher_identifier,
                registrationStatus=registration_status,
                publicationLevel=publication_level,
                accessRights=access_rights,
                publicserviceIdentifier=publicservice_identifier,
                page=page,
                pageSize=page_size,
            )

    @mcp.tool()
    async def get_publicservice(publicservice_id: str) -> str:
        """Get detailed metadata for a specific public service by its ID.

        Args:
            publicservice_id: The unique identifier of the public service.

        Returns:
            JSON string with full public service metadata.
        """
        async with I14YApiClient() as client:
            return await client.get(f"/publicservices/{publicservice_id}")

    @mcp.tool()
    async def get_publicservice_by_identifier(identifier: str) -> str:
        """Get a public service by its human-readable identifier (not UUID).

        Args:
            identifier: The public service identifier string.

        Returns:
            JSON object with full public service metadata.
        """
        async with CoreApiClient() as client:
            return await client.get(f"/PublicServices/by-identifier/{identifier}")

    @mcp.tool()
    async def get_publicservice_relations(publicservice_id: str) -> str:
        """Get public services related to a given public service.

        Returns other public services that are semantically linked to this one
        (e.g. prerequisite services, related administrative procedures).

        Args:
            publicservice_id: The unique identifier (UUID) of the public service.

        Returns:
            JSON array of related public services.
        """
        async with CoreApiClient() as client:
            return await client.get(f"/PublicServices/{publicservice_id}/relations")
