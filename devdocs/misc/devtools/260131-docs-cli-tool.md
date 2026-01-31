# 📋 [DEVTOOLS-DOCS: 2026-01-31] - Document Store CLI Tool

## References

- `devtools/README.md` - Devtools monorepo structure & plugin system
- `devtools/common/cli/devtool/aweave/` - Existing aweave package structure
- `devtools/common/cli/devtool/aweave/mcp/response.py` - MCPResponse format (MUST follow)
- `devtools/tinybots/cli/bitbucket/` - Reference CLI plugin implementation
- `devdocs/misc/devtools/debate.md` - Parent project context (Debate ecosystem)

## User Requirements

1. Lưu trữ document dạng text (chủ yếu là markdown)
2. SQLite database với versioning support
3. CLI commands để AI Agent dễ sử dụng
4. Mỗi lần submit tạo version mới (immutable history)
5. Metadata column (JSON) để AI agent lưu arbitrary data

## 🎯 Objective

Xây dựng **`aw docs`** CLI tool để lưu trữ và quản lý documents với versioning, phục vụ cho việc AI agents trao đổi documents với nhau.

---

## 📐 Spec / Decisions

### 1. Database Location

**Decision**: Lưu ở **user home directory** (system-level, không trong repo)

**Path**: `~/.aweave/docstore.db`

**Rationale**:
- Không làm bẩn repo với database file
- Documents được share across tất cả projects
- Không cần add `.aweave/` vào `.gitignore`
- Consistent với convention của các tools khác (như `~/.config/`, `~/.local/`)

**Override for testing**: `AWEAVE_DB_PATH` env var

```python
def get_db_path() -> Path:
    """Get docstore database path."""
    # 1. Env var for testing
    if env_path := os.environ.get("AWEAVE_DB_PATH"):
        return Path(env_path)
    
    # 2. Default: ~/.aweave/docstore.db
    db_dir = Path.home() / ".aweave"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "docstore.db"
```

**DB Path**: `~/.aweave/docstore.db`

### 2. Timestamp Format

- **Format**: UTC ISO-8601 with timezone (`2026-01-31T10:30:00+00:00`)
- **Storage**: TEXT in SQLite (ISO string)
- **Generation**: `datetime.now(timezone.utc).isoformat()`

### 3. Delete Policy

**Decision**: **Soft-delete with tombstone**

- Documents are NEVER physically deleted
- Add `deleted_at` column (NULL = active, timestamp = deleted)
- `list` và `get` commands filter out deleted documents by default
- Add `--include-deleted` flag for recovery scenarios
- **Rationale**: Preserves immutable history / audit trail

### 4. Metadata Policy

**Decision**: **Full replace on each version**

- Mỗi version có `metadata` riêng
- Submit mới = cung cấp full metadata mới (không merge với version cũ)
- AI agent muốn merge thì `get` version cũ, merge locally, rồi submit
- **Rationale**: Đơn giản, predictable, tránh merge conflicts

### 5. Content Input Rules

**Decision**: `--file` và `--content` mutually exclusive, exactly one required

```
--file <path>     Read content from file (relative to cwd)
--content <text>  Inline content string
--stdin           Read content from stdin (for piping)
```

**Validation**: Error if none provided, error if multiple provided.

### 6. Output Format Convention

**Follow MCPResponse** (from `aweave/mcp/response.py`):

```python
# Success response
MCPResponse(
    success=True,
    content=[MCPContent(type=ContentType.JSON, data={...})],
    metadata={"document_id": "...", "version": 1}
)

# Error response  
MCPResponse(
    success=False,
    error=MCPError(
        code="DOC_NOT_FOUND",
        message="Document 'abc' not found",
        suggestion="Use 'aw docs list' to see available documents"
    )
)
```

**Output formats**:
- `--format json` (default): `response.to_json()`
- `--format markdown`: `response.to_markdown()`
- `--format plain`: Content only (for `get` command - raw document text)

### 7. Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error (invalid args, file not found) |
| 2 | Document not found |
| 3 | Database error |
| 4 | Validation error (e.g., both --file and --content) |

### 8. Error Codes (in MCPError.code)

| Code | Description |
|------|-------------|
| `DOC_NOT_FOUND` | Document ID does not exist (or soft-deleted) |
| `VERSION_NOT_FOUND` | Specific version does not exist |
| `INVALID_INPUT` | Invalid arguments, content, or format |
| `DB_ERROR` | Database operation failed |
| `FILE_NOT_FOUND` | Input file does not exist |

### 9. Output Format Constraints

| Command | Allowed Formats | Notes |
|---------|-----------------|-------|
| `create` | `json`, `markdown` | `plain` → `INVALID_INPUT` |
| `submit` | `json`, `markdown` | `plain` → `INVALID_INPUT` |
| `get` | `json`, `markdown`, `plain` | `plain` = raw content only |
| `list` | `json`, `markdown` | `plain` → `INVALID_INPUT` |
| `history` | `json`, `markdown` | `plain` → `INVALID_INPUT` |
| `export` | `json`, `markdown` | Output to stdout, file written separately |
| `delete` | `json`, `markdown` | `plain` → `INVALID_INPUT` |

### 10. Metadata Validation

- `--metadata` must parse to a **JSON object** (dict)
- If parsed value is `list`, `string`, `number`, `null` → `INVALID_INPUT`
- Empty object `{}` is valid (default)

### 11. Soft-Delete Semantics

| Operation | Behavior with deleted document |
|-----------|-------------------------------|
| `get` | `DOC_NOT_FOUND` (no `--include-deleted` flag yet) |
| `submit` | `DOC_NOT_FOUND` - cannot submit to deleted doc |
| `list` | Hidden by default, **shown with `--include-deleted`** ✅ |
| `history` | `DOC_NOT_FOUND` (no `--include-deleted` flag yet) |
| `delete` | `DOC_NOT_FOUND` - already deleted |

