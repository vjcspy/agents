# Devtools (Unified CLI Monorepo)

A domain/project-oriented “dev tools” monorepo with **a single entrypoint**:

```bash
aw <subcommand> [...]
```

This repo supports:
- Python tools via **entry points** (`aw.plugins`) → runs in-process.
- Node tools via a **registry** (`aw-plugins.yaml`) + subprocess wrapper → `aw <node-plugin> ...`.

## Quickstart

### Install (recommended)

```bash
cd devtools
./scripts/install-all.sh
```

If you want to run without linking `~/.local/bin/aw`:

```bash
uv sync
uv run aw --help
```

### Generate plugin registry (for Node plugins)

```bash
uv run python scripts/generate-registry.py
```

The registry is written to `aw-plugins.yaml` at the repo root.

## Usage

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

```bash
pnpm install
pnpm -r build
uv run python scripts/generate-registry.py

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

1) Create a package at `<domain>/cli/<name>/` with a `pyproject.toml`.
2) Register an entry point:

```toml
[project.entry-points."aw.plugins"]
<command> = "<module.path>:app"
```

3) Install/sync:

```bash
uv sync
aw <command> --help
```

Example: [confluence/pyproject.toml](file:///Users/kai/work/k/dev/devtools/nab/cli/confluence/pyproject.toml).

### Add a Node plugin

1) Create a package at `<domain>/cli/<name>/` with a `package.json`.
2) Add a `aw-plugin.yaml` marker in that folder:

```yaml
name: <command>
description: ...
bin: dist/cli.js
```

3) Build `dist/cli.js`, then generate the registry:

```bash
pnpm -r build
python scripts/generate-registry.py
aw <command> --help
```

## Lint

```bash
uv run ruff check .
```

## Troubleshooting

- `aw` can't find a Node plugin: run `pnpm -r build` and `python scripts/generate-registry.py`, then check `aw-plugins.yaml`.
- No `uv` available: [install-all.sh](file:///Users/kai/work/k/dev/devtools/scripts/install-all.sh) falls back to `pip` (using `.venv`).
