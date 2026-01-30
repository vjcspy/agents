# Implementation Plan: Bitbucket CLI với MCP-style Response

**Date:** 2026-01-30  
**Status:** ✅ Completed  
**Related:** `devdocs/agent/commands/tinybots/fix-pr-comments.md`

## 1. Overview

**Mục tiêu:** Implement Bitbucket API client trong `devtools/tinybots/cli/bitbucket` với response format theo chuẩn MCP để:

- Thay thế curl commands bằng Python API calls
- Response data chuẩn hóa cho AI agent dễ xử lý
- Code reusable cho các dự án khác

**Reference:**
- MCP Best Practices: `devdocs/agent/skills/common/mcp-builder/reference/mcp_best_practices.md`
- Current command: `devdocs/agent/commands/tinybots/fix-pr-comments.md`

---

## 2. Architecture

```
devtools/
├── common/cli/devtool/aweave/
│   ├── http/                       # Shared HTTP utilities
│   │   ├── __init__.py
│   │   └── client.py              # Base HTTP client với error handling
│   │
│   └── mcp/                        # MCP-style response models
│       ├── __init__.py
│       ├── response.py            # MCPResponse, MCPError, MCPContent
│       └── pagination.py          # Pagination helpers
│
└── tinybots/cli/bitbucket/
    ├── pyproject.toml
    ├── ruff.toml
    └── tinybots/                   # Namespace package
        ├── __init__.py
        └── bitbucket/              # Bitbucket module
            ├── __init__.py
            ├── cli.py             # Typer CLI commands
            ├── client.py          # Bitbucket API client
            └── models.py          # Bitbucket data models (PR, Comment, Task)
```

---

## 3. Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `BITBUCKET_USER` | Bitbucket username/email | `user@example.com` |
| `BITBUCKET_APP_PASSWORD` | Bitbucket App Password | `ATATTxxxxx...` |

> **Note:** Create an App Password at: https://bitbucket.org/account/settings/app-passwords/

---

## 4. CLI Usage

```bash
# Get PR info
aw tinybots-bitbucket pr <repo> <pr_id>

# Get PR info in markdown format
aw tinybots-bitbucket pr micro-manager 126 -f markdown

# List comments with pagination
aw tinybots-bitbucket comments micro-manager 126 --limit 50

# List tasks for different workspace
aw tinybots-bitbucket tasks my-repo 42 -w my-workspace

# Pipe to jq for processing
aw tinybots-bitbucket comments micro-manager 126 | jq '.content[].data'
```

---

## 5. MCP Response Format

### Success Response

```json
{
  "success": true,
  "content": [
    {
      "type": "json",
      "data": {
        "id": 126,
        "title": "feat: implement API for listing triggered script executions",
        "author": {
          "uuid": "{uuid}",
          "display_name": "Kai",
          "account_id": "712020:xxx"
        },
        "source_branch": "task/PROD-1067-TASK1-api-list",
        "destination_branch": "feature/PROD-1067-expose-trigger-script",
        "state": "OPEN",
        "created_on": "2026-01-15T07:48:17.142448+00:00"
      }
    }
  ],
  "metadata": {
    "workspace": "tinybots",
    "repo_slug": "micro-manager",
    "resource_type": "pull_request"
  }
}
```

### Paginated Response

```json
{
  "success": true,
  "content": [
    {"type": "json", "data": {"id": 740667474, "content": "Why not create a separate model...", ...}},
    {"type": "json", "data": {"id": 740668693, "content": "Should add the response to tiny-specs...", ...}}
  ],
  "metadata": {
    "workspace": "tinybots",
    "repo_slug": "micro-manager",
    "pr_id": 126,
    "resource_type": "pr_comments"
  },
  "has_more": true,
  "next_offset": 5,
  "total_count": 11
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "code": "AUTH_FAILED",
    "message": "Authentication failed",
    "suggestion": "Check your credentials (username/password or token)"
  }
}
```

---

## 6. File Changes Summary

### New Files