**Note**: `list` already supports `--include-deleted`. For `get` and `history`, this flag is a future enhancement.

### 12. Error Output Format

When `--format plain` is used on commands that don't support it, the error response is **always returned as JSON** (not markdown). This ensures errors are parseable even when the requested format is invalid.

---

### ⚠️ Key Considerations

1. **Versioning over Update**: Mỗi lần submit = version mới. Không có update-in-place. Điều này đảm bảo:
   - Traceability: Xem lại history bất cứ lúc nào
   - Conflict-free: Nhiều agents có thể submit mà không conflict
   - Audit trail: Biết ai submit gì, khi nào

2. **User-level DB**: Database nằm ở `~/.aweave/docstore.db`
   - Shared across tất cả projects
   - Không làm bẩn repo
   - Env var `AWEAVE_DB_PATH` override cho testing

3. **AI-friendly Output**: 
   - Default: MCPResponse JSON format (consistent với các CLI khác)
   - Markdown option cho human readability
   - Plain text option cho raw content
   - Structured error messages với actionable suggestions

4. **Metadata Flexibility**: JSON column cho phép AI agents lưu:
   - `debate_id`, `argument_id` (cho Debate system)
   - `tags`, `category` (cho organization)
   - Custom fields tùy use case

5. **Concurrency Safety**: Version allocation sử dụng transaction với retry để handle concurrent submits

---

## 🔄 Implementation Plan

### Phase 1: Analysis & Preparation

- [x] **Define final database schema**
  - **Outcome**: Single table `document_versions` + `schema_meta` for versioning, với soft-delete

- [x] **Define CLI command interface**
  - **Outcome**: Full command signatures với MCPResponse output

- [x] **Identify dependencies**
  - **Outcome**: Không cần thêm dependency mới (dùng stdlib sqlite3, dataclasses)

---

### Phase 2: Implementation (File/Code Structure)

```
devtools/common/cli/devtool/aweave/
├── __init__.py                    # ✅ EXISTS
├── core/                          # ✅ EXISTS - Main CLI
├── http/                          # ✅ EXISTS
├── mcp/                           # ✅ EXISTS (MCPResponse, MCPError, MCPContent)
└── docs/                          # 🚧 TODO - Document Store module
    ├── __init__.py                # Module init, export cli app
    ├── cli.py                     # Typer CLI commands (follow bitbucket pattern)
    └── db.py                      # SQLite database operations + path resolution
```

**Notes**:
- **Không cần models.py riêng** - dùng `dict` + MCPResponse là đủ
- **Không cần workspace.py riêng** - logic đơn giản, inline trong db.py
- **Dùng dataclasses nếu cần** - từ stdlib, không thêm dependency

**Database location**: `~/.aweave/docstore.db` (user home directory)

---

### Phase 3: Detailed Implementation Steps

#### Step 1: Database Schema Design

**Design: Single table `document_versions` + `schema_meta`**

```sql
-- Enable WAL mode for better concurrency (multiple agents)
PRAGMA journal_mode=WAL;

-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
INSERT OR IGNORE INTO schema_meta (key, value) VALUES ('version', '1');

-- Table: document_versions (stores all versions, immutable)
CREATE TABLE IF NOT EXISTS document_versions (
    id TEXT PRIMARY KEY,              -- UUID for each version record
    document_id TEXT NOT NULL,        -- Logical document ID (groups versions)
    summary TEXT NOT NULL,            -- Brief description
    content TEXT NOT NULL,            -- Document content (markdown)
    version INTEGER NOT NULL,         -- Version number (1, 2, 3...)
    metadata TEXT DEFAULT '{}',       -- JSON metadata (must be object/dict)
    created_at TEXT NOT NULL,         -- ISO-8601 UTC timestamp
    deleted_at TEXT DEFAULT NULL,     -- Soft-delete tombstone (NULL = active)
    
    UNIQUE(document_id, version)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_doc_id ON document_versions(document_id);
CREATE INDEX IF NOT EXISTS idx_doc_latest ON document_versions(document_id, version DESC);
CREATE INDEX IF NOT EXISTS idx_created_at ON document_versions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_active ON document_versions(document_id) WHERE deleted_at IS NULL;
```

**Notes:**
- `PRAGMA journal_mode=WAL` reduces lock contention when multiple agents write
- `idx_active` is a partial index for fast lookup of non-deleted documents

**Query Strategy:**

```sql
-- Get latest version of a document (excluding deleted)
SELECT * FROM document_versions 
WHERE document_id = ? AND deleted_at IS NULL
ORDER BY version DESC LIMIT 1;

-- List all documents (latest version each, excluding deleted)
SELECT dv.* FROM document_versions dv
INNER JOIN (
    SELECT document_id, MAX(version) as max_version
    FROM document_versions 
    WHERE deleted_at IS NULL
    GROUP BY document_id
) latest ON dv.document_id = latest.document_id AND dv.version = latest.max_version
WHERE dv.deleted_at IS NULL
ORDER BY dv.created_at DESC;

-- Get version history of a document
SELECT id, version, summary, created_at FROM document_versions
WHERE document_id = ? AND deleted_at IS NULL
ORDER BY version DESC;
```

**Concurrency handling for version allocation:**

