# QuestCanvas — Canvas Study Copilot for Canvas LMS

> **Status:** Planning package after MCP-first pivot · April 2026

QuestCanvas is now scoped as an **MCP-first study copilot** for Canvas LMS. The core idea is simple: an AI agent should be able to read course material that already lives in Canvas, extract usable text from lecture files, and answer questions about those materials without manual uploads or copy-paste.

The repo currently contains the **implementation blueprint** for that product. The immediate deliverable is not a hosted dashboard. It is a local Python MCP server that exposes Canvas course material to Claude Desktop, Codex, or similar agent clients.

## Product Direction

### V1: Local MCP server

Primary tool surface:

- `list_courses()`
- `list_course_files(course_id, module_id=None, search=None)`
- `list_modules(course_id)`
- `get_file_text(file_id, max_units=40)`
- `get_assignments(course_id)`
- `get_announcements(course_id, limit=5)`

Primary value:

- Ask for lecture summaries directly from Canvas files
- Read PDFs, slide decks, docs, and plain text course material
- Use assignments and announcements as context, not as the main product

### V2: Local-first indexing and retrieval

Planned additions:

- `index_course(course_id)`
- `get_indexed_files(course_id=None)`
- `search_course_material(query, course_id=None, top_k=5)`

Primary value:

- Index a full term of course material once
- Reuse extracted text and embeddings locally
- Answer repeated questions without resending entire files into model context

## Repository Structure

```text
├── docs/
│   ├── PRD.md                  # Product definition for the study-copilot pivot
│   ├── TECH_REQUIREMENTS.md    # MCP-first technical requirements
│   ├── ARCHITECTURE.md         # Local MCP architecture and future hosted path
│   ├── DATA_MODEL.md           # Study-material data model and local SQLite schema
│   ├── CANVAS_API_PLAN.md      # Canvas endpoint plan for files-first access
│   ├── PRIVACY_SECURITY.md     # Local-first privacy and storage decisions
│   ├── ROADMAP.md              # V1 MCP, V2 indexing/RAG, V3 expansion
│   ├── AUTH_OAUTH.md           # Future OAuth hardening path
│   ├── PLANNER_DESIGN.md       # Deferred planner design, retained for future use
│   └── RISK_REGISTER.md        # Risks and mitigations
│
├── agent_prompts/
│   ├── 01-canvas-api-wrapper.md
│   ├── 02-oauth-token-manager.md
│   ├── 03-planner-engine.md
│   ├── 04-llm-orchestrator.md
│   ├── 05-files-indexer.md
│   └── 06-frontend-shell.md
│
├── docker-compose.yml          # Legacy/local infra sketch, no longer v1-critical
└── README.md
```

The prompt filenames are unchanged for continuity, but their content now follows the new implementation order:

1. Canvas API wrapper
2. Local auth/config
3. File listing and extraction
4. MCP server and tool registration
5. Local indexing and search
6. Optional hosted/web surfaces later

## Key Decisions

- **MCP-first:** the main entry point is an MCP server, not a web app
- **PAT-first auth:** v1 uses a Canvas PAT from environment or local config
- **Files-first scope:** course files are the primary study material source in v1
- **Local-first storage:** v2 uses SQLite for metadata, chunks, and embeddings
- **Planner is secondary:** assignments and announcements remain useful context, but scheduling is no longer the headline capability

## Start Here

1. Read [docs/PRD.md](docs/PRD.md) for the product definition.
2. Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the local MCP system design.
3. Read [docs/CANVAS_API_PLAN.md](docs/CANVAS_API_PLAN.md) for the endpoint and rate-limit plan.
4. Use the prompts in `agent_prompts/` to implement the system in the new order.

## Local Run

1. Install the package: `pip install -e .`
2. Copy `.env.example` values into your shell environment.
3. Set `CANVAS_BASE_URL` and `CANVAS_TOKEN`.
4. Start the stdio MCP server: `python -m questcanvas`

The implementation now lives under `src/questcanvas/` and includes:

- PAT-based config and token provider
- async Canvas API client with pagination and bounded retry handling
- file extraction for PDF, PPTX, DOCX, text, Markdown, CSV, and HTML
- a local MCP server adapter exposing the v1 tool surface

## Status of Older Material

- Planner-focused docs are retained as **deferred design work**, not as the active MVP.
- OAuth and hosted multi-user infrastructure remain future hardening paths.
- The repo still contains some future-state documents because they may be reused after the MCP core ships.
