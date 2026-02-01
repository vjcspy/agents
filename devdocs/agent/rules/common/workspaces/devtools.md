# DevTools Workspace

Workspace for development tools, CLI applications, and infrastructure serving AI agents and development workflow.

## Key Paths

| Purpose | Path |
|---------|------|
| **Source Code Root** | `devtools/` |
| **Documentation Root** | `devdocs/misc/devtools/` |
| **Global Overview** | `devdocs/misc/devtools/OVERVIEW.md` |
| **Plans** | `devdocs/misc/devtools/plans/` |

## Folder Structure

```
devtools/                           # Source code
├── common/                         # Shared tools across all domains
│   ├── cli/devtool/aweave/         # Python CLI packages (aw command)
│   │   ├── core/                   # CLI core
│   │   ├── docs/                   # aw docs
│   │   ├── debate/                 # aw debate
│   │   └── ...
│   └── debate-server/              # Node.js debate server
├── <domain>/                       # Domain-specific tools
│   ├── cli/                        # Domain CLI tools
│   └── local/                      # Local dev infrastructure
└── scripts/                        # Installation & utility scripts

devdocs/misc/devtools/              # Documentation
├── OVERVIEW.md                     # Global devtools overview (MUST read)
├── plans/                          # Implementation plans
│   └── [YYMMDD-name].md
├── common/                         # Package-level documentation
│   ├── cli/devtool/aweave/<pkg>/   # Python package docs
│   │   └── OVERVIEW.md
│   └── <package>/                  # Node package docs
│       └── OVERVIEW.md
└── <domain>/                       # Domain-specific docs
```

## Required Context Loading

**Loading Order — MUST follow sequentially:**

1. **Global Overview** (ALWAYS read first)
   ```
   devdocs/misc/devtools/OVERVIEW.md
   ```

2. **Package Overview** (if working on specific package)
   
   For Python CLI packages:
   ```
   devdocs/misc/devtools/common/cli/devtool/aweave/<package>/OVERVIEW.md
   ```
   
   For Node packages:
   ```
   devdocs/misc/devtools/common/<package>/OVERVIEW.md
   ```
   
   For domain-specific packages:
   ```
   devdocs/misc/devtools/<domain>/<package>/OVERVIEW.md
   ```

3. **Project Structure** (if need to understand folder structure)
   ```
   devdocs/agent/rules/common/project-structure.md
   ```

> **CRITICAL:** If Global Overview does not exist or is empty, **STOP** and ask user to provide context before proceeding.

## Path Detection Examples

| User Input | Package Type | Package Overview Path |
|------------|--------------|----------------------|
| `devtools/common/cli/devtool/aweave/debate/` | Python CLI | `devdocs/misc/devtools/common/cli/devtool/aweave/debate/OVERVIEW.md` |
| `devtools/common/debate-server/` | Node.js | `devdocs/misc/devtools/common/debate-server/OVERVIEW.md` |
| `devdocs/misc/devtools/plans/260131-debate-cli.md` | Plan file | Load Global OVERVIEW + related package OVERVIEW |

## CLI Development

### Python CLI (aw command)

- Entry point: `devtools/common/cli/devtool/aweave/core/main.py`
- Plugin discovery: `aw.plugins` entry points
- Run dev mode: `uv run aw <command>`

### Node Packages

- Build required: `npm run build` → `dist/cli.js`
- Plugin registry: `aw-plugins.yaml`

### Adding New Tools

> **SKILL:** When creating new CLI tool, **MUST** read and follow:
> `devdocs/agent/skills/common/devtools-builder/SKILL.md`

## Development Commands

| Task | Command |
|------|---------|
| Install all | `cd devtools && ./scripts/install-all.sh` |
| Sync Python deps | `cd devtools && uv sync` |
| Run CLI (dev) | `uv run aw <cmd>` |
| Lint Python | `uv run ruff check .` |
| Build Node package | `cd <package> && npm run build` |

## Working with Plans

Plans are stored at: `devdocs/misc/devtools/plans/`

Naming convention: `[YYMMDD-name].md`

When creating plans, use template: `devdocs/agent/templates/create-plan.md`