```python
def submit_version(document_id: str, summary: str, content: str, metadata: dict) -> dict:
    """Submit new version with retry on conflict."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with sqlite3.connect(db_path) as conn:
                conn.execute("BEGIN IMMEDIATE")  # Lock early
                
                # Get next version number
                cursor = conn.execute(
                    "SELECT COALESCE(MAX(version), 0) + 1 FROM document_versions WHERE document_id = ?",
                    (document_id,)
                )
                next_version = cursor.fetchone()[0]
                
                # Insert new version
                version_id = str(uuid.uuid4())
                conn.execute(
                    """INSERT INTO document_versions 
                       (id, document_id, summary, content, version, metadata, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (version_id, document_id, summary, content, next_version, 
                     json.dumps(metadata), datetime.now(timezone.utc).isoformat())
                )
                conn.commit()
                return {"document_id": document_id, "version": next_version, "id": version_id}
        except sqlite3.IntegrityError:
            if attempt < max_retries - 1:
                continue  # Retry
            raise
```

#### Step 2: CLI Commands Specification

| Command | Description | Arguments/Options |
|---------|-------------|-------------------|
| `aw docs create` | Tạo document mới (v1) | `--summary`, `--file`/`--content`/`--stdin`, `--metadata` |
| `aw docs submit` | Submit version mới | `<document_id>`, `--summary`, `--file`/`--content`/`--stdin`, `--metadata` |
| `aw docs get` | Lấy document (stdout) | `<document_id>`, `--version`, `--format` |
| `aw docs list` | List tất cả documents | `--limit`, `--format`, `--include-deleted` |
| `aw docs history` | Xem version history | `<document_id>`, `--limit`, `--format` |
| `aw docs export` | Export to file | `<document_id>`, `--version`, `--output` (required) |
| `aw docs delete` | Soft-delete document | `<document_id>`, `--confirm` |

**Semantic distinction:**
- `get` → stdout only (for piping, AI parsing)
- `export` → write to file (for AI to continue editing locally)

**Command Details:**

```bash
# CREATE - Tạo document mới, trả về document_id (UUID)
aw docs create --summary "Design proposal" --file ./draft.md
aw docs create --summary "Quick note" --content "inline content here"
aw docs create --summary "With meta" --file ./doc.md --metadata '{"debate_id": "abc"}'
cat doc.md | aw docs create --summary "From pipe" --stdin

# Output (MCPResponse JSON):
{
  "success": true,
  "content": [
    {
      "type": "json",
      "data": {
        "document_id": "550e8400-e29b-41d4-a716-446655440000",
        "version": 1
      }
    }
  ],
  "metadata": {
    "message": "Document created successfully"
  }
}

# SUBMIT - Submit version mới cho document đã tồn tại
aw docs submit 550e8400-e29b-41d4-a716-446655440000 --summary "Updated v2" --file ./draft.md
aw docs submit <doc_id> --summary "v3" --content "new content" --metadata '{"status": "reviewed"}'

# Output (MCPResponse JSON):
{
  "success": true,
  "content": [
    {
      "type": "json", 
      "data": {
        "document_id": "550e8400-e29b-41d4-a716-446655440000",
        "version": 2
      }
    }
  ],
  "metadata": {
    "message": "Version 2 submitted successfully"
  }
}

# GET - Lấy document (stdout only)
aw docs get <document_id>                     # Latest, MCPResponse JSON
aw docs get <document_id> --version 1         # Specific version
aw docs get <document_id> --format plain      # Content only (raw text)
aw docs get <document_id> --format markdown   # MCPResponse markdown

# Output (--format json, default):
{
  "success": true,
  "content": [
    {
      "type": "json",
      "data": {
        "id": "record-uuid",
        "document_id": "550e8400-e29b-41d4-a716-446655440000",
        "summary": "Updated v2",
        "content": "# Document content...",
        "version": 2,
        "metadata": {"status": "reviewed"},
        "created_at": "2026-01-31T10:30:00+00:00"
      }
    }
  ]
}

# Output (--format plain):
# Document content...
(raw content only, no JSON wrapper - useful for piping)

# LIST - Liệt kê documents (latest version của mỗi doc)
aw docs list                        # All active documents
aw docs list --limit 10             # Limit results
aw docs list --include-deleted      # Include soft-deleted
aw docs list --format markdown      # Human-readable

# Output (MCPResponse JSON):
{
  "success": true,
  "content": [
    {
      "type": "json",
      "data": {
        "documents": [
          {"document_id": "...", "summary": "...", "version": 3, "created_at": "..."},
          {"document_id": "...", "summary": "...", "version": 1, "created_at": "..."}
        ]
      }
    }
  ],
  "total_count": 2
}

# HISTORY - Version history của 1 document
aw docs history <document_id>
aw docs history <document_id> --limit 5

# Output (MCPResponse JSON):
{
  "success": true,
  "content": [
    {
      "type": "json",
      "data": {
        "document_id": "...",
        "versions": [
          {"version": 3, "summary": "...", "created_at": "..."},
          {"version": 2, "summary": "...", "created_at": "..."},
          {"version": 1, "summary": "...", "created_at": "..."}
        ]
      }
    }
  ],
  "total_count": 3
}

# EXPORT - Export content to file (cho AI tiếp tục edit locally)
aw docs export <document_id> --output ./working.md           # Latest version
aw docs export <document_id> --version 1 --output ./old.md   # Specific version

# Output (MCPResponse JSON to stdout, file written separately):
{
  "success": true,
  "content": [{"type": "text", "text": "Exported to ./working.md"}],
  "metadata": {"path": "./working.md", "version": 3}
}

# DELETE - Soft-delete document (marks all versions as deleted)
aw docs delete <document_id> --confirm

# Output (MCPResponse JSON):
{
  "success": true,
  "content": [{"type": "text", "text": "Document soft-deleted"}],
  "metadata": {"document_id": "...", "versions_affected": 3}
}

# Error example (document not found):
{
  "success": false,
  "error": {
    "code": "DOC_NOT_FOUND",
    "message": "Document '550e8400...' not found",
    "suggestion": "Use 'aw docs list' to see available documents"
  }
}
```

