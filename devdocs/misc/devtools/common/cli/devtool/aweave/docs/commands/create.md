# `aw docs create`

Tạo document mới (version 1).

## Usage

```bash
aw docs create --summary "Design proposal" --file ./draft.md
aw docs create --summary "Quick note" --content "inline content"
aw docs create --summary "From pipe" --stdin < ./doc.md
aw docs create --summary "With metadata" --file ./doc.md --metadata '{"project": "debate"}'
```

## Options

| Option | Required | Description |
|--------|----------|-------------|
| `--summary, -s` | ✅ | Brief description |
| `--file, -f` | One of three | Path to content file |
| `--content` | One of three | Inline content string |
| `--stdin` | One of three | Read content from stdin |
| `--metadata` | ❌ | JSON object for custom data (default: `{}`) |
| `--format` | ❌ | `json` (default) or `markdown` |

## Output

```json
{
  "success": true,
  "content": [{"type": "json", "data": {"document_id": "550e8400-...", "version": 1, "id": "..."}}],
  "metadata": {"message": "Document created successfully"}
}
```
