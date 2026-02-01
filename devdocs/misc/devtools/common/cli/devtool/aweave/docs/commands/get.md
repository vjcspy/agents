# `aw docs get`

Lấy document content. **Default là `plain` (raw text) để AI Agent đọc trực tiếp.**

## Usage

```bash
aw docs get <document_id>                     # Latest version, raw content (default)
aw docs get <document_id> --version 2         # Specific version
aw docs get <document_id> --format json       # With metadata (MCPResponse)
aw docs get <document_id> --format markdown   # Human-readable
```

## Arguments

| Argument | Description |
|----------|-------------|
| `document_id` | UUID của document |

## Options

| Option | Description |
|--------|-------------|
| `--version, -v` | Specific version number (default: latest) |
| `--format` | `plain` (default), `json`, or `markdown` |

## Output

**Plain (default):**
```
# Your document content here...

No JSON encoding, no escape characters.
AI Agent reads directly like a file.
```

**JSON (when metadata needed):**
```json
{
  "success": true,
  "content": [{
    "type": "json",
    "data": {
      "id": "...",
      "document_id": "550e8400-...",
      "summary": "Updated v2",
      "content": "# Your document...",
      "version": 2,
      "metadata": {"status": "reviewed"},
      "created_at": "2026-01-31T10:30:00+00:00"
    }
  }]
}
```
