# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

QuestCanvas is a **local MCP-first study copilot** for Canvas LMS. The shipping surface is a stdio MCP server (`python -m questcanvas`) that exposes Canvas course material (courses, modules, files, assignments, announcements) to agent clients like Claude Desktop. There is no web app, no hosted backend, and no OAuth in V1 — auth is a Canvas Personal Access Token read from the environment.

V2 (not yet implemented) will add local SQLite-backed indexing and retrieval (`index_course`, `search_course_material`). Planner/scheduling features are deferred; `docs/PLANNER_DESIGN.md` and older `agent_prompts/` filenames reflect the pre-pivot plan.

## Commands

- Install (editable): `pip install -e .`
- Required Python: `>=3.12`
- Required env: `CANVAS_BASE_URL`, `CANVAS_TOKEN`. Optional: `QUESTCANVAS_DATA_DIR` (defaults to `~/.local/share/questcanvas`). See `.env.example`.
- Run the MCP stdio server: `python -m questcanvas` (or the `questcanvas` console script).
- Run all tests: `python -m unittest discover -s tests -t .`
- Run one test file: `python -m unittest tests.test_canvas_client`
- Run one test: `python -m unittest tests.test_canvas_client.TestCanvasClient.test_whatever`

There is no lint/format config and no dev extras in `pyproject.toml`. Tests use `unittest` plus in-repo fakes (`tests/fakes.py`) — no pytest, no network, no real httpx client.

## Architecture

The system is assembled top-down in `src/questcanvas/server.py` as `QuestCanvasApp`. `QuestCanvasApp.from_env()` builds the full object graph: `AppConfig` → `StaticTokenProvider` → `CanvasClient` → `FileService` → tool handlers. `build_mcp_server()` wraps the six tool methods with `FastMCP` decorators; `run_stdio()` starts the server. The MCP SDK is imported lazily inside `build_mcp_server` so unit tests and non-MCP callers don't need it installed.

Layering (each layer depends only on layers below it):

1. `canvas/` — Typed async Canvas REST wrapper. `CanvasClient` handles pagination (`_get_paginated` follows `Link: rel="next"` via `pagination.py`), throttling/retry (`rate_limits.py` inspects `X-Rate-Limit-Remaining`, `X-Request-Cost`, 403/429 with `Rate Limit Exceeded`), and error normalization (`errors.py` → `CanvasResponseError`, `CanvasRateLimitError`). The HTTP client is injected as an `AsyncHttpClient` Protocol so tests substitute fakes; `httpx.AsyncClient` is only constructed lazily on first use.
2. `extractors/` — `ExtractorRegistry` picks one of `PdfExtractor` (PyMuPDF), `PptxExtractor` (python-pptx), `DocxExtractor` (python-docx), `HtmlExtractor`, `TextExtractor` based on MIME/extension. All return `ExtractionResult` with `ExtractionUnit`s bounded by `max_units`. Each extractor imports its heavy dependency lazily so missing optional deps surface as `MissingDependencyError` at extraction time, not import time.
3. `services/files.py` — `FileService` joins Canvas file listings with module items (to filter by `module_id`) and owns the download-then-extract flow for `get_file_text`.
4. `tools/` — Thin adapters that shape service/client output into the JSON-serializable dicts the MCP tools return. Keep the six tool signatures in `server.py` in sync with handlers here.

### Conventions that matter

- **Auth** is abstracted behind `TokenProvider` (`auth.py`). V1 only has `StaticTokenProvider`, but the interface is `async get_token()` so a future OAuth provider drops in without changing `CanvasClient`.
- **Errors** defined in `errors.py` are the public boundary: `ConfigError`, `CanvasResponseError`, `CanvasRateLimitError`, `UnsupportedFileTypeError`, `MissingDependencyError`. Tools/services should raise these rather than leaking httpx/PyMuPDF exceptions.
- **Pagination**: always use `_get_paginated` for list endpoints; it sets `per_page=100` and walks `Link` headers. Don't re-implement in tools.
- **Rate limits**: `_request` sleeps between attempts using `get_retry_delay` and applies a post-response `get_budget_delay` when remaining budget is low. Bounded by `max_retries` (default 3) — after that it raises `CanvasRateLimitError`.
- **URL handling**: `CanvasClient._make_url` accepts either a relative path or a fully-qualified URL (needed because Canvas file download URLs are pre-signed absolute URLs on a different host).
- **Logging**: `CanvasClient` logs method, path (never full URL with query — see `_safe_path`), status, elapsed ms, and cost/remaining headers. Preserve this shape; downstream observability may depend on it.

### Tests

`tests/fakes.py` provides a `FakeHttpClient` and response helpers used across `test_canvas_client.py`, `test_file_service.py`, and `test_server.py`. `test_server.py` uses stub clients directly rather than the fake HTTP layer. When adding a new Canvas endpoint, extend the fake rather than mocking httpx.
