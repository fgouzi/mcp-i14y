# CLAUDE.md — mcp-i14y

This file provides context and conventions for Claude (and other LLM coding assistants) working on this repository.

## Project Overview

`mcp-i14y` is a **Model Context Protocol (MCP) server** that bridges LLMs (Claude, Gemini, GitHub Copilot, etc.) to the **Swiss I14Y Interoperability Platform** (`https://www.i14y.admin.ch`). It exposes I14Y's Public API as callable MCP tools, enabling conversational queries over Swiss government metadata.

Inspired by the French [`datagouv-mcp`](https://github.com/datagouv/datagouv-mcp) project, adapted for I14Y's unique resource model (Concepts, PublicServices, Catalogs).

---

## Directory Structure

```
mcp-i14y/
├── main.py                   # FastMCP server + health endpoint + Starlette app
├── tools/
│   ├── __init__.py           # register_tools() — single entry point
│   ├── datasets.py           # list_datasets, get_dataset, get_dataset_structure
│   ├── dataservices.py       # list_dataservices, get_dataservice
│   ├── concepts.py           # list_concepts, get_concept, get_concept_codelist
│   ├── publicservices.py     # list_publicservices, get_publicservice
│   └── catalogs.py           # get_catalog
├── helpers/
│   ├── env_config.py         # API base URL + server host/port from env vars
│   └── i14y_api_client.py    # Async httpx client (context manager)
├── tests/
│   ├── test_i14y_api_client.py
│   ├── test_datasets.py
│   ├── test_concepts.py
│   ├── test_dataservices.py
│   ├── test_publicservices.py
│   └── test_health.py
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

---

## Development Commands

```bash
# Install all dependencies (including dev)
uv sync

# Run the server locally
uv run python main.py

# Run unit tests
uv run pytest

# Run only integration tests (requires live I14Y API)
uv run pytest -m integration

# Lint + format
uv run ruff check --fix .
uv run ruff format .

# Install pre-commit hooks
uv run pre-commit install
```

---

## I14Y API Reference

| Environment | Base URL |
|---|---|
| Production | `https://api.i14y.admin.ch/api/public/v1` |
| Test | `https://api-a.i14y.admin.ch/api/public/v1` |

**Authentication:** None (public API). Fair-use policy applies.

**Swagger docs:** `https://apiconsole.i14y.admin.ch/public/v1/index.html`

### Common filter parameters

All list endpoints accept:
- `publisherIdentifier` — filter by organisation identifier
- `registrationStatus` — `Initial | Candidate | Recorded | Qualified | Standard | PreferredStandard | Superseded | Retired`
- `publicationLevel` — `Internal | Public`
- `accessRights` — access restriction code
- `page` — page number (default 1)
- `pageSize` — results per page (default 25)

### Response language

I14Y returns multilingual fields as objects: `{"de": "...", "fr": "...", "it": "...", "en": "..."}`. Tools return these as-is; the LLM picks the appropriate language from context.

---

## Code Conventions

1. **Async everywhere** — all tool functions and HTTP calls are `async`.
2. **Tools return strings** — MCP tool functions must return `str`. Always return JSON-serialised strings (or raw text for RDF/TTL/CSV).
3. **Strip None params** — `_build_params()` in `i14y_api_client.py` removes `None` values before sending to the API.
4. **Friendly error messages** — HTTP errors are caught and returned as `{"error": "..."}` JSON strings, never raised as exceptions.
5. **Context manager for HTTP** — always use `async with I14YApiClient() as client:`.
6. **No global state** — each tool invocation creates a fresh client session.

---

## Adding a New Tool

1. **Create or edit** the relevant tool file in `tools/` (or create a new one).
2. **Define** an `async def` function decorated with `@mcp.tool()` inside the `register(mcp)` function.
3. **Register** it: add `from tools.yourmodule import register as register_yourmodule` and call it in `tools/__init__.py`.
4. **Add tests** in `tests/test_yourmodule.py` using mocked `I14YApiClient.get`.
5. **Document** the tool in `README.md` (Available Tools table).

### Minimal example

```python
# tools/myresource.py
from helpers.i14y_api_client import I14YApiClient

def register(mcp):
    @mcp.tool()
    async def get_myresource(resource_id: str) -> str:
        """Get a specific resource by ID."""
        async with I14YApiClient() as client:
            return await client.get(f"/myresources/{resource_id}")
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MCP_HOST` | `0.0.0.0` | Server bind address |
| `MCP_PORT` | `8000` | Server port |
| `I14Y_API_ENV` | `prod` | API environment: `prod` or `test` |
| `LOG_LEVEL` | `INFO` | Python logging level |
| `SENTRY_DSN` | _(empty)_ | Sentry DSN for error tracking |
| `SENTRY_SAMPLE_RATE` | `0.1` | Sentry traces sample rate (0.0–1.0) |

---

## Testing Notes

- Unit tests mock `I14YApiClient.get` — they never hit the real API.
- Integration tests (marked `@pytest.mark.integration`) hit the real test API at `https://api-a.i14y.admin.ch`.
- Do not add `uv.lock` to `.gitignore` — it should be committed for reproducible builds.
