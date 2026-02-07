# 📋 [CLI-OCLIF: 2026-02-07] - Refactor CLI from Commander.js to oclif Plugin Architecture

## References

- Previous migration plan (superseded): `devdocs/misc/devtools/plans/260207-cli-typescript-migration.md`
- DevTools overview: `devdocs/misc/devtools/OVERVIEW.md`
- Debate ecosystem spec: `devdocs/misc/devtools/debate.md`
- Unified NestJS server plan: `devdocs/misc/devtools/plans/260207-unified-nestjs-server.md`

## Background & Decision Context

> This plan supersedes the Commander.js approach from `260207-cli-typescript-migration.md`.

The `aw` CLI was initially migrated from Python to TypeScript using Commander.js. While functional, Commander.js showed architectural issues for a **multi-domain platform CLI**:

1. **Cyclic dependencies** — cli-core depended on plugins (to load them), plugins depended on cli-core (for utilities). pnpm warned about this.
2. **Fragile plugin loading** — `try { require() } catch {}` in bin/aw.ts. Silent failures, no standard discovery.
3. **Adding a domain = editing core** — Every new plugin required modifying cli-core's package.json AND bin/aw.ts.

### Why oclif?

`aw` is a **platform CLI** that serves multiple domains (`common/`, `tinybots/`, `nab/`, future domains). oclif provides:

- **Standard plugin system** — Plugins declared in `oclif.plugins` config, auto-discovered at runtime
- **No cyclic dependencies** — Shared utilities in `@aweave/cli-shared`, both main CLI and plugins depend on it independently
- **File-based command routing** — `src/commands/debate/create.ts` → `aw debate create`
- **Built-in flag validation** — Type-safe flags with required/optional, options validation
- **Manifest caching** — `oclif.manifest.json` for fast command lookup

### Architecture

```
@aweave/cli-shared (pure utilities — MCPResponse, HTTPClient, helpers)
     ↑                    ↑
     |                    |
@aweave/cli          @aweave/cli-plugin-*
(oclif main)         (oclif plugins)
```

No cycles. `@aweave/cli-shared` is a leaf dependency that both the main CLI and all plugins depend on.

## 🎯 Objective

Refactor the `aw` CLI from Commander.js to oclif plugin architecture, eliminating cyclic dependencies and establishing a scalable multi-domain plugin pattern.

### ⚠️ Key Considerations

1. **All business logic is preserved** — MCP response models, HTTP client, debate/docs/bitbucket logic are unchanged. Only the command registration pattern changes.
2. **MCP response format unchanged** — The JSON output contract with AI agents is identical.
3. **oclif uses CommonJS** — All packages use `"module": "commonjs"` in tsconfig for oclif compatibility.

## 📐 Package Structure

| Package | npm name | Folder | Dependencies |
|---------|----------|--------|--------------|
| CLI Shared | `@aweave/cli-shared` | `devtools/common/cli-shared/` | (none) |
| CLI Main | `@aweave/cli` | `devtools/common/cli/` | `@oclif/core`, `cli-shared`, all plugins |
| Debate Plugin | `@aweave/cli-plugin-debate` | `devtools/common/cli-plugin-debate/` | `@oclif/core`, `cli-shared` |
| Docs Plugin | `@aweave/cli-plugin-docs` | `devtools/common/cli-plugin-docs/` | `@oclif/core`, `cli-shared`, `better-sqlite3` |
| Bitbucket Plugin | `@aweave/cli-plugin-bitbucket` | `devtools/tinybots/cli-plugin-bitbucket/` | `@oclif/core`, `cli-shared` |

## 🔄 Implementation Plan

### Phase 1: Create @aweave/cli-shared
- Move mcp/, http/, helpers/, services/ from old cli-core
- Remove Commander.js, bin/, program.ts
- Pure utilities package, no CLI framework dependency

### Phase 2: Create @aweave/cli (oclif main)
- New oclif CLI with bin/run.js, bin/dev.js
- oclif config declaring all plugins
- `pnpm link --global`

### Phase 3: Convert plugins to oclif
- Each command → one file in `src/commands/<topic>/<command>.ts`
- Commander chains → oclif Command classes with static flags
- Import `@aweave/cli-shared` instead of `@aweave/cli`

### Phase 4: Cleanup
- Delete old Commander.js packages
- Update workspace config

## 📊 Summary of Results

> Do not summarize until implementation is done

### ✅ Completed Achievements

- [ ] ...
