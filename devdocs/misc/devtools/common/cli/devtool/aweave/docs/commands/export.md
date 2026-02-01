# `aw docs export`

Export document content ra file (cho AI tiếp tục edit locally).

## Usage

```bash
aw docs export <document_id> --output ./working.md
aw docs export <document_id> --version 1 --output ./old.md
```

## Arguments

| Argument | Description |
|----------|-------------|
| `document_id` | UUID của document |

## Options

| Option | Required | Description |
|--------|----------|-------------|
| `--output, -o` | ✅ | Output file path |
| `--version, -v` | ❌ | Specific version (default: latest) |
| `--format` | ❌ | `json` (default) or `markdown` |