#### Step 3: Implementation Tasks

**3.1. Create module structure** 🚧

```python
# aweave/docs/__init__.py
from .cli import app

__all__ = ["app"]
```

**3.2. Implement db.py - get_db_path()** 🚧

```python
"""Database path resolution."""
import os
from pathlib import Path


def get_db_path() -> Path:
    """
    Get docstore database path.
    
    Location: ~/.aweave/docstore.db (user home directory)
    Override: AWEAVE_DB_PATH env var (for testing)
    """
    # 1. Env var for testing
    if env_path := os.environ.get("AWEAVE_DB_PATH"):
        return Path(env_path)
    
    # 2. Default: ~/.aweave/docstore.db
    db_dir = Path.home() / ".aweave"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "docstore.db"
```

**Note**: Không cần file `workspace.py` riêng - logic đơn giản, inline trong `db.py`.

**3.3. Implement db.py** 🚧

```python
"""SQLite database operations for docstore."""
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Schema version for migrations
SCHEMA_VERSION = "1"


def get_db_path() -> Path:
    """
    Get docstore database path.
    
    Location: ~/.aweave/docstore.db (user home directory)
    Override: AWEAVE_DB_PATH env var (for testing)
    """
    if env_path := os.environ.get("AWEAVE_DB_PATH"):
        return Path(env_path)
    
    db_dir = Path.home() / ".aweave"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "docstore.db"


def init_db() -> sqlite3.Connection:
    """Initialize database, create tables if not exist."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # Enable WAL mode for better concurrency
    conn.execute("PRAGMA journal_mode=WAL")
    
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS schema_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        
        CREATE TABLE IF NOT EXISTS document_versions (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            summary TEXT NOT NULL,
            content TEXT NOT NULL,
            version INTEGER NOT NULL,
            metadata TEXT DEFAULT '{}',
            created_at TEXT NOT NULL,
            deleted_at TEXT DEFAULT NULL,
            UNIQUE(document_id, version)
        );
        
        CREATE INDEX IF NOT EXISTS idx_doc_id ON document_versions(document_id);
        CREATE INDEX IF NOT EXISTS idx_doc_latest ON document_versions(document_id, version DESC);
        CREATE INDEX IF NOT EXISTS idx_created_at ON document_versions(created_at DESC);
    """)
    
    # Partial index for active documents (SQLite 3.8.0+)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_active 
        ON document_versions(document_id) WHERE deleted_at IS NULL
    """)
    
    conn.execute(
        "INSERT OR IGNORE INTO schema_meta (key, value) VALUES (?, ?)",
        ("version", SCHEMA_VERSION)
    )
    conn.commit()
    return conn


def create_document(summary: str, content: str, metadata: dict[str, Any]) -> dict[str, Any]:
    """Create new document (version 1), return document_id."""
    conn = init_db()
    document_id = str(uuid.uuid4())
    version_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    
    conn.execute(
        """INSERT INTO document_versions 
           (id, document_id, summary, content, version, metadata, created_at)
           VALUES (?, ?, ?, ?, 1, ?, ?)""",
        (version_id, document_id, summary, content, json.dumps(metadata), created_at)
    )
    conn.commit()
    conn.close()
    
    return {"document_id": document_id, "version": 1, "id": version_id}


def submit_version(
    document_id: str, summary: str, content: str, metadata: dict[str, Any]
) -> dict[str, Any]:
    """Add new version to existing document with retry on conflict."""
    max_retries = 3
    
    for attempt in range(max_retries):
        conn = None
        try:
            conn = init_db()
            conn.execute("BEGIN IMMEDIATE")
            
            # Check document exists (and not deleted)
            cursor = conn.execute(
                "SELECT 1 FROM document_versions WHERE document_id = ? AND deleted_at IS NULL LIMIT 1",
                (document_id,)
            )
            if not cursor.fetchone():
                return None  # Document not found or deleted
            
            # Get next version
            cursor = conn.execute(
                "SELECT COALESCE(MAX(version), 0) + 1 FROM document_versions WHERE document_id = ?",
                (document_id,)
            )
            next_version = cursor.fetchone()[0]
            
            # Insert
            version_id = str(uuid.uuid4())
            created_at = datetime.now(timezone.utc).isoformat()
            
            conn.execute(
                """INSERT INTO document_versions 
                   (id, document_id, summary, content, version, metadata, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (version_id, document_id, summary, content, next_version, 
                 json.dumps(metadata), created_at)
            )
            conn.commit()
            
            return {"document_id": document_id, "version": next_version, "id": version_id}
            
        except sqlite3.IntegrityError:
            if attempt < max_retries - 1:
                continue  # Retry on version conflict
            raise
        finally:
            if conn:
                conn.close()


def get_document(
    document_id: str, version: int | None = None, include_deleted: bool = False
) -> dict[str, Any] | None:
    """Get document by ID, optionally specific version."""
    conn = init_db()
    
    if version:
        query = "SELECT * FROM document_versions WHERE document_id = ? AND version = ?"
        params = (document_id, version)
    else:
        query = """SELECT * FROM document_versions 
                   WHERE document_id = ? ORDER BY version DESC LIMIT 1"""
        params = (document_id,)
    
    if not include_deleted:
        query = query.replace("WHERE", "WHERE deleted_at IS NULL AND")
    
    cursor = conn.execute(query, params)
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    return {
        "id": row["id"],
        "document_id": row["document_id"],
        "summary": row["summary"],
        "content": row["content"],
        "version": row["version"],
        "metadata": json.loads(row["metadata"]),
        "created_at": row["created_at"],
    }


def list_documents(
    limit: int | None = None, include_deleted: bool = False
) -> tuple[list[dict[str, Any]], int]:
    """List all documents (latest version each)."""
    conn = init_db()
    
    deleted_filter = "" if include_deleted else "WHERE deleted_at IS NULL"
    inner_filter = "" if include_deleted else "WHERE deleted_at IS NULL"
    
    query = f"""
        SELECT dv.* FROM document_versions dv
        INNER JOIN (
            SELECT document_id, MAX(version) as max_version
            FROM document_versions {inner_filter}
            GROUP BY document_id
        ) latest ON dv.document_id = latest.document_id AND dv.version = latest.max_version
        {deleted_filter}
        ORDER BY dv.created_at DESC
    """
    
    if limit:
        query += f" LIMIT {limit}"
    
    cursor = conn.execute(query)
    rows = cursor.fetchall()
    
    # Get total count
    count_cursor = conn.execute(
        f"SELECT COUNT(DISTINCT document_id) FROM document_versions {deleted_filter}"
    )
    total = count_cursor.fetchone()[0]
    conn.close()
    
    documents = [
        {
            "document_id": row["document_id"],
            "summary": row["summary"],
            "version": row["version"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]
    
    return documents, total


def get_history(
    document_id: str, limit: int | None = None
) -> tuple[list[dict[str, Any]], int]:
    """Get version history of a document."""
    conn = init_db()
    
    query = """SELECT id, version, summary, created_at FROM document_versions
               WHERE document_id = ? AND deleted_at IS NULL
               ORDER BY version DESC"""
    
    if limit:
        query += f" LIMIT {limit}"
    
    cursor = conn.execute(query, (document_id,))
    rows = cursor.fetchall()
    
    count_cursor = conn.execute(
        "SELECT COUNT(*) FROM document_versions WHERE document_id = ? AND deleted_at IS NULL",
        (document_id,)
    )
    total = count_cursor.fetchone()[0]
    conn.close()
    
    versions = [
        {"version": row["version"], "summary": row["summary"], "created_at": row["created_at"]}
        for row in rows
    ]
    
    return versions, total


def soft_delete_document(document_id: str) -> int:
    """Soft-delete document and all its versions. Returns count of affected versions."""
    conn = init_db()
    deleted_at = datetime.now(timezone.utc).isoformat()
    
    cursor = conn.execute(
        "UPDATE document_versions SET deleted_at = ? WHERE document_id = ? AND deleted_at IS NULL",
        (deleted_at, document_id)
    )
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    return affected
```

