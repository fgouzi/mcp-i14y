"""mcp-i14y — MCP server for the Swiss I14Y Interoperability Platform."""

from __future__ import annotations

import logging
import os

import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from helpers.env_config import get_server_host, get_server_port
from tools import register_tools

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Sentry (optional) ─────────────────────────────────────────────────────────
_sentry_dsn = os.getenv("SENTRY_DSN")
if _sentry_dsn:
    import sentry_sdk

    sentry_sdk.init(
        dsn=_sentry_dsn,
        traces_sample_rate=float(os.getenv("SENTRY_SAMPLE_RATE", "0.1")),
    )
    logger.info("Sentry error tracking enabled.")

# ── MCP Server ─────────────────────────────────────────────────────────────────
mcp = FastMCP(
    "mcp-i14y",
    instructions=(
        "You are connected to the Swiss I14Y Interoperability Platform. "
        "Use the available tools to list and retrieve datasets, data services, "
        "concepts (codelists), public services, and catalogs published by Swiss "
        "federal and cantonal bodies. All data is returned in the language(s) "
        "available on the platform (DE, FR, IT, EN)."
    ),
)
register_tools(mcp)


# ── Health endpoint ────────────────────────────────────────────────────────────
async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "platform": "i14y", "version": "0.1.0"})


# ── ASGI app ───────────────────────────────────────────────────────────────────
_mcp_app = mcp.streamable_http_app()

# Mount the health route alongside the MCP app
from starlette.applications import Starlette

app = Starlette(
    routes=[
        Route("/health", health),
    ]
)

# Mount MCP app at root so /mcp path is preserved (Starlette strips mount prefix)
app.mount("/", _mcp_app)

# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    host = get_server_host()
    port = get_server_port()
    logger.info("Starting mcp-i14y on %s:%d", host, port)
    uvicorn.run(app, host=host, port=port)
