# Document Store CLI - Commands Reference

> Full command reference for `aw docs`. For overview and concepts, see [OVERVIEW.md](./OVERVIEW.md).

## Commands

| Command | Description | Details |
|---------|-------------|---------|
| `aw docs create` | Tạo document mới (version 1) | [create.md](./commands/create.md) |
| `aw docs submit` | Submit version mới cho document đã tồn tại | [submit.md](./commands/submit.md) |
| `aw docs get` | Lấy document content (default: plain text) | [get.md](./commands/get.md) |
| `aw docs list` | Liệt kê tất cả documents | [list.md](./commands/list.md) |
| `aw docs history` | Xem version history của một document | [history.md](./commands/history.md) |
| `aw docs export` | Export document content ra file | [export.md](./commands/export.md) |
| `aw docs delete` | Soft-delete document | [delete.md](./commands/delete.md) |

## Quick Examples

```bash
# Create new document
aw docs create --summary "Plan v1" --file ./plan.md

# Submit new version
aw docs submit <doc_id> --summary "v2" --file ./plan.md

# Get document content (plain text for AI)
aw docs get <doc_id>

# List all documents
aw docs list

# View version history
aw docs history <doc_id>

# Export to local file
aw docs export <doc_id> --output ./working.md

# Soft-delete
aw docs delete <doc_id> --confirm
```
