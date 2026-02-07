# DevTools Overview

> **Branch:** master
> **Last Updated:** 2026-02-07

## TL;DR

Unified TypeScript monorepo with single CLI entrypoint `aw <subcommand>`. All tools built with Node.js: CLI (Commander.js), server (NestJS), frontend (Next.js). Organized with domain-first folder structure, pnpm workspaces for package management.

## Purpose & Bounded Context

- **Role:** Provide unified CLI toolset and backend services for entire development workflow
- **Domain:** Developer Experience, Automation, Local Development Infrastructure

## Design Philosophy

### Core Principles

1. **Single Entrypoint** — All tools accessed via `aw <subcommand>`
2. **Domain-First Organization** — Folder structure by domain, not by tool type
3. **TypeScript Everywhere** — CLI, server, frontend — all TypeScript
4. **pnpm Workspace = Plugin System** — Each domain exports a Commander program, composed via `.addCommand()`
5. **Modular Backend** — Each feature is a NestJS module in its own pnpm package, imported by a single unified server

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    User Terminal / AI Agent                   │
│                         │                                   │
│                    aw <command>                              │
│                         │                                   │
│  ┌──────────────────────┴──────────────────────┐            │
│  │             @aweave/cli (Commander.js)       │            │
│  │  ┌──────────┐ ┌──────────┐ ┌─────────────┐  │            │
│  │  │cli-debate│ │ cli-docs │ │cli-bitbucket │  │            │
│  │  └────┬─────┘ └────┬─────┘ └──────┬──────┘  │            │
│  └───────┼─────────────┼──────────────┼─────────┘            │
│          │             │              │                      │
│          ▼             │              ▼                      │
│  ┌───────────────┐     │      ┌─────────────┐               │
│  │ @aweave/server │     │      │ Bitbucket   │               │
│  │   (NestJS)    │     │      │  REST API   │               │
│  │ ┌───────────┐ │     │      └─────────────┘               │
│  │ │  Debate   │ │     │                                    │
│  │ │  Module   │ │     │  SQLite (direct)                   │
│  │ └───────────┘ │     └─────────────┘                      │
│  └───────────────┘                                          │
│                                                             │
│  ┌───────────────┐                                          │
│  │  debate-web   │  (Next.js — WebSocket to server)         │
│  └───────────────┘                                          │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
devtools/
├── common/                        # Shared tools & core infrastructure
│   ├── cli-core/                  # @aweave/cli — root CLI + shared utilities
│   │   └── src/
│   │       ├── bin/aw.ts          # Global entrypoint
│   │       ├── program.ts         # Commander root, registers subcommands
│   │       ├── mcp/               # MCP response format helpers
│   │       ├── http/              # HTTP client utilities
│   │       └── services/          # pm2 service management
│   ├── cli-debate/                # @aweave/cli-debate — aw debate commands
│   ├── cli-docs/                  # @aweave/cli-docs — aw docs commands
│   ├── server/                    # @aweave/server — unified NestJS server
│   ├── nestjs-debate/             # @aweave/nestjs-debate — debate backend module
│   └── debate-web/                # Next.js debate monitoring UI
├── <domain>/                      # Domain-specific tools
│   ├── cli-<tool>/                # CLI package for this domain
│   └── local/                     # Local dev infrastructure
│       ├── docker-compose.yaml
│       ├── Justfile
│       └── .env.example
├── pnpm-workspace.yaml            # pnpm workspace packages
└── .npmrc                         # Build permissions
```

## Core Components

### CLI (`@aweave/cli` — Commander.js)

- **Root program** (`cli-core/src/program.ts`): Registers all subcommands via `.addCommand()`
- **Domain packages** export Commander `Command` objects, composed at root level
- **Shared utilities**: MCP response format, HTTP client, pm2 service management
- **Global install**: `pnpm add -g @aweave/cli` → `aw` command available globally

### Server (`@aweave/server` — NestJS)

- Single unified server at port `3456`
- Feature modules imported as separate pnpm packages (`@aweave/nestjs-<feature>`)
- Shared infrastructure: auth guard, exception filter, CORS
- REST API + WebSocket support

### MCP Response Format

All CLI tools output responses in a structured format designed for AI agent consumption:

```json
{
  "success": true,
  "content": [{ "type": "json", "data": { ... } }],
  "metadata": { ... },
  "has_more": false,
  "total_count": 10
}
```

## Development Approach

### Adding a New CLI Tool

1. Create package at `devtools/<domain>/cli-<name>/`
2. Export a Commander `Command` from the package
3. Add to `pnpm-workspace.yaml`
4. Import and register in `cli-core/src/program.ts` via `.addCommand()`
5. Build: `pnpm build`

### Adding a New Backend Feature

1. Create NestJS module package at `devtools/<domain>/nestjs-<feature>/`
2. Export NestJS module from the package
3. Add as dependency of `@aweave/server`
4. Import in `server/src/app.module.ts`
5. See: `devdocs/misc/devtools/common/server/OVERVIEW.md` for full pattern

## Package Management

- **pnpm** — Workspace management for all packages
- **pnpm-workspace.yaml** — Defines all workspace packages
- Dependencies isolated per package, shared via `workspace:*` protocol

### Key Considerations

- All packages use TypeScript with strict mode
- Internal workspace dependencies use `workspace:*` version spec
- `aw` is installed globally via `pnpm add -g @aweave/cli`

## Quick Reference

| Task | Command |
|------|---------|
| Install all | `cd devtools && pnpm install` |
| Build all | `cd devtools && pnpm -r build` |
| Build specific | `cd devtools/common/<pkg> && pnpm build` |
| Run CLI (dev) | `cd devtools/common/cli-core && node dist/bin/aw.js <cmd>` |
| Run CLI (global) | `aw <cmd>` |
| Start server | `cd devtools/common/server && node dist/main.js` |
| Health check | `curl http://127.0.0.1:3456/health` |

## Package Documentation

Each package has its own OVERVIEW at:
- CLI packages: `devdocs/misc/devtools/common/cli-<package>/OVERVIEW.md`
- NestJS modules: `devdocs/misc/devtools/common/nestjs-<package>/OVERVIEW.md`
- Server: `devdocs/misc/devtools/common/server/OVERVIEW.md`
- Domain-specific: `devdocs/misc/devtools/<domain>/<package>/OVERVIEW.md`
