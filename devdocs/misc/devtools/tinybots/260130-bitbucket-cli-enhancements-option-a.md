# 📋 [260130: 2026-01-30] - Bitbucket CLI Enhancements

**Status:** Draft  
**Related:** [260130-bitbucket-cli-implementation.md](./260130-bitbucket-cli-implementation.md)

## References

- MCP Best Practices: `devdocs/agent/skills/common/mcp-builder/reference/mcp_best_practices.md`
- Command liên quan: `devdocs/agent/commands/tinybots/fix-pr-comments.md`
- Source code:
  - Common MCP/HTTP: `devtools/common/cli/devtool/aweave/mcp/`, `devtools/common/cli/devtool/aweave/http/`
  - Tinybots Bitbucket: `devtools/tinybots/cli/bitbucket/tinybots/bitbucket/`

---

## 🎯 Objective

Nâng cao chất lượng Bitbucket CLI và common MCP/HTTP:

1. **JSON decode hardening** - Xử lý response không phải JSON
2. **Pagination fix** - Sửa logic `has_more` và `total_count` theo đúng Bitbucket API behavior
3. **Tests** - Unit tests cho models, client, và CLI

### ⚠️ Key Considerations

- Giữ nguyên API hiện có, không phá vỡ entry points hoặc hành vi output
- Credentials chỉ qua environment variables (an toàn, không expose qua CLI args)
- Logging sẽ được improve riêng trong task khác

---

## 📚 Background: Bitbucket Pagination

