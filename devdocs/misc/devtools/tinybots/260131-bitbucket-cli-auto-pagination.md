# 📋 [260131: 2026-01-31] - Bitbucket CLI Auto-Pagination

**Status:** Implemented  
**Related:** 
- [260130-bitbucket-cli-implementation.md](./260130-bitbucket-cli-implementation.md)
- [260130-bitbucket-cli-enhancements-option-a.md](./260130-bitbucket-cli-enhancements-option-a.md)

## References

- Source code:
  - BitbucketClient: `devtools/tinybots/cli/bitbucket/tinybots/bitbucket/client.py`
  - CLI commands: `devtools/tinybots/cli/bitbucket/tinybots/bitbucket/cli.py`
  - MCP Response: `devtools/common/cli/devtool/aweave/mcp/response.py`
  - Pagination: `devtools/common/cli/devtool/aweave/mcp/pagination.py`

---

## 🎯 Objective

**Tự động fetch tất cả dữ liệu** từ Bitbucket API khi nguồn trả về pagination. CLI sẽ loop qua tất cả pages và chỉ return khi đã có đầy đủ data.

**Kết quả mong muốn:**
- Response từ CLI **luôn luôn** có `has_more = false`
- AI agent không cần handle pagination logic
- Đơn giản hóa interface cho consumer

### ⚠️ Key Considerations

1. **CLI không phải MCP Server thực sự** - chỉ follow chuẩn MCP response format. Vì vậy không cần expose pagination cho consumer.

2. **Safety limit** - Cần có max limit để tránh fetch quá nhiều data (ví dụ: PR có 10,000 comments). Đề xuất max mặc định: 500 items.

3. **Backward compatibility** - Loại bỏ `--limit` và `--offset` options khỏi CLI vì không còn cần thiết.

4. **Performance** - Bitbucket API cho phép `pagelen` max 100 items/page. Sẽ sử dụng giá trị này để minimize số lượng requests.

5. **Architecture** - Pagination logic sẽ được encapsulate trong `BitbucketClient` thay vì `HTTPClient` để giữ generic client sạch sẽ.

6. **Error handling** - Nếu fetch bất kỳ page nào fail → fail toàn bộ request (không return partial data). Đơn giản và consistent.

---

## 📚 Background: Current vs New Behavior

### Current Behavior

```bash
# Phải gọi nhiều lần với offset khác nhau
$ aw tinybots-bitbucket comments micro-manager 126 --limit 5
{
  "success": true,
  "content": [...5 comments...],
  "has_more": true,           # ← Consumer phải check và fetch tiếp
  "next_offset": 5,
  "total_count": 11
}
```

### New Behavior (Auto-pagination)

```bash
# Một lần gọi - lấy tất cả
$ aw tinybots-bitbucket comments micro-manager 126
{
  "success": true,
  "content": [...11 comments...],  # ← Tất cả comments
  "has_more": false,               # ← Luôn false
  "total_count": 11
}
```

---

## 🔄 Implementation Plan

### Phase 1: Enhance HTTPClient (Minimal)

**File:** `devtools/common/cli/devtool/aweave/http/client.py`

Thêm method `get_url()` để fetch từ full URL (hỗ trợ pagination links của Bitbucket):

```python
def get_url(self, url: str) -> dict[str, Any]:
    """GET request using full URL (for pagination next links)."""
    # httpx Client handles absolute URLs correctly (ignoring base_url)
    with self._build_client() as client:
        response = client.get(url)
        return self._handle_response(response)
```

### Phase 2: Update BitbucketClient Methods

**File:** `devtools/tinybots/cli/bitbucket/tinybots/bitbucket/client.py`

#### 2.1 Add `_fetch_all_pages` Helper

Thêm private method để xử lý logic pagination đặc thù của Bitbucket:

