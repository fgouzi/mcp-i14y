# mcp-i14y

[![Python](https://img.shields.io/badge/python-3.13%2B-blue)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-compatible-green)](https://modelcontextprotocol.io)

**An MCP server that connects AI assistants to the [Swiss I14Y Interoperability Platform](https://www.i14y.admin.ch).**

Ask Claude, Gemini, or GitHub Copilot to explore Swiss government datasets, APIs, codelists, and public services in natural language — powered by the [Model Context Protocol](https://modelcontextprotocol.io).

> Inspired by the French [datagouv-mcp](https://github.com/datagouv/datagouv-mcp) project, adapted for the Swiss I14Y platform.

---

## What is I14Y?

The **I14Y Interoperability Platform** (operated by the Swiss Federal Statistical Office) is Switzerland's national catalog for government data. It standardises and publishes metadata for:
- **Datasets** — data published by federal and cantonal bodies
- **Data Services** — APIs exposing government data
- **Concepts** — reusable data definitions, codelists, and data dictionaries
- **Public Services** — administrative services offered to citizens and businesses

---

## Features

| Tool | Description |
|---|---|
| `list_datasets` | List datasets with filters (publisher, status, level) |
| `get_dataset` | Get full metadata for a dataset |
| `get_dataset_structure` | Export dataset schema (JSON-LD, Turtle, RDF) |
| `list_dataservices` | List data services (APIs) with filters |
| `get_dataservice` | Get full metadata for a data service |
| `list_concepts` | List concepts (codelists, dictionaries) with filters |
| `get_concept` | Get concept details, optionally with codelist entries |
| `get_concept_codelist` | Export all codelist entries (JSON or CSV) |
| `list_publicservices` | List public services with filters |
| `get_publicservice` | Get full metadata for a public service |
| `get_catalog` | Export a catalog in DCAT-AP format (Turtle or RDF/XML) |
| `list_mappingtables` | List mapping tables (source → target codelist correspondences) |
| `get_mappingtable` | Get full metadata for a mapping table |
| `get_mappingtable_relations` | Export all mapping relations (value correspondences) as JSON or CSV |
| `search_datasets` | Search datasets by keyword across titles and descriptions |
| `search_concepts` | Search concepts (codelists) by keyword |
| `find_concept_for_variable` | Find concepts matching a dataset variable name |

---

## Quick Start

### Option 1: Docker Compose (recommended)

```bash
git clone https://github.com/fgouzi/mcp-i14y.git
cd mcp-i14y
cp .env.example .env
docker compose up -d
```

The server will be available at `http://localhost:8400/mcp`.

### Option 2: Local setup with uv

```bash
git clone https://github.com/fgouzi/mcp-i14y.git
cd mcp-i14y
uv sync
uv run python main.py
```

### Verify

```bash
curl http://localhost:8400/health
# → {"status":"ok","platform":"i14y","version":"0.1.0"}
```

---

## Connect to your AI assistant

The MCP endpoint is `http://localhost:8400/mcp` (Streamable HTTP / JSON-RPC).

### Claude Desktop

Add to `claude_desktop_config.json`:

> macOS/Linux: `~/.claude/claude_desktop_config.json` · Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "i14y": {
      "type": "http",
      "url": "http://localhost:8400/mcp"
    }
  }
}
```

### Claude Code (CLI)

```bash
/mcp add i14y http://localhost:8400/mcp
```

### GitHub Copilot (VS Code)

Requires **VS Code 1.112+** with the GitHub Copilot Chat extension.

A `.vscode/mcp.json` file is already included in this repository. After starting the server:

1. Open the repo in VS Code — a **"Start"** button appears at the top of `.vscode/mcp.json`
2. Click **Start** (or run `MCP: List Servers` from the Command Palette)
3. Open Copilot Chat (`Ctrl+Shift+I` / `Cmd+Shift+I`) and switch to **Agent** mode
4. Click the **Tools** icon to confirm the i14y tools are available

To configure manually in another project, create `.vscode/mcp.json`:

```json
{
  "servers": {
    "i14y": {
      "type": "http",
      "url": "http://localhost:8400/mcp"
    }
  }
}
```

### Mistral Le Chat

1. Open [Le Chat](https://chat.mistral.ai) → side panel → **Intelligence** → **Connectors**
2. Click **+ Add Connector** → **Custom MCP Connector**
3. Fill in:
   - **Connector name**: `i14y`
   - **Connection server URL**: `http://localhost:8400/mcp`
   - **Authentication**: None
4. Click **Connect**
5. Enable it in any conversation via the **Tools icon** (four squares) below the chat input

### Mistral Vibe (CLI agent)

Add to your `config.toml`:

```toml
[[mcp_servers]]
name = "i14y"
transport = "streamable-http"
url = "http://localhost:8400/mcp"
```

Tools are then available as `i14y_list_datasets`, `i14y_get_concept`, etc.

### MCP Inspector (testing)

```bash
npx @modelcontextprotocol/inspector http://localhost:8400/mcp
```

---

## Available Tools

### Datasets

#### `list_datasets`
List datasets from the I14Y platform with optional filters.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `publisher_identifier` | string | — | Filter by publisher organisation ID |
| `registration_status` | string | — | `Initial`, `Candidate`, `Recorded`, `Qualified`, `Standard`, `PreferredStandard`, `Superseded`, `Retired` |
| `publication_level` | string | — | `Internal` or `Public` |
| `access_rights` | string | — | Access restriction code |
| `dataset_identifier` | string | — | Filter by dataset identifier |
| `page` | integer | `1` | Page number |
| `page_size` | integer | `25` | Results per page |

#### `get_dataset`
| Parameter | Type | Description |
|---|---|---|
| `dataset_id` | string | Dataset unique identifier |

#### `get_dataset_structure`
| Parameter | Type | Default | Description |
|---|---|---|---|
| `dataset_id` | string | — | Dataset unique identifier |
| `format` | string | `JsonLd` | `JsonLd`, `Ttl`, or `Rdf` |

---

### Data Services

#### `list_dataservices`
Same filter parameters as `list_datasets` (with `dataservice_identifier` instead of `dataset_identifier`).

#### `get_dataservice`
| Parameter | Type | Description |
|---|---|---|
| `dataservice_id` | string | Data service unique identifier |

---

### Concepts

#### `list_concepts`
| Parameter | Type | Default | Description |
|---|---|---|---|
| `publisher_identifier` | string | — | Filter by publisher |
| `concept_identifier` | string | — | Filter by concept identifier |
| `version` | string | — | Filter by version |
| `registration_status` | string | — | Registration status filter |
| `publication_level` | string | — | `Internal` or `Public` |
| `page` | integer | `1` | Page number |
| `page_size` | integer | `25` | Results per page |

#### `get_concept`
| Parameter | Type | Default | Description |
|---|---|---|---|
| `concept_id` | string | — | Concept unique identifier |
| `include_codelist_entries` | boolean | `false` | Embed codelist entries in response |

#### `get_concept_codelist`
| Parameter | Type | Default | Description |
|---|---|---|---|
| `concept_id` | string | — | Concept unique identifier |
| `format` | string | `json` | `json` or `csv` |

---

### Public Services

#### `list_publicservices`
Same filter parameters as `list_datasets` (with `publicservice_identifier`).

#### `get_publicservice`
| Parameter | Type | Description |
|---|---|---|
| `publicservice_id` | string | Public service unique identifier |

---

### Catalogs

#### `get_catalog`
| Parameter | Type | Default | Description |
|---|---|---|---|
| `catalog_id` | string | — | Catalog unique identifier |
| `format` | string | `ttl` | `ttl` (Turtle) or `rdf` (RDF/XML) |

---

### Mapping Tables

A mapping table defines a correspondence between two codelists (source → target), enabling semantic alignment across classification systems (e.g. old canton codes → new codes, Swiss codes → European standards).

#### `list_mappingtables`
| Parameter | Type | Default | Description |
|---|---|---|---|
| `publisher_identifier` | string | — | Filter by publisher organisation ID |
| `mappingtable_identifier` | string | — | Filter by mapping table identifier |
| `version` | string | — | Filter by version string |
| `registration_status` | string | — | `Initial`, `Candidate`, `Recorded`, `Qualified`, `Standard`, `PreferredStandard`, `Superseded`, `Retired` |
| `publication_level` | string | — | `Internal` or `Public` |
| `page` | integer | `1` | Page number |
| `page_size` | integer | `25` | Results per page |

#### `get_mappingtable`
| Parameter | Type | Description |
|---|---|---|
| `mappingtable_id` | string | Mapping table unique identifier (UUID) |

#### `get_mappingtable_relations`
| Parameter | Type | Default | Description |
|---|---|---|---|
| `mappingtable_id` | string | — | Mapping table unique identifier (UUID) |
| `format` | string | `Json` | `Json` or `Csv` |

---

### Search

Since the I14Y API has no full-text search endpoint, these tools fetch pages progressively and rank results client-side.

#### `search_datasets`
| Parameter | Type | Default | Description |
|---|---|---|---|
| `keyword` | string | — | Search term(s) — space-separated words are scored independently |
| `publisher_identifier` | string | — | Optionally restrict to a single publisher |
| `max_results` | integer | `10` | Maximum number of results to return |

#### `search_concepts`
| Parameter | Type | Default | Description |
|---|---|---|---|
| `keyword` | string | — | Search term(s) |
| `publisher_identifier` | string | — | Optionally restrict to a single publisher |
| `max_results` | integer | `10` | Maximum number of results to return |

#### `find_concept_for_variable`
Given a variable name from `get_dataset_structure()`, finds the best matching I14Y concept (codelist).

| Parameter | Type | Description |
|---|---|---|
| `variable_name` | string | Variable name to look up (any language) |
| `publisher_identifier` | string | Optionally restrict to a single publisher |

---

## Example Prompts

Once connected, try asking your LLM assistant:

- *"List all public datasets published by the Federal Statistical Office."*
- *"What data services are available with status Standard?"*
- *"Show me the codelist for Swiss canton codes."*
- *"Get the full details for dataset with ID `abc-123`."*
- *"Export the catalog of the OFS in Turtle format."*
- *"What public administrative services are registered on I14Y?"*
- *"Search for datasets about employment by canton."*
- *"Find the concept that matches the variable 'Secteur économique'."*
- *"List all mapping tables that link old canton codes to new ones."*
- *"Export the mapping relations for mapping table `xyz-456` as CSV."*

---

## Development

### Setup

```bash
git clone https://github.com/fgouzi/mcp-i14y.git
cd mcp-i14y
uv sync
cp .env.example .env
```

### Run tests

```bash
# Unit tests only (no network required)
uv run pytest

# Including integration tests (hits live I14Y test API)
uv run pytest -m integration
```

### Lint & format

```bash
uv run ruff check --fix .
uv run ruff format .
```

### Install pre-commit hooks

```bash
uv run pre-commit install
```

---

## Configuration

Copy `.env.example` to `.env` and adjust:

| Variable | Default | Description |
|---|---|---|
| `MCP_HOST` | `0.0.0.0` | Bind address (`127.0.0.1` for local-only) |
| `MCP_PORT` | `8400` | Server port |
| `I14Y_API_ENV` | `prod` | `prod` or `test` |
| `LOG_LEVEL` | `INFO` | Logging level |
| `SENTRY_DSN` | _(empty)_ | Optional Sentry DSN |

---

## License

MIT — see [LICENSE](LICENSE).

---

## Credits

- Inspired by [datagouv-mcp](https://github.com/datagouv/datagouv-mcp) by the [data.gouv.fr](https://www.data.gouv.fr) team
- Built on [FastMCP](https://github.com/jlowin/fastmcp) and the [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- Data provided by the [Swiss Federal Statistical Office (OFS/BFS)](https://www.bfs.admin.ch) via [I14Y](https://www.i14y.admin.ch)
