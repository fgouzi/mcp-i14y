# Architecture — mcp-i14y

## Overview

`mcp-i14y` acts as a **protocol bridge** between LLM clients (Claude, Gemini, Copilot, etc.) and the Swiss I14Y Interoperability Platform API. It speaks the **Model Context Protocol (MCP)** on one side and the **I14Y REST API** on the other.

```
┌─────────────────────────────────────────────────────────┐
│  LLM Client (Claude Desktop / Claude Code / Copilot…)   │
└───────────────────┬─────────────────────────────────────┘
                    │  MCP (Streamable HTTP / JSON-RPC)
                    │  POST http://localhost:8000/mcp
                    ▼
┌─────────────────────────────────────────────────────────┐
│                      mcp-i14y                           │
│                                                         │
│  Starlette app                                          │
│  ├── GET  /health  → {"status":"ok"}                    │
│  └── /mcp          → FastMCP (Streamable HTTP)          │
│       ├── list_datasets          ──┐                    │
│       ├── get_dataset            ──┤                    │
│       ├── get_dataset_structure  ──┤                    │
│       ├── list_dataservices      ──┤                    │
│       ├── get_dataservice        ──┤  I14YApiClient     │
│       ├── list_concepts          ──┤  (httpx async)     │
│       ├── get_concept            ──┤                    │
│       ├── get_concept_codelist   ──┤                    │
│       ├── list_publicservices    ──┤                    │
│       ├── get_publicservice      ──┤                    │
│       └── get_catalog            ──┘                    │
└───────────────────┬─────────────────────────────────────┘
                    │  HTTPS REST
                    ▼
┌─────────────────────────────────────────────────────────┐
│         I14Y Public API                                 │
│   https://api.i14y.admin.ch/api/public/v1               │
│   (Swiss Federal Statistical Office)                    │
└─────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### `main.py` — Application entry point

- Initialises FastMCP with a `name` and LLM-facing `instructions` string.
- Calls `register_tools(mcp)` to attach all 11 tools.
- Wraps the MCP app (`mcp.streamable_http_app()`) inside a **Starlette** application, adding the `/health` route at the top level.
- Reads `MCP_HOST` / `MCP_PORT` from environment, starts `uvicorn`.
- Optionally initialises **Sentry** if `SENTRY_DSN` is set.

### `tools/` — MCP Tool Layer

Each module follows the same pattern:

```python
def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def tool_name(param: type) -> str:
        """Docstring shown to the LLM as the tool description."""
        async with I14YApiClient() as client:
            return await client.get("/endpoint", param=param)
```

`tools/__init__.py` exposes a single `register_tools(mcp)` function that imports and calls all five `register()` functions. This keeps `main.py` clean and makes it easy to add or remove modules.

| Module | Tools | I14Y Endpoints |
|---|---|---|
| `datasets.py` | `list_datasets`, `get_dataset`, `get_dataset_structure` | `GET /datasets`, `/datasets/{id}`, `/datasets/{id}/structures/exports/{fmt}` |
| `dataservices.py` | `list_dataservices`, `get_dataservice` | `GET /dataservices`, `/dataservices/{id}` |
| `concepts.py` | `list_concepts`, `get_concept`, `get_concept_codelist` | `GET /concepts`, `/concepts/{id}`, `/concepts/{id}/codelist-entries/exports/{fmt}` |
| `publicservices.py` | `list_publicservices`, `get_publicservice` | `GET /publicservices`, `/publicservices/{id}` |
| `catalogs.py` | `get_catalog` | `GET /catalogs/{id}/dcat/exports/{fmt}` |

### `helpers/i14y_api_client.py` — HTTP Client

`I14YApiClient` is an **async context manager** wrapping `httpx.AsyncClient`:

- Sets a custom `User-Agent` header (`mcp-i14y/VERSION`).
- `get(path, **params)` strips `None` values from query parameters via `_build_params()`.
- Detects the response `Content-Type`:
  - `application/json` → parsed and re-serialised as an indented JSON string.
  - `text/turtle`, `application/rdf+xml`, `text/csv` → returned as raw text.
- All HTTP and network errors are caught and returned as `{"error": "..."}` JSON strings — tools never raise exceptions to the MCP layer.

### `helpers/env_config.py` — Configuration

- Maps `I14Y_API_ENV` (`prod` / `test`) to the appropriate base URL.
- Raises `ValueError` on unknown env values to fail fast at startup.
- Provides `get_server_host()` and `get_server_port()` for `main.py`.

---

## Request Flow (example: `list_datasets`)

```
1. LLM sends MCP tool call: list_datasets(publisher_identifier="BFS", page=1)