```python
def _fetch_all_pages(
    self,
    path: str,
    params: dict[str, Any] | None = None,
    max_items: int = 500,
) -> tuple[list[dict[str, Any]], int | None]:
    """
    Fetch all pages from a Bitbucket paginated endpoint.
    """
    all_items: list[dict[str, Any]] = []
    total_count: int | None = None
    params = params or {}
    params["pagelen"] = 100  # Always use max page size for efficiency
    
    current_url: str | None = None
    first_request = True
    
    while True:
        if first_request:
            data = self._http.get(path, params=params)
            first_request = False
        else:
            # Use next URL directly
            data = self._http.get_url(current_url)
        
        values = data.get("values", [])
        all_items.extend(values)
        
        # Get total count if available (first page usually has it)
        if total_count is None:
            total_count = data.get("size")
        
        # Check if more pages exist
        current_url = data.get("next")
        if not current_url or len(all_items) >= max_items:
            break
    
    return all_items[:max_items], total_count
```

#### 2.2 Update `list_pr_comments`

```python
def list_pr_comments(
    self,
    repo_slug: str,
    pr_id: int,
    max_items: int = 500,  # Replaced limit/offset with max_items
) -> MCPResponse:
    try:
        path = f"{self._repo_path(repo_slug)}/pullrequests/{pr_id}/comments"
        
        # Auto-fetch all pages
        all_comments_data, total_count = self._fetch_all_pages(
            path, max_items=max_items
        )
        
        comments = [PRComment.from_api(c) for c in all_comments_data]
        
        return create_paginated_response(
            items=comments,
            total=total_count or len(comments),
            has_more=False,           # ← Always false
            next_offset=None,         # ← No more pagination
            formatter=lambda c: MCPContent(type=ContentType.JSON, data=c.to_dict()),
            metadata={
                "workspace": self._workspace,
                "repo_slug": repo_slug,
                "pr_id": pr_id,
                "resource_type": "pr_comments",
            },
        )
    except HTTPClientError as e:
        return MCPResponse(
            success=False,
            error=MCPError(code=e.code, message=e.message, suggestion=e.suggestion),
        )
```

#### 2.3 Update `list_pr_tasks`

Apply same pattern as `list_pr_comments`.

### Phase 3: Update CLI Commands

**File:** `devtools/tinybots/cli/bitbucket/tinybots/bitbucket/cli.py`

#### 3.1 Remove `--limit` và `--offset` options

```python
@app.command("comments")
def list_comments(
    repo: Annotated[str, typer.Argument(help="Repository slug")],
    pr_id: Annotated[int, typer.Argument(help="Pull request ID")],
    workspace: Annotated[
        str, typer.Option("--workspace", "-w", help="Bitbucket workspace")
    ] = "tinybots",
    fmt: Annotated[
        OutputFormat, typer.Option("--format", "-f", help="Output format")
    ] = OutputFormat.json,
    max_items: Annotated[
        int, typer.Option("--max", "-m", help="Maximum items to fetch")
    ] = 500,
) -> None:
    """List all PR comments (auto-fetches all pages)."""
    client = _get_client(workspace)
    response = client.list_pr_comments(repo, pr_id, max_items=max_items)
    _output(response, fmt)
```

#### 3.2 Tương tự cho `tasks` command

### Phase 4: Simplify Response Format (Optional)

**File:** `devtools/common/cli/devtool/aweave/mcp/response.py`

Simplify `MCPResponse.to_dict()` to only include pagination fields if they are meaningful (or just keep as is with `has_more=False`).

---

## 📊 File Changes Summary

| File | Changes |
|------|---------|
| `aweave/http/client.py` | Add `get_url()` method only |
| `bitbucket/client.py` | Add `_fetch_all_pages`, replace `limit`/`offset` logic |
| `bitbucket/cli.py` | Remove `--limit`/`--offset`, add `--max` option |
| `aweave/mcp/response.py` | (Optional) Simplify `to_dict()` output |

---

## ✅ Implementation Checklist

| # | Task | Status |
|---|------|--------|
| 1 | Add `get_url()` method to HTTPClient | ⬜ Pending |
| 2.1 | Add `_fetch_all_pages()` to BitbucketClient | ⬜ Pending |
| 2.2 | Update `list_pr_comments()` to use auto-pagination | ⬜ Pending |
| 2.3 | Update `list_pr_tasks()` to use auto-pagination | ⬜ Pending |
| 3.1 | Update `comments` CLI command | ⬜ Pending |
| 3.2 | Update `tasks` CLI command | ⬜ Pending |
| 4 | (Optional) Simplify MCPResponse.to_dict() | ⬜ Pending |
| 5 | Test with PR having many comments | ⬜ Pending |
