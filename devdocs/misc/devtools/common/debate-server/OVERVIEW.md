# Debate Server

Node.js backend server cho hệ thống debate giữa các AI agents.

## Purpose

Server là **single source of truth** cho:
- State machine management
- Per-debate locking
- Data persistence (SQLite)
- Real-time notifications (WebSocket + Long Polling)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     debate-server                            │
├─────────────────────────────────────────────────────────────┤
│  HTTP REST API          │  WebSocket Server                 │
│  - POST /debates        │  - Room per debate_id             │
│  - GET /debates/:id     │  - new_argument events            │
│  - POST /arguments      │  - state_changed events           │
│  - GET /wait (polling)  │                                   │
├─────────────────────────────────────────────────────────────┤
│                    Services Layer                            │
│  DebateService         ArgumentService        LockService   │
├─────────────────────────────────────────────────────────────┤
│                    State Machine                             │
│  States: AWAITING_OPPONENT → AWAITING_PROPOSER → ...        │
├─────────────────────────────────────────────────────────────┤
│                    SQLite (WAL mode)                         │
│  Tables: debates, arguments, schema_meta                    │
└─────────────────────────────────────────────────────────────┘
```

## Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| `DEBATE_SERVER_HOST` | `127.0.0.1` | Bind address |
| `DEBATE_SERVER_PORT` | `3456` | Listen port |
| `DEBATE_AUTH_TOKEN` | (none) | Bearer token for auth |
| `DEBATE_DB_PATH` | `~/.aweave/debate.db` | SQLite database path |
| `DEBATE_POLL_TIMEOUT_MS` | `60000` | Long poll timeout (60s) |
| `DEBATE_HTTP_TIMEOUT_MS` | `65000` | HTTP keep-alive timeout |
| `DEBATE_MAX_CONTENT_LENGTH` | `10240` | Max content size (10KB) |

## State Machine

### States

| State | Description |
|-------|-------------|
| `AWAITING_OPPONENT` | Proposer đã submit, chờ Opponent phản hồi |
| `AWAITING_PROPOSER` | Opponent đã submit, chờ Proposer phản hồi |
| `AWAITING_ARBITRATOR` | Có APPEAL hoặc RESOLUTION, chờ Arbitrator ruling |
| `INTERVENTION_PENDING` | Arbitrator đã intervention, chờ ruling |
| `CLOSED` | Debate đã kết thúc |

### Transitions

| From State | Action | By | To State |
|------------|--------|-----|----------|
| - | create debate | Proposer | `AWAITING_OPPONENT` |
| `AWAITING_OPPONENT` | submit CLAIM | Opponent | `AWAITING_PROPOSER` |
| `AWAITING_OPPONENT` | intervention | Arbitrator | `INTERVENTION_PENDING` |
| `AWAITING_PROPOSER` | submit CLAIM | Proposer | `AWAITING_OPPONENT` |
| `AWAITING_PROPOSER` | appeal | Proposer | `AWAITING_ARBITRATOR` |
| `AWAITING_PROPOSER` | request-completion | Proposer | `AWAITING_ARBITRATOR` |
| `AWAITING_PROPOSER` | intervention | Arbitrator | `INTERVENTION_PENDING` |
| `AWAITING_ARBITRATOR` | ruling | Arbitrator | `AWAITING_PROPOSER` |
| `AWAITING_ARBITRATOR` | ruling --close | Arbitrator | `CLOSED` |
| `INTERVENTION_PENDING` | ruling | Arbitrator | `AWAITING_PROPOSER` |
| `INTERVENTION_PENDING` | ruling --close | Arbitrator | `CLOSED` |

### Allowed Actions Matrix

| State | Proposer | Opponent | Arbitrator |
|-------|----------|----------|------------|
| `AWAITING_OPPONENT` | ❌ | submit | intervention |
| `AWAITING_PROPOSER` | submit, appeal, request-completion | ❌ | intervention |
| `AWAITING_ARBITRATOR` | ❌ | ❌ | ruling |
| `INTERVENTION_PENDING` | ❌ | ❌ | ruling |
| `CLOSED` | ❌ | ❌ | ❌ |

## API Endpoints

### Debates

| Method | Endpoint | Description | CLI Command |
|--------|----------|-------------|-------------|
| `POST` | `/debates` | Create debate + MOTION | `aw debate create` |
| `GET` | `/debates/:id` | Get debate + motion + arguments | `aw debate get-context` |
| `GET` | `/debates` | List debates | `aw debate list` |

### Arguments

| Method | Endpoint | Description | CLI Command |
|--------|----------|-------------|-------------|
| `POST` | `/debates/:id/arguments` | Submit CLAIM | `aw debate submit` |
| `POST` | `/debates/:id/appeal` | Submit APPEAL | `aw debate appeal` |
| `POST` | `/debates/:id/resolution` | Submit RESOLUTION | `aw debate request-completion` |
| `POST` | `/debates/:id/ruling` | Submit RULING | `aw debate ruling` |
| `POST` | `/debates/:id/intervention` | Submit INTERVENTION | `aw debate intervention` |

### Polling

| Method | Endpoint | Description | CLI Command |
|--------|----------|-------------|-------------|
| `GET` | `/debates/:id/wait` | Long polling | `aw debate wait` |

## Response Format

### Success Response

```json
{
  "success": true,
  "data": { ... }
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "code": "ACTION_NOT_ALLOWED",
    "message": "Role 'opponent' cannot submit in state 'AWAITING_PROPOSER'",
    "suggestion": "Wait for proposer to submit their argument",
    "current_state": "AWAITING_PROPOSER",
    "allowed_roles": ["proposer"]
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `DEBATE_NOT_FOUND` | 404 | Debate không tồn tại |
| `ARGUMENT_NOT_FOUND` | 404 | Argument không tồn tại |
| `INVALID_INPUT` | 400 | Input không hợp lệ |
| `ACTION_NOT_ALLOWED` | 409 | Action không hợp lệ trong state hiện tại |
| `AUTH_FAILED` | 401 | Authentication failed |
| `FORBIDDEN` | 403 | Không có quyền |

## Key Features

### Idempotency

Mọi write operation đều support `client_request_id`:
- Client gửi UUID unique per request
- Server check nếu `(debate_id, client_request_id)` đã tồn tại → return existing result
- Safe để retry khi network error

### Long Polling

- Server giữ connection tối đa 60s (`DEBATE_POLL_TIMEOUT_MS`)
- In-memory notifier wake up waiters khi có argument mới
- Double-check pattern để tránh missed signals
- Response: `{ has_new_argument: true/false, action: "...", argument: {...} }`

### Per-Debate Locking

- Mỗi debate có mutex lock riêng
- Đảm bảo chỉ 1 write operation tại 1 thời điểm per debate
- Tránh race condition khi concurrent submit

### SQLite Features

- WAL mode cho concurrent read
- `BEGIN IMMEDIATE` transaction cho writes
- Retry on `SQLITE_BUSY` với exponential backoff

## Development

```bash
cd devtools/common/debate-server

# Install dependencies
npm install

# Run in development
npx tsx src/index.ts

# Or with npm script
npm run dev

# Build
npm run build

# Run production
node dist/index.js
```

## Related

- **Spec:** `devdocs/misc/devtools/debate.md`
- **CLI:** `devtools/common/cli/devtool/aweave/debate/`
- **CLI Overview:** `devdocs/misc/devtools/common/cli/devtool/aweave/debate/OVERVIEW.md`
- **Plan:** `devdocs/misc/devtools/plans/260131-debate-server.md`
