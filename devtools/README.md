# Devtools (Unified CLI Monorepo)

A domain/project-oriented “dev tools” monorepo with **a single entrypoint**:

```bash
dt <subcommand> [...]
```

This repo supports:
- Python tools via **entry points** (`dt.plugins`) → runs in-process.
- Node tools via a **registry** (`dt-plugins.yaml`) + subprocess wrapper → `dt <node-plugin> ...`.

## Quickstart

### Install (recommended)

```bash
cd devtools
./scripts/install-all.sh
```

If you want to run without linking `~/.local/bin/dt`:

```bash
uv sync
uv run dt --help
```

### Generate plugin registry (for Node plugins)

```bash
uv run python scripts/generate-registry.py
```

The registry is written to `dt-plugins.yaml` at the repo root.

## Usage

```bash
dt --help
dt version
```

### Python plugin: confluence

```bash
dt confluence --help
dt confluence status
dt confluence sync <source> --dry-run
```

### Node plugin: foo

The Node plugin is only added to `dt` if the `bin` path in the registry exists (e.g. `nab/cli/foo/dist/cli.js`).

```bash
pnpm install
pnpm -r build
uv run python scripts/generate-registry.py

dt foo --help
dt foo build --watch
```

## Repository layout (short)

```
devtools/
  common/cli/devtool/          # Python package "dt" (root CLI)
  nab/cli/confluence/          # Python package (dt plugin)
  nab/cli/foo/                 # Node package (dt plugin)
  scripts/                     # install-all.sh, doctor.sh, generate-registry.py, ...
  pyproject.toml               # uv workspace root
  pnpm-workspace.yaml          # pnpm workspace
```

## Adding a new plugin

### Add a Python plugin

1) Create a package at `<domain>/cli/<name>/` with a `pyproject.toml`.
2) Register an entry point:

```toml
[project.entry-points."dt.plugins"]
<command> = "<module.path>:app"
```

3) Install/sync:

```bash
uv sync
dt <command> --help
```

Example: [confluence/pyproject.toml](file:///Users/kai/work/k/dev/devtools/nab/cli/confluence/pyproject.toml).

### Add a Node plugin

1) Create a package at `<domain>/cli/<name>/` with a `package.json`.
2) Add a `dt-plugin.yaml` marker in that folder:

```yaml
name: <command>
description: ...
bin: dist/cli.js
```

3) Build `dist/cli.js`, then generate the registry:

```bash
pnpm -r build
python scripts/generate-registry.py
dt <command> --help
```

## Lint

```bash
uv run ruff check .
```

## Troubleshooting

- `dt` can't find a Node plugin: run `pnpm -r build` and `python scripts/generate-registry.py`, then check `dt-plugins.yaml`.
- No `uv` available: [install-all.sh](file:///Users/kai/work/k/dev/devtools/scripts/install-all.sh) falls back to `pip` (using `.venv`).