**3.4. Implement cli.py** 🚧

```python
"""Document Store CLI commands."""
import json
import sys
from enum import Enum
from pathlib import Path
from typing import Annotated

import typer

from aweave.mcp.response import MCPContent, MCPError, MCPResponse, ContentType
from . import db

app = typer.Typer(name="docs", help="Document storage for AI agents")


class OutputFormat(str, Enum):
    """Output format options."""
    json = "json"
    markdown = "markdown"
    plain = "plain"


def _output(response: MCPResponse, fmt: OutputFormat) -> None:
    """Output response in specified format."""
    if fmt == OutputFormat.json:
        typer.echo(response.to_json())
    else:  # markdown
        typer.echo(response.to_markdown())


def _output_plain(content: str) -> None:
    """Output plain text content (for get command only)."""
    typer.echo(content)


def _error_response(code: str, message: str, suggestion: str | None = None) -> MCPResponse:
    """Create error response."""
    return MCPResponse(
        success=False,
        error=MCPError(code=code, message=message, suggestion=suggestion)
    )


def _validate_format_no_plain(fmt: OutputFormat, command: str) -> MCPResponse | None:
    """Validate that plain format is not used for commands that don't support it."""
    if fmt == OutputFormat.plain:
        return _error_response(
            "INVALID_INPUT",
            f"--format plain is not supported for '{command}' command",
            "Use --format json or --format markdown"
        )
    return None


def _parse_metadata(metadata_str: str) -> tuple[dict | None, MCPResponse | None]:
    """Parse and validate metadata JSON. Must be an object/dict."""
    try:
        parsed = json.loads(metadata_str)
    except json.JSONDecodeError as e:
        return None, _error_response(
            "INVALID_INPUT",
            f"Invalid JSON in --metadata: {e}",
            "Provide valid JSON object, e.g. '{\"key\": \"value\"}'"
        )
    
    if not isinstance(parsed, dict):
        return None, _error_response(
            "INVALID_INPUT",
            f"--metadata must be a JSON object, got {type(parsed).__name__}",
            "Provide JSON object, e.g. '{\"key\": \"value\"}', not array/string/number"
        )
    
    return parsed, None


def _read_content(
    file: Path | None, content: str | None, stdin: bool
) -> tuple[str | None, MCPResponse | None]:
    """Read content from file, inline, or stdin. Returns (content, error_response)."""
    sources = sum([file is not None, content is not None, stdin])
    
    if sources == 0:
        return None, _error_response(
            "INVALID_INPUT",
            "No content provided",
            "Use --file, --content, or --stdin to provide content"
        )
    
    if sources > 1:
        return None, _error_response(
            "INVALID_INPUT",
            "Multiple content sources provided",
            "Use only one of --file, --content, or --stdin"
        )
    
    if stdin:
        return sys.stdin.read(), None
    
    if file:
        if not file.exists():
            return None, _error_response(
                "FILE_NOT_FOUND",
                f"File not found: {file}",
                "Check the file path and try again"
            )
        return file.read_text(), None
    
    return content, None


# --- Commands ---

@app.command()
def create(
    summary: Annotated[str, typer.Option("--summary", "-s", help="Document summary")],
    file: Annotated[Path | None, typer.Option("--file", "-f", help="Path to content file")] = None,
    content: Annotated[str | None, typer.Option("--content", "-c", help="Inline content")] = None,
    stdin: Annotated[bool, typer.Option("--stdin", help="Read content from stdin")] = False,
    metadata: Annotated[str, typer.Option("--metadata", "-m", help="JSON metadata object")] = "{}",
    fmt: Annotated[OutputFormat, typer.Option("--format", help="Output format (json|markdown)")] = OutputFormat.json,
) -> None:
    """Create a new document (version 1)."""
    # Validate format (no plain for create)
    if error := _validate_format_no_plain(fmt, "create"):
        _output(error, OutputFormat.json)
        raise typer.Exit(code=4)
    
    # Read content
    doc_content, error = _read_content(file, content, stdin)
    if error:
        _output(error, fmt)
        raise typer.Exit(code=4)
    
    # Parse and validate metadata (must be object/dict)
    meta_dict, error = _parse_metadata(metadata)
    if error:
        _output(error, fmt)
        raise typer.Exit(code=4)
    
    # Create document
    try:
        result = db.create_document(summary, doc_content, meta_dict)
    except Exception as e:
        _output(_error_response("DB_ERROR", str(e)), fmt)
        raise typer.Exit(code=3)
    
    response = MCPResponse(
        success=True,
        content=[MCPContent(type=ContentType.JSON, data=result)],
        metadata={"message": "Document created successfully"}
    )
    _output(response, fmt)


@app.command()
def submit(
    document_id: Annotated[str, typer.Argument(help="Document ID to update")],
    summary: Annotated[str, typer.Option("--summary", "-s", help="Version summary")],
    file: Annotated[Path | None, typer.Option("--file", "-f", help="Path to content file")] = None,
    content: Annotated[str | None, typer.Option("--content", "-c", help="Inline content")] = None,
    stdin: Annotated[bool, typer.Option("--stdin", help="Read content from stdin")] = False,
    metadata: Annotated[str, typer.Option("--metadata", "-m", help="JSON metadata object")] = "{}",
    fmt: Annotated[OutputFormat, typer.Option("--format", help="Output format (json|markdown)")] = OutputFormat.json,
) -> None:
    """Submit a new version of existing document."""
    # Validate format (no plain for submit)
    if error := _validate_format_no_plain(fmt, "submit"):
        _output(error, OutputFormat.json)
        raise typer.Exit(code=4)
    
    doc_content, error = _read_content(file, content, stdin)
    if error:
        _output(error, fmt)
        raise typer.Exit(code=4)
    
    # Parse and validate metadata
    meta_dict, error = _parse_metadata(metadata)
    if error:
        _output(error, fmt)
        raise typer.Exit(code=4)
    
    try:
        result = db.submit_version(document_id, summary, doc_content, meta_dict)
    except Exception as e:
        _output(_error_response("DB_ERROR", str(e)), fmt)
        raise typer.Exit(code=3)
    
    if result is None:
        _output(_error_response(
            "DOC_NOT_FOUND",
            f"Document '{document_id}' not found or deleted",
            "Use 'aw docs list' to see available documents. Cannot submit to deleted documents."
        ), fmt)
        raise typer.Exit(code=2)
    
    response = MCPResponse(
        success=True,
        content=[MCPContent(type=ContentType.JSON, data=result)],
        metadata={"message": f"Version {result['version']} submitted successfully"}
    )
    _output(response, fmt)


@app.command()
def get(
    document_id: Annotated[str, typer.Argument(help="Document ID")],
    version: Annotated[int | None, typer.Option("--version", "-v", help="Specific version")] = None,
    fmt: Annotated[OutputFormat, typer.Option("--format", help="Output format (json|markdown|plain)")] = OutputFormat.json,
) -> None:
    """Get document content (stdout). Use --format plain for raw content only."""
    doc = db.get_document(document_id, version)
    
    if doc is None:
        # For errors, always use json/markdown (not plain)
        error_fmt = OutputFormat.json if fmt == OutputFormat.plain else fmt
        _output(_error_response(
            "DOC_NOT_FOUND" if version is None else "VERSION_NOT_FOUND",
            f"Document '{document_id}'" + (f" version {version}" if version else "") + " not found",
            "Use 'aw docs list' or 'aw docs history' to see available documents/versions"
        ), error_fmt)
        raise typer.Exit(code=2)
    
    if fmt == OutputFormat.plain:
        # Plain format: raw content only (no JSON wrapper)
        _output_plain(doc["content"])
    else:
        response = MCPResponse(
            success=True,
            content=[MCPContent(type=ContentType.JSON, data=doc)]
        )
        _output(response, fmt)


@app.command("list")
def list_docs(
    limit: Annotated[int | None, typer.Option("--limit", "-l", help="Max documents")] = None,
    include_deleted: Annotated[bool, typer.Option("--include-deleted", help="Include deleted")] = False,
    fmt: Annotated[OutputFormat, typer.Option("--format", help="Output format (json|markdown)")] = OutputFormat.json,
) -> None:
    """List all documents (latest version each)."""
    # Validate format (no plain for list)
    if error := _validate_format_no_plain(fmt, "list"):
        _output(error, OutputFormat.json)
        raise typer.Exit(code=4)
    
    documents, total = db.list_documents(limit, include_deleted)
    
    response = MCPResponse(
        success=True,
        content=[MCPContent(type=ContentType.JSON, data={"documents": documents})],
        total_count=total,
        has_more=limit is not None and len(documents) < total,
    )
    _output(response, fmt)


@app.command()
def history(
    document_id: Annotated[str, typer.Argument(help="Document ID")],
    limit: Annotated[int | None, typer.Option("--limit", "-l", help="Max versions")] = None,
    fmt: Annotated[OutputFormat, typer.Option("--format", help="Output format (json|markdown)")] = OutputFormat.json,
) -> None:
    """Show version history of a document (hidden for deleted docs)."""
    # Validate format (no plain for history)
    if error := _validate_format_no_plain(fmt, "history"):
        _output(error, OutputFormat.json)
        raise typer.Exit(code=4)
    
    versions, total = db.get_history(document_id, limit)
    
    if total == 0:
        _output(_error_response(
            "DOC_NOT_FOUND",
            f"Document '{document_id}' not found or deleted",
            "Use 'aw docs list' to see available documents"
        ), fmt)
        raise typer.Exit(code=2)
    
    response = MCPResponse(
        success=True,
        content=[MCPContent(
            type=ContentType.JSON,
            data={"document_id": document_id, "versions": versions}
        )],
        total_count=total,
        has_more=limit is not None and len(versions) < total,
    )
    _output(response, fmt)


@app.command()
def export(
    document_id: Annotated[str, typer.Argument(help="Document ID")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Output file path")],
    version: Annotated[int | None, typer.Option("--version", "-v", help="Specific version")] = None,
    fmt: Annotated[OutputFormat, typer.Option("--format", help="Output format (json|markdown)")] = OutputFormat.json,
) -> None:
    """Export document content to file. Confirmation printed to stdout."""
    # Validate format (no plain for export)
    if error := _validate_format_no_plain(fmt, "export"):
        _output(error, OutputFormat.json)
        raise typer.Exit(code=4)
    
    doc = db.get_document(document_id, version)
    
    if doc is None:
        _output(_error_response(
            "DOC_NOT_FOUND",
            f"Document '{document_id}' not found",
            "Use 'aw docs list' to see available documents"
        ), fmt)
        raise typer.Exit(code=2)
    
    # Write content to file
    output.write_text(doc["content"])
    
    # Confirmation to stdout
    response = MCPResponse(
        success=True,
        content=[MCPContent(type=ContentType.TEXT, text=f"Exported to {output}")],
        metadata={"path": str(output), "version": doc["version"]}
    )
    _output(response, fmt)


@app.command()
def delete(
    document_id: Annotated[str, typer.Argument(help="Document ID")],
    confirm: Annotated[bool, typer.Option("--confirm", help="Confirm deletion")] = False,
    fmt: Annotated[OutputFormat, typer.Option("--format", help="Output format (json|markdown)")] = OutputFormat.json,
) -> None:
    """Soft-delete document (marks all versions as deleted)."""
    # Validate format (no plain for delete)
    if error := _validate_format_no_plain(fmt, "delete"):
        _output(error, OutputFormat.json)
        raise typer.Exit(code=4)
    
    if not confirm:
        _output(_error_response(
            "INVALID_INPUT",
            "Deletion requires confirmation",
            "Add --confirm flag to proceed"
        ), fmt)
        raise typer.Exit(code=4)
    
    affected = db.soft_delete_document(document_id)
    
    if affected == 0:
        _output(_error_response(
            "DOC_NOT_FOUND",
            f"Document '{document_id}' not found or already deleted",
            "Use 'aw docs list' to see available documents"
        ), fmt)
        raise typer.Exit(code=2)
    
    response = MCPResponse(
        success=True,
        content=[MCPContent(type=ContentType.TEXT, text="Document soft-deleted")],
        metadata={"document_id": document_id, "versions_affected": affected}
    )
    _output(response, fmt)


if __name__ == "__main__":
    app()
```

