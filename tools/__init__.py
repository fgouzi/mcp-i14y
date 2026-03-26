"""Tool registration for mcp-i14y."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

__all__ = ["register_tools"]


def register_tools(mcp: FastMCP) -> None:
    """Register all I14Y MCP tools with the server."""
    from tools.agents import register as register_agents
    from tools.distributions import register as register_distributions
    from tools.catalogs import register as register_catalogs
    from tools.concepts import register as register_concepts
    from tools.datasets import register as register_datasets
    from tools.dataservices import register as register_dataservices
    from tools.mappingtables import register as register_mappingtables
    from tools.publicservices import register as register_publicservices
    from tools.search import register as register_search
    from tools.vocabularies import register as register_vocabularies

    register_datasets(mcp)
    register_dataservices(mcp)
    register_concepts(mcp)
    register_publicservices(mcp)
    register_catalogs(mcp)
    register_mappingtables(mcp)
    register_search(mcp)
    register_agents(mcp)
    register_vocabularies(mcp)
    register_distributions(mcp)
