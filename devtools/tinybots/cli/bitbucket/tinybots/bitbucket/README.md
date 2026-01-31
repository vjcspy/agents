# TinyBots Bitbucket CLI

## Overview
CLI để tương tác với Bitbucket Pull Requests theo chuẩn MCP-style response. Hỗ trợ lấy thông tin PR, liệt kê comments và tasks với **auto-pagination** (tự động fetch tất cả pages).

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
- `aw tinybots-bitbucket comments <repo> <pr_id> [-w <workspace>] [-f json|markdown] [--max N]`
- `aw tinybots-bitbucket tasks <repo> <pr_id> [-w <workspace>] [-f json|markdown] [--max N]`

Mặc định:
- `workspace = tinybots`
- `format = json`
- `max = 500` (safety limit)

## Auto-Pagination Behavior
CLI tự động fetch tất cả pages từ Bitbucket API trước khi trả về response:
- Response **luôn luôn** có `has_more = false`
- AI agent/consumer không cần handle pagination logic
- `total_count` hiển thị tổng số items thực tế từ Bitbucket
- Option `--max` giới hạn số items tối đa fetch (mặc định 500, để tránh fetch quá nhiều data)

## Error Handling
- `AUTH_FAILED` (401): Sai tài khoản hoặc app password
- `FORBIDDEN` (403): Không đủ quyền truy cập
- `NOT_FOUND` (404): Sai workspace/repo/pr hoặc không có quyền xem
- `BAD_JSON`: Endpoint trả về dữ liệu không phải JSON hoặc payload hỏng

Nếu bất kỳ page nào fail trong quá trình fetch → toàn bộ request fail (không return partial data).

## Usage Examples
```bash
# Lấy thông tin PR
aw tinybots-bitbucket pr micro-manager 126 -f markdown

# Liệt kê tất cả comments (auto-fetch all pages)
aw tinybots-bitbucket comments micro-manager 126

# Giới hạn số comments tối đa
aw tinybots-bitbucket comments micro-manager 126 --max 10

# Liệt kê tasks cho workspace khác
aw tinybots-bitbucket tasks micro-manager 126 -w my-workspace
```

## Troubleshooting
- Nhận "Repository not found" hoặc 404 trên trang web → Có thể thiếu quyền truy cập hoặc repo không tồn tại trong workspace. Đảm bảo đã đăng nhập và có quyền phù hợp.
- Nhận `AUTH_FAILED` → Kiểm tra `BITBUCKET_USER` và `BITBUCKET_APP_PASSWORD`.
- Nhận `FORBIDDEN` → Kiểm tra quyền của app password.
- Nhận `BAD_JSON` → Kiểm tra `Accept: application/json` và tính hợp lệ của endpoint.