**3.5. Register plugin** 🚧

Add to `devtools/common/cli/devtool/aweave/core/main.py`:

```python
from aweave.docs import app as docs_app

# After load_python_plugins(app)
app.add_typer(docs_app, name="docs")
```

**3.6. Dependencies** ✅

**Không cần thêm dependency mới** - sử dụng:
- `sqlite3` (stdlib)
- `uuid` (stdlib)
- `json` (stdlib)
- `dataclasses` (stdlib, nếu cần)
- `typer` (đã có)
- `aweave.mcp.response` (internal)

#### Step 4: Testing

**4.1. Unit Tests (pytest)** 🚧

Create `devtools/common/cli/devtool/tests/test_docs.py`:

```python
"""Tests for aw docs CLI."""
import json
import os
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from aweave.docs.cli import app
from aweave.docs import db


@pytest.fixture
def temp_db(tmp_path):
    """Use temporary database file for testing."""
    db_path = tmp_path / "test_docstore.db"
    os.environ["AWEAVE_DB_PATH"] = str(db_path)
    yield db_path
    del os.environ["AWEAVE_DB_PATH"]


@pytest.fixture
def runner():
    return CliRunner()


class TestCreate:
    def test_create_with_content(self, runner, temp_db):
        result = runner.invoke(app, [
            "create", "--summary", "Test doc", "--content", "Hello world"
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["success"] is True
        assert "document_id" in data["content"][0]["data"]
        assert data["content"][0]["data"]["version"] == 1

    def test_create_with_file(self, runner, temp_db, tmp_path):
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test content")
        
        result = runner.invoke(app, [
            "create", "--summary", "From file", "--file", str(test_file)
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["success"] is True

    def test_create_no_content_error(self, runner, temp_db):
        result = runner.invoke(app, ["create", "--summary", "No content"])
        assert result.exit_code == 4
        data = json.loads(result.output)
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_INPUT"


class TestSubmit:
    def test_submit_new_version(self, runner, temp_db):
        # Create first
        result = runner.invoke(app, [
            "create", "--summary", "v1", "--content", "Version 1"
        ])
        doc_id = json.loads(result.output)["content"][0]["data"]["document_id"]
        
        # Submit v2
        result = runner.invoke(app, [
            "submit", doc_id, "--summary", "v2", "--content", "Version 2"
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["content"][0]["data"]["version"] == 2

    def test_submit_nonexistent_doc(self, runner, temp_db):
        result = runner.invoke(app, [
            "submit", "nonexistent-id", "--summary", "v2", "--content", "test"
        ])
        assert result.exit_code == 2
        data = json.loads(result.output)
        assert data["error"]["code"] == "DOC_NOT_FOUND"


class TestGet:
    def test_get_latest(self, runner, temp_db):
        # Create
        result = runner.invoke(app, [
            "create", "--summary", "Test", "--content", "Content here"
        ])
        doc_id = json.loads(result.output)["content"][0]["data"]["document_id"]
        
        # Get
        result = runner.invoke(app, ["get", doc_id])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["content"][0]["data"]["content"] == "Content here"

    def test_get_plain_format(self, runner, temp_db):
        result = runner.invoke(app, [
            "create", "--summary", "Test", "--content", "Raw content"
        ])
        doc_id = json.loads(result.output)["content"][0]["data"]["document_id"]
        
        result = runner.invoke(app, ["get", doc_id, "--format", "plain"])
        assert result.exit_code == 0
        assert result.output.strip() == "Raw content"


class TestList:
    def test_list_empty(self, runner, temp_db):
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["total_count"] == 0

    def test_list_with_documents(self, runner, temp_db):
        # Create 2 docs
        runner.invoke(app, ["create", "--summary", "Doc 1", "--content", "c1"])
        runner.invoke(app, ["create", "--summary", "Doc 2", "--content", "c2"])
        
        result = runner.invoke(app, ["list"])
        data = json.loads(result.output)
        assert data["total_count"] == 2


class TestDelete:
    def test_soft_delete(self, runner, temp_db):
        # Create
        result = runner.invoke(app, [
            "create", "--summary", "To delete", "--content", "test"
        ])
        doc_id = json.loads(result.output)["content"][0]["data"]["document_id"]
        
        # Delete without confirm
        result = runner.invoke(app, ["delete", doc_id])
        assert result.exit_code == 4
        
        # Delete with confirm
        result = runner.invoke(app, ["delete", doc_id, "--confirm"])
        assert result.exit_code == 0
        
        # Should not appear in list
        result = runner.invoke(app, ["list"])
        data = json.loads(result.output)
        assert data["total_count"] == 0
        
        # Should appear with --include-deleted
        result = runner.invoke(app, ["list", "--include-deleted"])
        data = json.loads(result.output)
        assert data["total_count"] == 1
```

