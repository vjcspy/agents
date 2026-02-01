# `aw docs submit`

Submit version mới cho document đã tồn tại.

## Usage

```bash
aw docs submit <document_id> --summary "Updated v2" --file ./draft.md
aw docs submit <document_id> --summary "v3" --content "new content" --metadata '{"status": "reviewed"}'
```

## Arguments

| Argument | Description |
|----------|-------------|
| `document_id` | UUID của document (từ `create` output) |

## Options

Giống [`create`](./create.md):
- `--summary, -s` (required)
- `--file, -f` / `--content` / `--stdin` (one required)
- `--metadata` (optional)
- `--format` (optional)

## Notes

- Không thể submit vào document đã bị soft-deleted
- Mỗi submit tạo version mới (immutable, không overwrite)