2. FastMCP deserialises the JSON-RPC request, validates parameters,
   and invokes the async Python function.

3. list_datasets() opens an I14YApiClient context manager,
   which creates an httpx.AsyncClient with the configured base URL.

4. client.get("/datasets", publisherIdentifier="BFS", page=1, pageSize=25)
   → sends GET https://api.i14y.admin.ch/api/public/v1/datasets
         ?publisherIdentifier=BFS&page=1&pageSize=25

5. I14Y API responds with JSON {"data": [...], "totalItems": N, ...}

6. I14YApiClient serialises the response to an indented JSON string.

7. FastMCP wraps the string in a JSON-RPC response and streams it
   back to the LLM client.

8. httpx.AsyncClient is closed (aclose called in __aexit__).
```

---

## I14Y Resource Model

I14Y organises government metadata into four primary resource types plus catalogs:

```
Catalog
  └── Groups of resources published by an organisation (DCAT-AP compliant)

Dataset
  ├── Metadata: title, description, themes, publisher, license, dates
  ├── Distributions (download URLs, formats)
  └── Structure (column definitions, exportable as JSON-LD / RDF / TTL)

DataService
  ├── Metadata: title, description, publisher
  └── Endpoint URL (the API's access point)

Concept  ←── unique to I14Y (not in data.gouv.fr)
  ├── Type: CodeList | Date | Numeric | String
  ├── Metadata: identifier, version, publisher
  └── CodeList entries: [{code, label_de, label_fr, label_it, label_en}]

PublicService  ←── unique to I14Y
  ├── Metadata: title, description, publisher
  └── Eligibility, channels, processing time, etc.
```

### Registration Status lifecycle

```
Initial → Candidate → Recorded → Qualified → Standard → PreferredStandard
                                                              ↓
                                                         Superseded / Retired
```

Publication levels: `Internal` (visible only to partners) | `Public` (visible to all).

---

## Response Format Handling

| Content-Type | Client handling | Typical endpoints |
|---|---|---|
| `application/json` | Parsed JSON → indented string | All list/get endpoints |
| `text/turtle` | Raw text passthrough | `/catalogs/{id}/dcat/exports/ttl`, `/datasets/{id}/structures/exports/Ttl` |
| `application/rdf+xml` | Raw text passthrough | `/catalogs/{id}/dcat/exports/rdf`, `/datasets/{id}/structures/exports/Rdf` |
| `text/csv` | Raw text passthrough | `/concepts/{id}/codelist-entries/exports/csv` |

---

## Deployment

### Local (development)

```bash
uv sync
uv run python main.py
# Server: http://localhost:8000
```

### Docker

```bash
docker compose up -d
# Server: http://localhost:8000
```

The Dockerfile uses `ghcr.io/astral-sh/uv:python3.13-bookworm-slim` as the base image.
Dependencies are installed with `uv sync --frozen --no-dev` for reproducible, minimal images.

---

## Comparison with datagouv-mcp (French reference)

| Aspect | datagouv-mcp | mcp-i14y |
|---|---|---|
| Platform | data.gouv.fr (France) | I14Y (Switzerland) |
| Language | Python 3.13+ | Python 3.13+ |
| MCP framework | FastMCP | FastMCP |
| Transport | Streamable HTTP | Streamable HTTP |
| Auth required | No | No |
| Full-text search | Yes (API supports it) | No (API uses filters only) |
| Tabular data query | Yes (CSV/XLSX via Tabular API) | No equivalent |
| Unique resource types | Datasets, DataServices | + Concepts, PublicServices, Catalogs |
| Multilingual responses | No | Yes (DE/FR/IT/EN object fields) |
| Metrics endpoint | Yes (Matomo) | Not implemented |

---

## Security Notes

- **No credentials** are stored or transmitted — the I14Y Public API requires no authentication.
- For local development, bind to `127.0.0.1` instead of `0.0.0.0` (set `MCP_HOST=127.0.0.1`).
- The MCP endpoint (`/mcp`) should not be exposed publicly without an authentication proxy.
- `SENTRY_DSN` is optional; no telemetry is collected by default.