**4.2. Run tests**

```bash
cd devtools
uv run pytest common/cli/devtool/tests/test_docs.py -v
```

**4.3. Manual Testing Workflow**

```bash
# Override DB path for testing (optional - otherwise uses ~/.aweave/docstore.db)
export AWEAVE_DB_PATH=/tmp/test-docstore.db

# Test create
aw docs create --summary "Test doc" --content "Hello world"
# Expected: MCPResponse with document_id

# Test submit
aw docs submit <doc_id> --summary "v2" --content "Updated content"
# Expected: MCPResponse with version: 2

# Test get (JSON)
aw docs get <doc_id>
# Expected: Full document MCPResponse

# Test get (plain - for piping)
aw docs get <doc_id> --format plain
# Expected: Raw content only

# Test list
aw docs list
# Expected: List of documents MCPResponse

# Test history  
aw docs history <doc_id>
# Expected: Version history MCPResponse

# Test export
aw docs export <doc_id> --output ./test.md
# Expected: File created, MCPResponse confirmation

# Test delete
aw docs delete <doc_id> --confirm
# Expected: Soft-delete MCPResponse

# Verify soft-delete
aw docs list                    # Should not show deleted
aw docs list --include-deleted  # Should show deleted
```

---

## 📊 Summary of Results

> *To be filled after implementation*

