# Document Store CLI (`aw docs`)

## Overview

CLI tool để lưu trữ và quản lý documents với **immutable version history**. Thiết kế cho AI agents trao đổi documents với nhau, nhưng cũng hữu ích cho human users.

**Key features:**
- Immutable versioning: Mỗi lần submit = version mới (không overwrite)
- Soft-delete: Documents không bị xóa vĩnh viễn, có thể recovery
- MCP-style response: Output JSON/Markdown chuẩn cho AI agents parse
- SQLite backend: Lightweight, không cần server

## Database Location

```
~/.aweave/docstore.db
```

Database được lưu ở user home directory, shared across tất cả projects.

**Override for testing:**
```bash
export AWEAVE_DB_PATH=/path/to/custom.db
```

## Commands

Available commands:
- `aw docs create` - Tạo document mới (version 1)
- `aw docs submit` - Submit version mới cho document đã tồn tại
- `aw docs get` - Lấy document content (default: plain text)
- `aw docs list` - Liệt kê tất cả documents
- `aw docs history` - Xem version history của một document
- `aw docs export` - Export document content ra file
- `aw docs delete` - Soft-delete document

> **Full command reference:** See [COMMANDS.md](./COMMANDS.md) for detailed options, arguments, and examples.

## AI Agent Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Agent Workflow                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Create new document                                     │
│     $ aw docs create --summary "Plan v1" --file ./plan.md   │
│     → Receives document_id                                  │
│                                                             │
│  2. Export to local file for editing                        │
│     $ aw docs export <doc_id> --output ./draft.md           │
│                                                             │
│  3. Edit locally (StrReplace, Write tools)                  │
│     [Modify ./draft.md as needed]                           │
│                                                             │
│  4. Submit new version when ready                           │
│     $ aw docs submit <doc_id> --summary "v2" --file ./draft.md │
│                                                             │
│  5. Other AI agent can get latest version                   │
│     $ aw docs get <doc_id>                                  │
│     $ aw docs get <doc_id> --format plain > ./local.md      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Error Handling

| Exit Code | Error Code | Description |
|-----------|------------|-------------|
| 1 | `FILE_NOT_FOUND` | Input file không tồn tại |
| 2 | `DOC_NOT_FOUND` | Document không tồn tại hoặc đã bị deleted |
| 2 | `VERSION_NOT_FOUND` | Version cụ thể không tồn tại |
| 3 | `DB_ERROR` | Database operation failed |
| 4 | `INVALID_INPUT` | Invalid arguments (e.g., both --file and --content, invalid JSON metadata, --format plain on unsupported command) |

**Error response format:**
```json
{
  "success": false,
  "error": {
    "code": "DOC_NOT_FOUND",
    "message": "Document '550e8400-...' not found",
    "suggestion": "Use 'aw docs list' to see available documents"
  }
}
```

## Metadata

Metadata là JSON object cho phép AI agents lưu arbitrary data:

```bash
# Store with metadata
aw docs create --summary "Debate motion" --file ./motion.md \
  --metadata '{"debate_id": "abc-123", "role": "proposer", "type": "MOTION"}'

# Metadata được lưu per-version (không merge với version cũ)
aw docs submit <doc_id> --summary "v2" --file ./motion.md \
  --metadata '{"debate_id": "abc-123", "role": "proposer", "type": "REVISE"}'
```

**Validation:**
- Must be valid JSON
- Must be an object/dict (not array, string, number, or null)

## Output Format Constraints

| Command | Default | Allowed Formats | Notes |
|---------|---------|-----------------|-------|
| `create` | `json` | `json`, `markdown` | `plain` → error |
| `submit` | `json` | `json`, `markdown` | `plain` → error |
| `get` | **`plain`** | `plain`, `json`, `markdown` | Raw content for AI agents |
| `list` | `json` | `json`, `markdown` | `plain` → error |
| `history` | `json` | `json`, `markdown` | `plain` → error |
| `export` | `json` | `json`, `markdown` | `plain` → error |
| `delete` | `json` | `json`, `markdown` | `plain` → error |

When `--format plain` is used on unsupported commands, error is returned as JSON.

## Soft-Delete Semantics

| Operation | Behavior with deleted document |
|-----------|-------------------------------|
| `get` | `DOC_NOT_FOUND` |
| `submit` | `DOC_NOT_FOUND` - cannot submit to deleted doc |
| `list` | Hidden by default, shown with `--include-deleted` ✅ |
| `history` | `DOC_NOT_FOUND` |
| `delete` | `DOC_NOT_FOUND` - already deleted |

## Concurrency

- Database uses WAL mode for better concurrent access
- Version allocation uses `BEGIN IMMEDIATE` transaction with retry on conflict
- Safe for multiple AI agents to submit versions concurrently
