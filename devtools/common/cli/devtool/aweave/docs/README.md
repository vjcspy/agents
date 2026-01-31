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

### `aw docs create`

Tạo document mới (version 1).

```bash
aw docs create --summary "Design proposal" --file ./draft.md
aw docs create --summary "Quick note" --content "inline content"
aw docs create --summary "From pipe" --stdin < ./doc.md
aw docs create --summary "With metadata" --file ./doc.md --metadata '{"project": "debate"}'
```

**Options:**
| Option | Required | Description |
|--------|----------|-------------|
| `--summary, -s` | ✅ | Brief description |
| `--file, -f` | One of three | Path to content file |
| `--content` | One of three | Inline content string |
| `--stdin` | One of three | Read content from stdin |
| `--metadata` | ❌ | JSON object for custom data (default: `{}`) |
| `--format` | ❌ | `json` (default) or `markdown` |

**Output:**
```json
{
  "success": true,
  "content": [{"type": "json", "data": {"document_id": "550e8400-...", "version": 1, "id": "..."}}],
  "metadata": {"message": "Document created successfully"}
}
```

### `aw docs submit`

Submit version mới cho document đã tồn tại.

```bash
aw docs submit <document_id> --summary "Updated v2" --file ./draft.md
aw docs submit <document_id> --summary "v3" --content "new content" --metadata '{"status": "reviewed"}'
```

**Arguments:**
| Argument | Description |
|----------|-------------|
| `document_id` | UUID của document (từ `create` output) |

**Options:** Giống `create`

**Note:** Không thể submit vào document đã bị soft-deleted.

### `aw docs get`

Lấy document content. **Đây là command duy nhất hỗ trợ `--format plain`.**

```bash
aw docs get <document_id>                     # Latest version, JSON
aw docs get <document_id> --version 2         # Specific version
aw docs get <document_id> --format plain      # Raw content only (for piping)
aw docs get <document_id> --format markdown   # Human-readable
```

**Options:**
| Option | Description |
|--------|-------------|
| `--version, -v` | Specific version number (default: latest) |
| `--format` | `json` (default), `markdown`, or `plain` |

**Output (plain):**
```
# Your document content here...
```

**Output (json):**
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

### `aw docs list`

Liệt kê tất cả documents (latest version của mỗi doc).

```bash
aw docs list                        # All active documents
aw docs list --limit 10             # Limit results
aw docs list --include-deleted      # Include soft-deleted documents
```

**Options:**
| Option | Description |
|--------|-------------|
| `--limit, -l` | Maximum documents to return |
| `--include-deleted` | Show soft-deleted documents |
| `--format` | `json` (default) or `markdown` |

### `aw docs history`

Xem version history của một document.

```bash
aw docs history <document_id>
aw docs history <document_id> --limit 5
```

**Options:**
| Option | Description |
|--------|-------------|
| `--limit, -l` | Maximum versions to return |
| `--format` | `json` (default) or `markdown` |

### `aw docs export`

Export document content ra file (cho AI tiếp tục edit locally).

```bash
aw docs export <document_id> --output ./working.md
aw docs export <document_id> --version 1 --output ./old.md
```

**Options:**
| Option | Required | Description |
|--------|----------|-------------|
| `--output, -o` | ✅ | Output file path |
| `--version, -v` | ❌ | Specific version (default: latest) |
| `--format` | ❌ | `json` (default) or `markdown` |

### `aw docs delete`

Soft-delete document (marks all versions as deleted).

```bash
aw docs delete <document_id> --confirm
```

**Options:**
| Option | Required | Description |
|--------|----------|-------------|
| `--confirm` | ✅ | Must be provided to proceed |
| `--format` | ❌ | `json` (default) or `markdown` |

**Note:** Deleted documents can be seen with `aw docs list --include-deleted`.

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

| Command | Allowed Formats | Notes |
|---------|-----------------|-------|
| `create` | `json`, `markdown` | `plain` → error |
| `submit` | `json`, `markdown` | `plain` → error |
| `get` | `json`, `markdown`, `plain` | `plain` = raw content only |
| `list` | `json`, `markdown` | `plain` → error |
| `history` | `json`, `markdown` | `plain` → error |
| `export` | `json`, `markdown` | `plain` → error |
| `delete` | `json`, `markdown` | `plain` → error |

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