### ✅ Completed Achievements

- [ ] Database schema với versioning + soft-delete
- [ ] DB location: `~/.aweave/docstore.db` (user home)
- [ ] All CLI commands với MCPResponse output
- [ ] Concurrency-safe version allocation
- [ ] Pytest test suite
- [ ] Integration with existing `aw` CLI

---

## 🚧 Outstanding Issues & Follow-up

### Implementation Checklist

- [ ] Create `aweave/docs/` module structure
- [ ] Implement `db.py` with all functions (incl. `get_db_path()`)
- [ ] Implement `cli.py` with all commands
- [ ] Register plugin in `main.py`
- [ ] Create test file
- [ ] Run `uv sync` to update workspace
- [ ] Manual testing

### Future Enhancements (Out of Scope)

1. **Search capability**: Full-text search trong content (FTS5 extension)
2. **Tags/Categories**: Filter documents by metadata tags
3. **Diff view**: Compare versions (`aw docs diff <doc_id> --v1 1 --v2 2`)
4. **Bulk operations**: Import/export multiple documents
5. **MCP Integration**: Expose as MCP tools cho broader AI agent ecosystem
6. **Schema migrations**: Auto-migrate khi schema thay đổi

### Design Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| DB location | `~/.aweave/docstore.db` | User home - không làm bẩn repo, share across projects |
| Delete policy | Soft-delete | Preserve audit trail |
| Metadata handling | Full replace | Simple, predictable |
| Output format | MCPResponse | Consistent với existing CLI tools |
| Dependencies | Stdlib only | No new deps needed |
| Data model | Single table | Simpler queries, good enough for use case |

### Questions Deferred

- **Multi-user**: Hiện tại single-user, local-only. Multi-user sẽ cần server component.
- **Per-project isolation**: Hiện tại 1 DB chung. Nếu cần isolate per project, có thể add `--db` flag hoặc namespace trong document_id.
- **Size limit**: Không enforce limit, SQLite handles large TEXT fine. Có thể add warning nếu cần.
