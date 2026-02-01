# Debate CLI

Python CLI (`aw debate`) để AI agents và human (Arbitrator) tương tác với debate-server.

## Purpose

CLI là **cầu nối chính** giữa AI agents và hệ thống debate:
- Proposer/Opponent agents gọi CLI để submit arguments
- Long polling cho real-time response
- Arbitrator commands (DEV-ONLY) để test trước khi có Web UI

## Commands

| Command | Role | Description |
|---------|------|-------------|
| `generate-id` | All | Generate UUID cho debate mới |
| `create` | Proposer | Tạo debate với MOTION |
| `get-context` | All | Lấy debate + motion + arguments |
| `submit` | Proposer/Opponent | Submit CLAIM argument |
| `wait` | Proposer/Opponent | Long polling chờ response |
| `appeal` | Proposer | Submit APPEAL yêu cầu Arbitrator |
| `request-completion` | Proposer | Submit RESOLUTION yêu cầu kết thúc |
| `ruling` | Arbitrator | Submit RULING (DEV-ONLY) |
| `intervention` | Arbitrator | Submit INTERVENTION (DEV-ONLY) |
| `list` | All | Liệt kê debates |

## Usage Examples

### Proposer Flow

```bash
# Generate debate ID
aw debate generate-id

# Create debate with motion
aw debate create \
  --debate-id <uuid> \
  --title "Implement caching layer" \
  --type coding_plan_debate \
  --content "I propose we add Redis caching..."

# Wait for opponent response
aw debate wait --debate-id <uuid> --role proposer

# Submit response
aw debate submit \
  --debate-id <uuid> \
  --role proposer \
  --target-id <argument_uuid> \
  --content "I agree with your point about..."
```

### Opponent Flow

```bash
# Get debate context
aw debate get-context --debate-id <uuid> --limit 10

# Wait for proposer (from beginning)
aw debate wait --debate-id <uuid> --role opponent

# Submit response
aw debate submit \
  --debate-id <uuid> \
  --role opponent \
  --target-id <argument_uuid> \
  --stdin < response.md
```

### Arbitrator Flow (DEV-ONLY)

```bash
# Submit intervention (pause debate)
aw debate intervention --debate-id <uuid>

# Submit ruling
aw debate ruling \
  --debate-id <uuid> \
  --content "My ruling is..."

# Submit ruling and close debate
aw debate ruling \
  --debate-id <uuid> \
  --content "Final ruling..." \
  --close
```

## Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| `DEBATE_SERVER_URL` | `http://127.0.0.1:3456` | Server URL |
| `DEBATE_AUTH_TOKEN` | (none) | Bearer token |
| `DEBATE_WAIT_DEADLINE` | `300` | Overall wait timeout (seconds) |

## Output Format

CLI outputs MCPResponse format cho AI agents parse:

**Success:**
```json
{
  "success": true,
  "content": [
    {
      "type": "json",
      "data": { ... }
    }
  ],
  "metadata": { "message": "..." }
}
```

**Error:**
```json
{
  "success": false,
  "error": {
    "code": "ACTION_NOT_ALLOWED",
    "message": "...",
    "suggestion": "..."
  },
  "content": [
    {
      "type": "json",
      "data": {
        "server_error": { ... }
      }
    }
  ]
}
```

## Wait Response

Khi có argument mới:
```json
{
  "success": true,
  "content": [{
    "type": "json",
    "data": {
      "status": "new_argument",
      "action": "respond",
      "debate_state": "AWAITING_PROPOSER",
      "argument": { ... },
      "next_argument_id_to_wait": "<uuid>"
    }
  }]
}
```

Khi timeout:
```json
{
  "success": true,
  "content": [{
    "type": "json",
    "data": {
      "status": "timeout",
      "message": "No response after 300s",
      "debate_id": "<uuid>",
      "last_argument_id": "<uuid>",
      "last_seen_seq": 5
    }
  }]
}
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | File not found |
| 2 | Resource not found (debate/argument) |
| 3 | Server/internal error |
| 4 | Invalid input |
| 5 | Action not allowed |
| 6 | Auth failed |

## Content Input

All commands accepting content support 3 input methods:

```bash
# From file
aw debate submit ... --file response.md

# Inline
aw debate submit ... --content "My response..."

# From stdin
cat response.md | aw debate submit ... --stdin
```

## Idempotency

- Tất cả write commands auto-generate `client_request_id` nếu không truyền
- Có thể truyền explicit `--client-request-id` để retry safely
- Server trả existing result nếu request đã xử lý

## Related

- **Spec:** `devdocs/misc/devtools/debate.md`
- **Server:** `devtools/common/debate-server/`
- **Plan:** `devdocs/misc/devtools/plans/260131-debate-cli.md`
- **HTTP Client:** `aweave/http/client.py`
- **MCPResponse:** `aweave/mcp/response.py`
