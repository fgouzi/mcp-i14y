# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-03-24

### Added
- Initial release of `mcp-i14y`
- 11 MCP tools covering all I14Y Public API resource types:
  - `list_datasets`, `get_dataset`, `get_dataset_structure`
  - `list_dataservices`, `get_dataservice`
  - `list_concepts`, `get_concept`, `get_concept_codelist`
  - `list_publicservices`, `get_publicservice`
  - `get_catalog`
- Async HTTP client (`I14YApiClient`) with httpx
- Support for `prod` and `test` API environments via `I14Y_API_ENV`
- Health endpoint at `GET /health`
- Docker and Docker Compose support
- Optional Sentry error tracking
- Full unit test suite with mocked API responses
- Integration test marker for live API testing