> Source: [Bitbucket Cloud REST API - Pagination](https://developer.atlassian.com/cloud/bitbucket/rest/intro/#pagination)

### Response Structure

```json
{
  "size": 5421,
  "page": 2,
  "pagelen": 10,
  "next": "https://api.bitbucket.org/2.0/repositories/pypy/pypy/commits?page=3",
  "previous": "https://api.bitbucket.org/2.0/repositories/pypy/pypy/commits?page=1",
  "values": [...]
}
```

### Field Definitions

| Field | Required | Description |
|-------|----------|-------------|
| `values` | ✅ Yes | The list of objects (max `pagelen` items) |
| `next` | ✅ Yes* | Link to next page. **Absence indicates end of collection** |
| `pagelen` | ✅ Yes | Number of objects on current page (10-100) |
| `size` | ❌ Optional | Total count - **expensive to compute, not always provided** |
| `page` | ❌ Optional | Current page number - not always provided |
| `previous` | ❌ Optional | Link to previous page |

> *`next` is guaranteed on all pages except the last page

### Two Types of Pagination

| Type | Characteristics | `next` format | Has `size`/`page` |
|------|-----------------|---------------|-------------------|
| **List-based** | Discrete, finite array with fixed size | `?page=4` | ✅ Usually yes |
| **Iterator-based** | Stream-like, forward-only navigation | `?hash=abc123` | ❌ No |

**Examples:**
- Comments, Tasks, PRs → List-based (usually have `size`)
- Commits → Iterator-based (no `size`, unpredictable `next` hash)

### Key Insight

> "Only `values` and `next` are guaranteed (except the last page, which lacks `next`)"

**Implication:** Không nên dựa vào `size` để tính `has_more`. Phải dùng sự có mặt của `next` link.

---

## 🔍 Current Implementation Issues

### Issue 1: JSON decode không có error handling

```python
# http/client.py line 101
return response.json()  # ❌ Có thể crash nếu response không phải JSON
```

### Issue 2: Pagination logic dựa vào `size` (unreliable)

```python
# bitbucket/client.py
total = data.get("size", len(comments))  # ❌ Fallback misleading
has_more = offset + len(items) < total   # ❌ Sai nếu không có size
```

---

## 🔄 Implementation Plan

### Phase 1: HTTP JSON Decode Hardening

**File:** `devtools/common/cli/devtool/aweave/http/client.py`

```python
def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
    # ... existing error handling ...
    
    if response.status_code == 204:
        return {}
    
    # NEW: Handle JSON decode errors
    try:
        return response.json()
    except (ValueError, json.JSONDecodeError) as e:
        raise HTTPClientError(
            code="BAD_JSON",
            message=f"Invalid JSON response: {e}",
            suggestion="Check if the endpoint returns JSON or verify Accept header",
        )
```

### Phase 2: Fix Pagination Logic

#### 2.1 Update `create_paginated_response` signature

**File:** `devtools/common/cli/devtool/aweave/mcp/pagination.py`

```python
def create_paginated_response(
    items: list[T],
    total: int | None,           # Changed: accept None
    has_more: bool,              # New: explicit parameter
    next_offset: int | None,     # New: explicit parameter  
    formatter: Callable[[T], MCPContent],
    metadata: dict[str, Any] | None = None,
) -> MCPResponse:
    """Create MCP response with pagination metadata."""
    content = [formatter(item) for item in items]
    
    return MCPResponse(
        success=True,
        content=content,
        metadata=metadata or {},
        has_more=has_more,
        next_offset=next_offset,
        total_count=total,
    )
```

#### 2.2 Update `MCPResponse.to_markdown()` for None total_count

**File:** `devtools/common/cli/devtool/aweave/mcp/response.py`

```python
def to_markdown(self) -> str:
    # ... existing code ...
    
    if self.has_more:
        if self.total_count is not None:
            msg = f"Showing {len(self.content)} of {self.total_count} items."
        else:
            msg = f"Showing {len(self.content)} items. More available."
        lines.append(f"\n---\n*{msg} Use --offset {self.next_offset} to see more.*")
    
    return "\n".join(lines)
```

#### 2.3 Update BitbucketClient to use `next` link

**File:** `devtools/tinybots/cli/bitbucket/tinybots/bitbucket/client.py`

```python
def list_pr_comments(self, repo_slug: str, pr_id: int, limit: int = 25, offset: int = 0) -> MCPResponse:
    try:
        path = f"{self._repo_path(repo_slug)}/pullrequests/{pr_id}/comments"
        params = {"pagelen": limit, "page": (offset // limit) + 1}
        data = self._http.get(path, params=params)

        comments = [PRComment.from_api(c) for c in data.get("values", [])]
        
        # NEW: Correct pagination logic
        has_more = "next" in data                              # ✅ Reliable
        total_count = data.get("size")                         # ✅ None if not provided
        next_offset = offset + len(comments) if has_more else None

        return create_paginated_response(
            items=comments,
            total=total_count,
            has_more=has_more,
            next_offset=next_offset,
            formatter=lambda c: MCPContent(type=ContentType.JSON, data=c.to_dict()),
            metadata={...},
        )
    except HTTPClientError as e:
        return MCPResponse(
            success=False,
            error=MCPError(code=e.code, message=e.message, suggestion=e.suggestion),
        )
```

### Phase 3: Tests

#### 3.1 Test Structure

```
devtools/
├── common/cli/devtool/
│   └── tests/
│       ├── test_http_client.py      # HTTPClient error handling, JSON decode
│       └── test_mcp_response.py     # MCPResponse, pagination
└── tinybots/cli/bitbucket/
    └── tests/
        ├── test_models.py           # from_api/to_dict với edge cases
        ├── test_client.py           # BitbucketClient với mocked HTTP
        └── test_cli.py              # CLI commands với CliRunner
```

#### 3.2 Test Cases

**HTTP Client:**
- JSON decode success
- JSON decode failure → `BAD_JSON` error
- HTTP 401/403/404/500 → correct error codes

**Models:**
- `from_api` với đầy đủ fields
- `from_api` với missing optional fields (inline.path, creator, etc.)
- `to_dict` serialization

**BitbucketClient:**
- Pagination với `next` link present → `has_more=True`
- Pagination không có `next` link → `has_more=False`
- Pagination với `size` → `total_count` có giá trị
- Pagination không có `size` → `total_count=None`

**CLI:**
- JSON output format
- Markdown output format với `total_count=None`
- Missing credentials → error message

---

## 📊 File Changes Summary

| File | Changes |
|------|---------|
| `aweave/http/client.py` | Add JSON decode error handling |
| `aweave/mcp/pagination.py` | Change signature: `total: int \| None`, add `has_more`, `next_offset` |
| `aweave/mcp/response.py` | Update `to_markdown()` for `total_count=None` |
| `bitbucket/client.py` | Use `"next" in data` for `has_more`, `data.get("size")` for total |

---

## ✅ Implementation Checklist

| # | Task | Status |
|---|------|--------|
| 1 | JSON decode hardening in HTTPClient | ⬜ Pending |
| 2.1 | Update `create_paginated_response` signature | ⬜ Pending |
| 2.2 | Update `MCPResponse.to_markdown()` | ⬜ Pending |
| 2.3 | Fix BitbucketClient pagination logic | ⬜ Pending |
| 3.1 | Tests for HTTP client | ⬜ Pending |
| 3.2 | Tests for models | ⬜ Pending |
| 3.3 | Tests for BitbucketClient | ⬜ Pending |
| 3.4 | Tests for CLI | ⬜ Pending |

---

## 🚧 Out of Scope (Future Tasks)

- CLI credential options (`--username`, `--app-password`) - security concerns
- Logging framework - sẽ implement chuẩn chỉnh riêng
- Connection/Timeout error handling (`httpx.RequestError`)
- Rate limiting (HTTP 429) handling
