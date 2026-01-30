# Devtools (Unified CLI Monorepo)

A domain/project-oriented “dev tools” monorepo with **a single entrypoint**:

```bash
aw <subcommand> [...]
```

This repo supports:
- Python tools via **entry points** (`aw.plugins`) → runs in-process.
- Node tools via a **registry** (`aw-plugins.yaml`) + subprocess wrapper → `aw <node-plugin> ...`.

## Context (for AI Agents)

### User Requirements

- Monorepo with multiple CLI tools organized by domain: common, nab, tinybots.
- Each tool may be implemented in Python or Node.
- Single unified CLI entrypoint: aw <subcommand>.
- Domain-first folder structure; do not split by language. All CLIs live under <domain>/cli/.
- Feature-based package naming; no special prefixes required.
- Python managed by uv workspace with pip fallback when uv is unavailable.
- Node plugins discovered via registry so aw can invoke them through subprocess.

### Objective

- Provide a unified CLI aw for both Python and Node tools.
- Python plugins: auto-discovered via aw.plugins entry points and run in-process.
- Node plugins: discovered via aw-plugin.yaml → generate aw-plugins.yaml → executed via subprocess wrapper.
- Use uv workspace as a single lock for all Python members; pnpm workspace for Node.
- Support pip fallback for environments without uv.

### Key Considerations

- Single Python environment and shared lock; dependency conflicts across tools will cause sync failures.
- The root can export requirements.txt from uv.lock for pip fallback; install-all.sh uses it when present.
- Internal workspace dependencies must declare [tool.uv.sources] with workspace = true in the member’s pyproject.
- aw is linked to ~/.local/bin/aw via a wrapper script (runs uv run aw when needed).
- Node plugins are loaded only when aw-plugin.yaml exists and dist/cli.js is built, then the registry is generated.

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
│  │ • confluence    │           │ • foo           │         │
│  └─────────────────┘           └─────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### Plugin System Comparison

| Type | Discovery | Execution | Use Case |
|------|-----------|-----------|----------|
| Python | Entry points (aw.plugins) | In-process | Complex logic, leverage shared libraries |
| Node   | Registry (aw-plugin.yaml → aw-plugins.yaml) | Subprocess | Rapid prototyping, leverage npm ecosystem |

## Quickstart

### Install (recommended)

```bash
cd devtools
./scripts/install-all.sh
```

This script will:
1. Check your environment (doctor.sh)
2. Install Python packages via `uv sync`
3. Install Node packages via `pnpm install` (if available)
4. Generate the plugin registry
5. **Link `aw` to `~/.local/bin/aw`** for global access

After installation, make sure `~/.local/bin` is in your PATH. Add to `~/.zshrc` or `~/.bashrc`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Then reload your shell (`source ~/.zshrc`) and you can run `aw` from **anywhere**:

```bash
aw --help
```

### Development mode (without global install)

If you want to run without linking to `~/.local/bin/aw`:

```bash
cd devtools
uv sync
uv run aw --help
```

### Generate plugin registry (for Node plugins)

From the devtools directory:

```bash
cd devtools
uv run python scripts/generate-registry.py
```

The registry is written to `aw-plugins.yaml` at the repo root.

## Usage

After running `install-all.sh`, `aw` is available globally. No need to `cd` into devtools:

```bash
aw --help
aw version
```

### Python plugin: confluence

```bash
aw confluence --help
aw confluence status
aw confluence sync <source> --dry-run
```

### Node plugin: foo

The Node plugin is only added to `aw` if the `bin` path in the registry exists (e.g. `nab/cli/foo/dist/cli.js`).

First, build from devtools directory:

```bash
cd devtools
pnpm install
pnpm -r build
uv run python scripts/generate-registry.py
```

Then use from anywhere:

```bash
aw foo --help
aw foo build --watch
```

## Repository layout (short)

```
devtools/
  common/cli/devtool/          # Python package "aw" (root CLI)
  nab/cli/confluence/          # Python package (aw plugin)
  nab/cli/foo/                 # Node package (aw plugin)
  scripts/                     # install-all.sh, doctor.sh, generate-registry.py, ...
  pyproject.toml               # uv workspace root
  pnpm-workspace.yaml          # pnpm workspace
```

## Adding a new plugin

### Add a Python plugin

1) Create a package at `<domain>/cli/<name>/` with the following structure:

```
<domain>/cli/<name>/
├── pyproject.toml
├── ruff.toml                    # Optional: linting config
└── <namespace>/                 # Namespace package (e.g., tinybots, nab)
    ├── __init__.py              # """<Namespace> CLI tools namespace package."""
    └── <module>/                # Actual module (e.g., bitbucket, confluence)
        ├── __init__.py
        ├── cli.py               # Typer app
        └── ...                  # Other module files
```

**Why namespace package?** This allows multiple plugins under the same namespace (e.g., `tinybots.bitbucket`, `tinybots.jira`) to coexist without conflicts.

2) Configure `pyproject.toml`:

```toml
[project]
name = "<namespace>-<module>"    # e.g., tinybots-bitbucket
version = "0.1.0"
dependencies = ["aweave"]        # Add if using common utilities

[project.entry-points."aw.plugins"]
<command> = "<namespace>.<module>.cli:app"   # e.g., tinybots.bitbucket.cli:app

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["<namespace>"]       # e.g., ["tinybots"]

[tool.uv.sources]
aweave = { workspace = true }    # If using common utilities
```

3) Add to workspace root `pyproject.toml`:

```toml
[tool.uv.workspace]
members = [
    # ... existing members
    "<domain>/cli/<name>"        # e.g., "tinybots/cli/bitbucket"
]

[tool.uv.sources]
# ... existing sources
<namespace>-<module> = { workspace = true }

[project]
dependencies = [
    # ... existing deps
    "<namespace>-<module>",
]
```

4) Install/sync (from devtools directory):

```bash
cd devtools
uv sync
```

Then use from anywhere:

```bash
aw <command> --help
```

**Example:** See `tinybots/cli/bitbucket/` for a complete Python plugin structure.

### Add a Node plugin

1) Create a package at `<domain>/cli/<name>/` with a `package.json`.
2) Add a `aw-plugin.yaml` marker in that folder:

```yaml
name: <command>
description: ...
bin: dist/cli.js
```

3) Build `dist/cli.js`, then generate the registry (from devtools directory):

```bash
cd devtools
pnpm -r build
uv run python scripts/generate-registry.py
```

Then use from anywhere:

```bash
aw <command> --help
```

## Lint

From the devtools directory:

```bash
cd devtools
uv run ruff check .
```

## Troubleshooting

- `aw` can't find a Node plugin: run `pnpm -r build` and `python scripts/generate-registry.py`, then check `aw-plugins.yaml`.
- No `uv` available: [install-all.sh](file:///Users/kai/work/k/dev/devtools/scripts/install-all.sh) falls back to `pip` (using `.venv`).
