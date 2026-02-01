# Debate CLI

Python CLI (`aw debate`) để AI agents và human (Arbitrator) tương tác với debate-server.

## Purpose

CLI là **cầu nối chính** giữa AI agents và hệ thống debate:
- Proposer/Opponent agents gọi CLI để submit arguments
- Long polling cho real-time response
- Arbitrator commands (DEV-ONLY) để test trước khi có Web UI

## Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| `DEBATE_SERVER_URL` | `http://127.0.0.1:3456` | Server URL |
| `DEBATE_AUTH_TOKEN` | (none) | Bearer token (nếu server require auth) |
| `DEBATE_WAIT_DEADLINE` | `300` | Overall wait timeout (seconds) |

## Response Format

Tất cả CLI commands output MCPResponse format:

```json
{
  "success": true|false,
  "content": [{ "type": "json", "data": { ... } }],
  "metadata": { ... },
  "error": { ... }
}
```

**Parse data với jq:**
```bash
jq -r '.content[0].data'        # Lấy data object
jq -r '.content[0].data.id'     # Lấy field cụ thể
```

## Commands

> **Chi tiết commands:** Xem [COMMANDS.md](COMMANDS.md)

Quick reference:

| Command | Description |
|---------|-------------|
| `generate-id` | Generate UUID |
| `create` | Tạo debate mới (Proposer) |
| `get-context` | Lấy debate context |
| `submit` | Submit CLAIM |
| `wait` | Long polling |
| `appeal` | Submit APPEAL (Proposer) |
| `request-completion` | Request close (Proposer) |
| `ruling` | Submit RULING (Arbitrator) |
| `intervention` | Pause debate (Arbitrator) |
| `list` | Liệt kê debates |

## Error Handling

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "ACTION_NOT_ALLOWED",
    "message": "Role 'opponent' cannot submit in state 'AWAITING_PROPOSER'",
    "suggestion": "Wait for proposer to submit their argument"
  }
}
```

### Error Codes

| Code | Exit Code | Meaning |
|------|-----------|---------|
| `DEBATE_NOT_FOUND` | 2 | Debate không tồn tại |
| `ARGUMENT_NOT_FOUND` | 2 | Argument không tồn tại |
| `INVALID_INPUT` | 4 | Input không hợp lệ |
| `ACTION_NOT_ALLOWED` | 5 | Action không hợp lệ trong state hiện tại |
| `AUTH_FAILED` | 6 | Authentication failed |
| `FILE_NOT_FOUND` | 4 | File không tồn tại |

## State Machine Reference

### States

| State | Description |
|-------|-------------|
| `AWAITING_OPPONENT` | Chờ Opponent phản hồi |
| `AWAITING_PROPOSER` | Chờ Proposer phản hồi |
| `AWAITING_ARBITRATOR` | Chờ Arbitrator ruling |
| `INTERVENTION_PENDING` | Arbitrator đã intervention |
| `CLOSED` | Debate kết thúc |

### Allowed Actions by State

| State | `submit` | `appeal` | `request-completion` | `ruling` | `intervention` |
|-------|----------|----------|----------------------|----------|----------------|
| `AWAITING_OPPONENT` | opponent | ❌ | ❌ | ❌ | ✅ |
| `AWAITING_PROPOSER` | proposer | proposer | proposer | ❌ | ✅ |
| `AWAITING_ARBITRATOR` | ❌ | ❌ | ❌ | ✅ | ❌ |
| `INTERVENTION_PENDING` | ❌ | ❌ | ❌ | ✅ | ❌ |
| `CLOSED` | ❌ | ❌ | ❌ | ❌ | ❌ |

## Idempotency

- Tất cả write commands auto-generate `client_request_id` nếu không truyền
- Có thể truyền explicit `--client-request-id` để retry safely
- Server trả existing result nếu request đã xử lý (same `client_request_id` + `debate_id`)

## Related

- **Commands Reference:** [COMMANDS.md](COMMANDS.md)
- **Spec:** `devdocs/misc/devtools/debate.md`
- **Server:** `devtools/common/debate-server/`
- **Server Overview:** `devdocs/misc/devtools/common/debate-server/OVERVIEW.md`
- **HTTP Client:** `aweave/http/client.py`
- **MCPResponse:** `aweave/mcp/response.py`
