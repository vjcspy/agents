# `aw docs delete`

Soft-delete document (marks all versions as deleted).

## Usage

```bash
aw docs delete <document_id> --confirm
```

## Arguments

| Argument | Description |
|----------|-------------|
| `document_id` | UUID của document |

## Options

| Option | Required | Description |
|--------|----------|-------------|
| `--confirm` | ✅ | Must be provided to proceed |
| `--format` | ❌ | `json` (default) or `markdown` |

## Notes

- Soft-delete: document không bị xóa vĩnh viễn
- Deleted documents can be seen with `aw docs list --include-deleted`
- Cannot submit new versions to deleted documents
