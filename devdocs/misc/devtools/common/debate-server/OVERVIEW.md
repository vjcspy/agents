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

## Key Features

### State Machine

| State | Proposer | Opponent | Arbitrator |
|-------|----------|----------|------------|
| AWAITING_OPPONENT | ❌ | submit | intervention |
| AWAITING_PROPOSER | submit/appeal/resolution | ❌ | intervention |
| AWAITING_ARBITRATOR | ❌ | ❌ | ruling |
| INTERVENTION_PENDING | ❌ | ❌ | ruling |
| CLOSED | ❌ | ❌ | ❌ |

### Idempotency

Mọi write operation đều support `client_request_id` để handle retry safely.

### Long Polling

- Server giữ connection tối đa 60s
- In-memory notifier wake up waiters khi có argument mới
- Double-check pattern để tránh missed signals

## Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| `DEBATE_SERVER_HOST` | `127.0.0.1` | Bind address |
| `DEBATE_SERVER_PORT` | `3456` | Listen port |
| `DEBATE_AUTH_TOKEN` | (none) | Bearer token for auth |
| `DEBATE_DB_PATH` | `~/.aweave/debate.db` | SQLite database path |
| `DEBATE_POLL_TIMEOUT_MS` | `60000` | Long poll timeout |
| `DEBATE_HTTP_TIMEOUT_MS` | `65000` | HTTP keep-alive timeout |
| `DEBATE_MAX_CONTENT_LENGTH` | `10240` | Max content size (10KB) |

## API Endpoints

### Debates

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/debates` | Create debate + MOTION |
| `GET` | `/debates/:id?limit=N` | Get debate + motion + arguments |
| `GET` | `/debates?state=&limit=&offset=` | List debates |

### Arguments

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/debates/:id/arguments` | Submit CLAIM |
| `POST` | `/debates/:id/appeal` | Submit APPEAL |
| `POST` | `/debates/:id/resolution` | Submit RESOLUTION |
| `POST` | `/debates/:id/ruling` | Submit RULING (DEV-ONLY) |
| `POST` | `/debates/:id/intervention` | Submit INTERVENTION (DEV-ONLY) |

### Polling

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/debates/:id/wait?argument_id=&role=` | Long polling |

## Response Format

**Success:**
```json
{
  "success": true,
  "data": { ... }
}
```

**Error (flat fields, no nested details):**
```json
{
  "success": false,
  "error": {
    "code": "ACTION_NOT_ALLOWED",
    "message": "...",
    "suggestion": "...",
    "current_state": "AWAITING_PROPOSER",
    "allowed_roles": ["proposer"]
  }
}
```

## Development

```bash
cd devtools/common/debate-server

# Install dependencies
npm install

# Run in development
npx tsx src/index.ts

# Build
npm run build

# Run production
node dist/index.js
```

## Related

- **Spec:** `devdocs/misc/devtools/debate.md`
- **CLI:** `devtools/common/cli/devtool/aweave/debate/`
- **Plan:** `devdocs/misc/devtools/plans/260131-debate-server.md`
