# TinyBots Bitbucket CLI

## Overview
CLI để tương tác với Bitbucket Pull Requests theo chuẩn MCP-style response. Hỗ trợ lấy thông tin PR, liệt kê comments và tasks với phân trang chuẩn “latest-only”.

## Requirements
- Python 3.13
- uv (quản lý workspace)
- Môi trường devtools workspace đã khai báo plugin `tinybots-bitbucket` trong `[tool.uv.workspace]` và `aw.plugins`.

## Environment Variables
| Variable | Description |
|----------|-------------|
| `BITBUCKET_USER` | Bitbucket username/email |
| `BITBUCKET_APP_PASSWORD` | Bitbucket App Password (cấp quyền: Repositories:Read, Pull requests:Read) |

## Commands
- `aw tinybots-bitbucket pr <repo> <pr_id> [-w <workspace>] [-f json|markdown]`
- `aw tinybots-bitbucket comments <repo> <pr_id> [-w <workspace>] [-f json|markdown] [--limit N] [--offset N]`
- `aw tinybots-bitbucket tasks <repo> <pr_id> [-w <workspace>] [-f json|markdown] [--limit N] [--offset N]`

Mặc định:
- `workspace = tinybots`
- `format = json`
- `limit = 25`, `offset = 0`

## Pagination Behavior (Latest-only)
- Dựa vào trường `next` trong Bitbucket response.
- `has_more = "next" in data`
- `total_count = data.get("size")` (có thể `None` nếu API không cung cấp).
- `next_offset = offset + len(values)` khi `has_more` là `True`.
- Markdown output khi `total_count=None` hiển thị: “Showing N items. More available.”

## Error Handling
- `AUTH_FAILED` (401): Sai tài khoản hoặc app password
- `FORBIDDEN` (403): Không đủ quyền truy cập
- `NOT_FOUND` (404): Sai workspace/repo/pr hoặc không có quyền xem
- `BAD_JSON`: Endpoint trả về dữ liệu không phải JSON hoặc payload hỏng

## Usage Examples
```bash
# Lấy thông tin PR
aw tinybots-bitbucket pr micro-manager 126 -f markdown

# Liệt kê comments (50 items/trang)
aw tinybots-bitbucket comments micro-manager 126 --limit 50

# Liệt kê tasks cho workspace khác
aw tinybots-bitbucket tasks micro-manager 126 -w my-workspace
```

## Troubleshooting
- Nhận “Repository not found” hoặc 404 trên trang web → Có thể thiếu quyền truy cập hoặc repo không tồn tại trong workspace. Đảm bảo đã đăng nhập và có quyền phù hợp.
- Nhận `AUTH_FAILED` → Kiểm tra `BITBUCKET_USER` và `BITBUCKET_APP_PASSWORD`.
- Nhận `FORBIDDEN` → Kiểm tra quyền của app password.
- Nhận `BAD_JSON` → Kiểm tra `Accept: application/json` và tính hợp lệ của endpoint.
