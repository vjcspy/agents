# CLI Tools Reference

Danh sách các CLI tools trong devtools monorepo, organized by namespace/domain.

## Common (`common/`)

Tools dùng chung cho tất cả projects.

### `aw docs` - Document Store

Lưu trữ và quản lý documents với immutable version history. Thiết kế cho AI agents trao đổi documents.

| Command | Description |
|---------|-------------|
| `aw docs create` | Tạo document mới |
| `aw docs submit` | Submit version mới |
| `aw docs get` | Lấy document content |
| `aw docs list` | Liệt kê documents |
| `aw docs history` | Xem version history |
| `aw docs export` | Export ra file |
| `aw docs delete` | Soft-delete document |

**Location:** `common/cli/devtool/aweave/docs/`

**Documentation:** [README.md](common/cli/devtool/aweave/docs/README.md)

---

## TinyBots (`tinybots/`)

Tools cho TinyBots project.

### `aw tinybots-bitbucket` - Bitbucket PR Tools

Tương tác với Bitbucket Pull Requests. Hỗ trợ auto-pagination.

| Command | Description |
|---------|-------------|
| `aw tinybots-bitbucket pr` | Lấy thông tin PR |
| `aw tinybots-bitbucket comments` | Liệt kê PR comments |
| `aw tinybots-bitbucket tasks` | Liệt kê PR tasks |

**Location:** `tinybots/cli/bitbucket/`

**Documentation:** [README.md](tinybots/cli/bitbucket/tinybots/bitbucket/README.md)

**Requirements:**
- `BITBUCKET_USER` environment variable
- `BITBUCKET_APP_PASSWORD` environment variable

---

## Output Format

Tất cả CLI tools đều output theo **MCP-style response format**:

```json
{
  "success": true,
  "content": [{"type": "json", "data": {...}}],
  "metadata": {...},
  "total_count": 10,
  "has_more": false
}
```

Error format:
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "suggestion": "Actionable next step"
  }
}
```

## Adding New Tools

See [README.md](README.md#adding-a-new-plugin) for instructions on adding new CLI tools.
