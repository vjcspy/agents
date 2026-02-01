# `aw docs list`

Liệt kê tất cả documents (latest version của mỗi doc).

## Usage

```bash
aw docs list                        # All active documents
aw docs list --limit 10             # Limit results
aw docs list --include-deleted      # Include soft-deleted documents
```

## Options

| Option | Description |
|--------|-------------|
| `--limit, -l` | Maximum documents to return |
| `--include-deleted` | Show soft-deleted documents |
| `--format` | `json` (default) or `markdown` |