| Path | Description |
|------|-------------|
| `common/cli/devtool/aweave/mcp/__init__.py` | MCP module init |
| `common/cli/devtool/aweave/mcp/response.py` | MCP response models |
| `common/cli/devtool/aweave/mcp/pagination.py` | Pagination utilities |
| `common/cli/devtool/aweave/http/__init__.py` | HTTP module init |
| `common/cli/devtool/aweave/http/client.py` | Base HTTP client |
| `tinybots/cli/bitbucket/tinybots/bitbucket/__init__.py` | Bitbucket module init |
| `tinybots/cli/bitbucket/tinybots/bitbucket/cli.py` | CLI commands |
| `tinybots/cli/bitbucket/tinybots/bitbucket/client.py` | Bitbucket API client |
| `tinybots/cli/bitbucket/tinybots/bitbucket/models.py` | Data models |

### Modified Files

| Path | Changes |
|------|---------|
| `common/cli/devtool/pyproject.toml` | Add `httpx>=0.28.0` dependency |
| `tinybots/cli/bitbucket/pyproject.toml` | Add `aweave` dependency, update entry point |
| `tinybots/cli/bitbucket/tinybots/__init__.py` | Update to namespace package |
| `pyproject.toml` | Add `tinybots-bitbucket` to dependencies and sources |

### Deleted Files

| Path | Reason |
|------|--------|
| `tinybots/cli/bitbucket/tinybots/cli.py` | Moved to `tinybots/bitbucket/cli.py` |

---

## 7. Implementation Checklist

| # | Task | Status |
|---|------|--------|
| 1.1 | Create MCP Response Models | ✅ Done |
| 1.2 | Create Pagination Utilities | ✅ Done |
| 1.3 | Create MCP Package Init | ✅ Done |
| 1.4 | Create Base HTTP Client | ✅ Done |
| 1.5 | Create HTTP Package Init | ✅ Done |
| 2.1 | Create Bitbucket Models | ✅ Done |
| 2.2 | Create Bitbucket Client | ✅ Done |
| 2.3 | Create Bitbucket Module Init | ✅ Done |
| 3.1 | Create CLI Commands | ✅ Done |
| 3.2 | Update tinybots package init | ✅ Done |
| 4.1 | Update Common Dependencies | ✅ Done |
| 4.2 | Update Bitbucket pyproject.toml | ✅ Done |
| 4.3 | Update Workspace Root pyproject.toml | ✅ Done |
| 4.4 | Delete old cli.py | ✅ Done |
| 5 | Sync and Test | ✅ Done |

---

## 8. Test Results

```bash
# PR info - ✅ Working
$ aw tinybots-bitbucket pr micro-manager 126
{
  "success": true,
  "content": [{"type": "json", "data": {"id": 126, "title": "feat: implement API...", ...}}],
  "metadata": {"workspace": "tinybots", "repo_slug": "micro-manager", "resource_type": "pull_request"}
}

# Comments with pagination - ✅ Working  
$ aw tinybots-bitbucket comments micro-manager 126 --limit 5
{
  "success": true,
  "content": [...5 comments...],
  "has_more": true,
  "next_offset": 5,
  "total_count": 11
}

# Tasks - ✅ Working
$ aw tinybots-bitbucket tasks micro-manager 126
{
  "success": true,
  "content": [...3 tasks with RESOLVED/UNRESOLVED state...],
  "has_more": false,
  "total_count": 3
}

# Error handling (missing credentials) - ✅ Working
$ aw tinybots-bitbucket pr test-repo 1
Error: BITBUCKET_USER and BITBUCKET_APP_PASSWORD environment variables required.
```

---

## 9. Future Extensions

1. **More Bitbucket Operations:**
   - Create/resolve tasks
   - Post comments
   - Approve/decline PR
   - Merge PR

2. **Convert to MCP Server:**
   - Code structure ready for MCP server wrapper
   - Add transport layer (stdio/HTTP)

3. **Caching Layer:**
   - Cache repeated requests
   - Configurable TTL

4. **Rate Limiting:**
   - Handle Bitbucket rate limits
   - Automatic retry with backoff
