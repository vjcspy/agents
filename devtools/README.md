# Devtools

Unified CLI monorepo với single entrypoint: `aw <subcommand>`

## Quickstart

```bash
cd devtools
./scripts/install-all.sh   # Install + link to ~/.local/bin/aw
```

Sau khi install, chạy `aw --help` từ bất kỳ đâu.

## Development Mode

```bash
cd devtools
uv sync
uv run aw --help
```

## Available Tools

See **[CLI_TOOLS.md](CLI_TOOLS.md)** for available commands.

## Documentation

- **Full Overview:** `devdocs/misc/devtools/OVERVIEW.md`
- **Adding plugins:** See OVERVIEW.md → "Development Workflow"
