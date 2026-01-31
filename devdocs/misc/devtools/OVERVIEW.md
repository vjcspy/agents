# DevTools Overview

> **Branch:** master
> **Last Commit:** b11f8de
> **Last Updated:** 2026-01-31

## TL;DR

Unified CLI monorepo với single entrypoint `aw <subcommand>`. Hỗ trợ Python plugins (entry points, in-process) và Node plugins (registry, subprocess). Tổ chức theo domain: common, nab, tinybots, vocalmeet.

## Repo Purpose & Bounded Context

- **Role:** Cung cấp unified CLI toolset cho toàn bộ development workflow
- **Domain:** Developer Experience, Automation, Local Development Infrastructure

## Design Context

### User Requirements

- Monorepo với multiple CLI tools tổ chức theo domain: common, nab, tinybots
- Mỗi tool có thể implement bằng Python hoặc Node
- Single unified CLI entrypoint: `aw <subcommand>`
- Domain-first folder structure; không tách theo language. Tất cả CLIs nằm trong `<domain>/cli/`
- Feature-based package naming; không cần prefix đặc biệt
- Python managed bởi uv workspace với pip fallback khi không có uv
- Node plugins discovered qua registry để aw có thể invoke qua subprocess

### Design Objectives

- Cung cấp unified CLI `aw` cho cả Python và Node tools
- Python plugins: auto-discovered qua `aw.plugins` entry points, chạy in-process
- Node plugins: discovered qua `aw-plugin.yaml` → generate `aw-plugins.yaml` → executed qua subprocess wrapper
- Sử dụng uv workspace như single lock cho tất cả Python members; pnpm workspace cho Node
- Support pip fallback cho environments không có uv

### Key Considerations

- Single Python environment và shared lock; dependency conflicts giữa các tools sẽ gây sync failures
- Root có thể export `requirements.txt` từ `uv.lock` cho pip fallback; `install-all.sh` sử dụng nó khi có
- Internal workspace dependencies phải declare `[tool.uv.sources]` với `workspace = true` trong member's pyproject
- `aw` được link tới `~/.local/bin/aw` qua wrapper script (chạy `uv run aw` khi cần)
- Node plugins chỉ được load khi `aw-plugin.yaml` exists và `dist/cli.js` đã build, sau đó registry được generate

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

### Plugin System Comparison

| Type | Discovery | Execution | Use Case |
|------|-----------|-----------|----------|
| Python | Entry points (`aw.plugins`) | In-process | Complex logic, leverage shared libraries |
| Node | Registry (`aw-plugin.yaml` → `aw-plugins.yaml`) | Subprocess | Rapid prototyping, leverage npm ecosystem |

## Project Structure

```
devtools/
├── common/cli/devtool/     # Root CLI "aw" + shared utilities (aweave package)
│   └── aweave/
│       ├── core/           # CLI core: main.py, plugin loaders
│       ├── docs/           # Document store CLI module
│       ├── http/           # HTTP client utilities
│       └── mcp/            # MCP pagination/response helpers
├── nab/
│   └── cli/
│       ├── confluence/     # Python: aw confluence (nab-confluence)
│       └── foo/            # Node: aw foo (example)
├── tinybots/
│   ├── cli/
│   │   └── bitbucket/      # Python: aw tinybots-bitbucket
│   └── local/              # Local dev infra (docker-compose, Justfile, seeds)
├── vocalmeet/
│   └── local/              # Local dev infra for vocalmeet domain
├── scripts/                # install-all.sh, doctor.sh, generate-registry.py
├── pyproject.toml          # uv workspace root
├── pnpm-workspace.yaml     # pnpm workspace for Node plugins
└── CLI_TOOLS.md            # Quick reference for available tools
```

## CLI Commands (Public Surface)

> **Quick Reference:** Xem `devtools/CLI_TOOLS.md` để có danh sách tools với links tới documentation.

### Root CLI (`aw`)

Entry point cho tất cả tools. Python plugins được discover qua `aw.plugins` entry points, Node plugins qua `aw-plugins.yaml` registry.

```bash
aw --help          # List all available commands
aw version         # Show version info
```

### Common Domain

- **`aw docs`** - Document store với immutable versioning cho AI agents
  - `aw docs init` - Initialize doc store
  - `aw docs add` - Add document (creates version)
  - `aw docs get` - Retrieve document by ID
  - `aw docs list` - List all documents
  - Docs: `common/cli/devtool/aweave/docs/README.md`

### TinyBots Domain

- **`aw tinybots-bitbucket`** - Bitbucket PR tools với auto-pagination
  - `aw tinybots-bitbucket pr-comments` - Get PR comments
  - `aw tinybots-bitbucket pr-diff` - Get PR diff
  - Docs: `tinybots/cli/bitbucket/tinybots/bitbucket/README.md`

## Core Services & Logic

### Plugin System

- **Python Loader** (`core/python_loader.py`): Auto-discover plugins via `aw.plugins` entry points, execute in-process
- **Node Loader** (`core/node_loader.py`): Load registry từ `aw-plugins.yaml`, execute via subprocess
- **Main CLI** (`core/main.py`): Typer app, orchestrates plugin discovery và command routing

### Shared Utilities (`aweave` package)

- **HTTP Client** (`http/client.py`): Reusable HTTP client với common patterns
- **MCP Helpers** (`mcp/`): Pagination, response formatting cho MCP integrations

### Local Development Infrastructure

Mỗi domain có thể có `<domain>/local/` chứa:

- `docker-compose.yaml` - Local services
- `Justfile` - Common tasks (seeding, migrations, etc.)
- `.env.example` - Environment template
- Seed scripts - Test data generation

## External Dependencies

### Python Dependencies

- **typer** - CLI framework
- **httpx** - HTTP client (nếu cần)
- **ruff** - Linting & formatting (dev)
- **pytest** - Testing (dev)

### Node Dependencies (nếu có Node plugins)

- **pnpm** - Package manager
- Dependencies specific to each Node plugin

### Package Management

- **uv** - Python workspace management (preferred)
- **pip** - Fallback khi không có uv
- **pnpm** - Node workspace management

## Development Workflow

### Adding a New Python Plugin

1. Tạo package tại `<domain>/cli/<name>/`
2. Cấu hình `pyproject.toml` với entry point `aw.plugins`
3. Thêm vào workspace root `pyproject.toml`
4. Run `uv sync`

### Adding a New Node Plugin

1. Tạo package tại `<domain>/cli/<name>/`
2. Tạo `aw-plugin.yaml` marker
3. Build `dist/cli.js`
4. Run `python scripts/generate-registry.py`

### Installation

```bash
cd devtools
./scripts/install-all.sh    # Full install + link to ~/.local/bin/aw
```

### Development Mode

```bash
cd devtools
uv sync
uv run aw --help
```

## Quick Reference

| Task | Command |
|------|---------|
| Install all | `./scripts/install-all.sh` |
| Sync Python deps | `uv sync` |
| Run CLI (dev mode) | `uv run aw <cmd>` |
| Lint | `uv run ruff check .` |
| Generate Node registry | `uv run python scripts/generate-registry.py` |
