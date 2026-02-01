# DevTools Overview

> **Branch:** master
> **Last Updated:** 2026-02-01

## TL;DR

Unified CLI monorepo with single entrypoint `aw <subcommand>`. Supports Python plugins (entry points, in-process) and Node plugins (registry, subprocess). Organized with domain-first folder structure.

## Purpose & Bounded Context

- **Role:** Provide unified CLI toolset for entire development workflow
- **Domain:** Developer Experience, Automation, Local Development Infrastructure

## Design Philosophy

### Core Principles

1. **Single Entrypoint** — All tools accessed via `aw <subcommand>`
2. **Domain-First Organization** — Folder structure by domain, not by language
3. **Language Flexibility** — Each tool can be implemented in Python or Node
4. **Shared Infrastructure** — Common utilities shared via `aweave` package

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    User Terminal                            │
│                         │                                   │
│                    aw <command>                             │
│                         │                                   │
│         ┌───────────────┴───────────────┐                   │
│         │                               │                   │
│         ▼                               ▼                   │
│  ┌─────────────────┐           ┌─────────────────┐         │
│  │ Python Plugins  │           │  Node Plugins   │         │
│  │ (Entry Points)  │           │   (Registry +   │         │
│  │   aw.plugins    │           │   Subprocess)   │         │
│  └─────────────────┘           └─────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### Plugin System

| Type | Discovery | Execution | Use Case |
|------|-----------|-----------|----------|
| Python | Entry points (`aw.plugins`) | In-process | Complex logic, leverage shared libraries |
| Node | Registry (`aw-plugin.yaml` → `aw-plugins.yaml`) | Subprocess | Rapid prototyping, leverage npm ecosystem |

## Project Structure

```
devtools/
├── common/                     # Shared tools & core infrastructure
│   └── cli/devtool/aweave/     # Root CLI "aw" + shared utilities
│       ├── core/               # CLI core: main.py, plugin loaders
│       ├── http/               # HTTP client utilities
│       └── mcp/                # MCP pagination/response helpers
├── <domain>/                   # Domain-specific tools
│   ├── cli/                    # CLI tools for this domain
│   │   └── <tool>/             # Individual tool package
│   └── local/                  # Local dev infrastructure
│       ├── docker-compose.yaml
│       ├── Justfile
│       └── .env.example
├── scripts/                    # install-all.sh, generate-registry.py
├── pyproject.toml              # uv workspace root
├── pnpm-workspace.yaml         # pnpm workspace for Node plugins
└── CLI_TOOLS.md                # Quick reference for available tools
```

## Core Components

### Plugin System

- **Python Loader** (`core/python_loader.py`): Auto-discover plugins via `aw.plugins` entry points
- **Node Loader** (`core/node_loader.py`): Load registry from `aw-plugins.yaml`, execute via subprocess
- **Main CLI** (`core/main.py`): Typer app, orchestrates plugin discovery and command routing

### Shared Utilities (`aweave` package)

- **HTTP Client** (`http/client.py`): Reusable HTTP client with common patterns
- **MCP Helpers** (`mcp/`): Pagination, response formatting for MCP integrations

## Development Approach

### Adding a New CLI Tool

> **SKILL:** When creating new CLI tool, AI agents **MUST** read and follow:
> `devdocs/agent/skills/common/devtools-builder/SKILL.md`
>
> Key patterns:
> - MCP-compatible response format for AI agent compatibility
> - Auto-pagination pattern (CLI returns full data, `has_more=false`)
> - Actionable error messages
> - Shared utilities (`aweave/http/`, `aweave/mcp/`)

### Python Plugin

1. Create package at `<domain>/cli/<name>/`
2. Configure `pyproject.toml` with entry point `aw.plugins`
3. Add to workspace root `pyproject.toml`
4. Run `uv sync`

### Node Plugin

1. Create package at `<domain>/cli/<name>/`
2. Create `aw-plugin.yaml` marker
3. Build `dist/cli.js`
4. Run `python scripts/generate-registry.py`

## Package Management

### Python

- **uv** — Primary workspace management (preferred)
- **pip** — Fallback when uv is not available
- Single lock file (`uv.lock`) for all Python packages

### Node

- **pnpm** — Workspace management for Node plugins
- Dependencies isolated per plugin

### Key Considerations

- Single Python environment; dependency conflicts between tools will cause sync failures
- Internal workspace dependencies must declare `[tool.uv.sources]` with `workspace = true`
- `aw` is linked to `~/.local/bin/aw` via wrapper script

## Quick Reference

| Task | Command |
|------|---------|
| Install all | `cd devtools && ./scripts/install-all.sh` |
| Sync Python deps | `cd devtools && uv sync` |
| Run CLI (dev mode) | `uv run aw <cmd>` |
| Lint Python | `uv run ruff check .` |
| Generate Node registry | `uv run python scripts/generate-registry.py` |
| List available tools | `aw --help` |

## Package Documentation

Each package has its own OVERVIEW at:
- Python CLI: `devdocs/misc/devtools/<domain>/cli/devtool/aweave/<package>/OVERVIEW.md`
- Node packages: `devdocs/misc/devtools/<domain>/<package>/OVERVIEW.md`
- Common: `devdocs/misc/devtools/common/...`

See `devtools/CLI_TOOLS.md` for list of tools with links to documentation.
