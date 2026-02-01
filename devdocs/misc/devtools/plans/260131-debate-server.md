# 📋 [DEBATE-SERVER: 2026-01-31] - Debate Server (Node.js)

## References

- Spec document: `devdocs/misc/devtools/debate.md`
- DevTools overview: `devdocs/misc/devtools/OVERVIEW.md`
- Docs CLI (pattern reference): `devtools/common/cli/devtool/aweave/docs/`

## 🎯 Objective

Xây dựng Node.js server làm backend cho hệ thống debate giữa các AI agents. Server là single source of truth cho state machine, locking, và data persistence.

### ⚠️ Key Considerations

1. **State Machine là core** - Mọi action đều phải validate state trước khi execute
2. **Locking per debate** - Tại một thời điểm chỉ có 1 bên được write vào debate
3. **Idempotency** - Mọi submit đều cần `client_request_id` để handle retry
4. **Long Polling** - Server giữ connection tối đa 60s cho wait endpoint
5. **Security** - Bind localhost only, optional bearer token auth

## 🔄 Implementation Plan

### Phase 1: Analysis & Preparation

- [ ] Setup Node.js project structure
  - **Outcome**: Project với TypeScript, ESLint, Prettier
- [ ] Define dependencies
  - **Outcome**: `better-sqlite3`, `express`, `ws` (WebSocket), `uuid`
- [ ] Review database patterns từ `aw docs`
  - **Outcome**: WAL mode, BEGIN IMMEDIATE, retry on SQLITE_BUSY

### Phase 2: Implementation (File/Code Structure)

```
devtools/common/debate-server/
├── package.json                    # 🚧 TODO
├── tsconfig.json                   # 🚧 TODO
├── src/
│   ├── index.ts                    # 🚧 TODO - Entry point
│   ├── config.ts                   # 🚧 TODO - Environment config
│   ├── db/
│   │   ├── index.ts                # 🚧 TODO - Database connection
│   │   ├── schema.sql              # 🚧 TODO - SQLite schema
│   │   └── migrations/             # 🚧 TODO - Future migrations
│   ├── state-machine/
│   │   ├── states.ts               # 🚧 TODO - State definitions
│   │   ├── transitions.ts          # 🚧 TODO - Transition logic
│   │   └── validator.ts            # 🚧 TODO - canSubmit validation
│   ├── services/
│   │   ├── debate.service.ts       # 🚧 TODO - Debate CRUD
│   │   ├── argument.service.ts     # 🚧 TODO - Argument operations
│   │   └── lock.service.ts         # 🚧 TODO - Mutex locking per debate
│   ├── routes/
│   │   ├── index.ts                # 🚧 TODO - Route aggregator
│   │   ├── debates.ts              # 🚧 TODO - /debates endpoints
│   │   └── health.ts               # 🚧 TODO - Health check
│   ├── websocket/
│   │   ├── index.ts                # 🚧 TODO - WebSocket server
│   │   └── handlers.ts             # 🚧 TODO - Event handlers
│   ├── middleware/
│   │   ├── auth.ts                 # 🚧 TODO - Bearer token auth
│   │   └── error.ts                # 🚧 TODO - Error handler
│   └── types/
│       ├── debate.ts               # 🚧 TODO - Type definitions
│       └── envelope.ts             # 🚧 TODO - Server JSON envelope types (NOT MCP)
└── tests/                          # 🚧 TODO - Test files
```

### Phase 3: Detailed Implementation Steps

#### Step 1: Project Setup

- [ ] Init npm project với TypeScript
- [ ] Configure ESLint + Prettier
- [ ] Install dependencies: `better-sqlite3`, `express`, `ws`, `uuid`
- [ ] Setup build scripts

#### Step 2: Database Layer

- [ ] Create `schema.sql` với debates + arguments tables
- [ ] Implement database connection với WAL mode
- [ ] Implement `BEGIN IMMEDIATE` transaction wrapper
- [ ] Implement retry on SQLITE_BUSY
- [ ] Test database operations

**schema.sql:**
```sql
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- Schema versioning (giống aw docs pattern)
CREATE TABLE IF NOT EXISTS schema_meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

INSERT OR IGNORE INTO schema_meta (key, value) VALUES ('version', '1');

CREATE TABLE IF NOT EXISTS debates (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  debate_type TEXT NOT NULL,
  state TEXT NOT NULL DEFAULT 'AWAITING_OPPONENT',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS arguments (
  id TEXT PRIMARY KEY,
  debate_id TEXT NOT NULL REFERENCES debates(id),
  parent_id TEXT REFERENCES arguments(id),
  type TEXT NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  client_request_id TEXT,
  seq INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(debate_id, client_request_id),
  UNIQUE(debate_id, seq)
);

CREATE INDEX IF NOT EXISTS idx_arguments_debate_id ON arguments(debate_id);
CREATE INDEX IF NOT EXISTS idx_arguments_parent_id ON arguments(parent_id);
CREATE INDEX IF NOT EXISTS idx_arguments_seq ON arguments(debate_id, seq);
```

**Migration Strategy:**
- Check `schema_meta.version` on startup
- If version < current, run migrations sequentially
- Update version after each successful migration

**Ordering Note:**
- `created_at` chỉ có độ phân giải giây (SQLite `datetime('now')`)
- **MỌI ordering query PHẢI dùng `seq`**, không dùng `created_at`
- `seq` là source of truth cho thứ tự arguments trong debate

#### Step 3: State Machine

- [ ] Define states enum: `AWAITING_OPPONENT`, `AWAITING_PROPOSER`, `AWAITING_ARBITRATOR`, `INTERVENTION_PENDING`, `CLOSED`
- [ ] Define argument types enum: `MOTION`, `CLAIM`, `APPEAL`, `RULING`, `INTERVENTION`, `RESOLUTION`
- [ ] Implement `canSubmit(state, role, actionType)` validator
- [ ] Implement `calculateNextState(currentState, argumentType, options)` transition logic
- [ ] Unit test all valid/invalid transitions

**Validation Matrix:**
| State | Proposer | Opponent | Arbitrator |
|-------|----------|----------|------------|
| AWAITING_OPPONENT | ❌ | submit | intervention |
| AWAITING_PROPOSER | submit/appeal/completion | ❌ | intervention |
| AWAITING_ARBITRATOR | ❌ | ❌ | ruling |
| INTERVENTION_PENDING | ❌ | ❌ | ruling |
| CLOSED | ❌ | ❌ | ❌ |

#### Step 4: Locking Service

- [ ] Implement in-memory mutex Map per debate_id
- [ ] Implement `acquire(debateId)` với timeout
- [ ] Implement `release(debateId)`
- [ ] Wrap all write operations với lock
- [ ] Implement in-memory notifier (EventEmitter) per debate để wake up waiters

```typescript
// Pseudo-code
class LockService {
  private locks = new Map<string, Mutex>();
  private notifiers = new Map<string, EventEmitter>();
  
  async withLock<T>(debateId: string, fn: () => Promise<T>): Promise<T> {
    const mutex = this.getOrCreate(debateId);
    const release = await mutex.acquire();
    try {
      return await fn();
    } finally {
      release();
    }
  }
  
  // Notify ALL waiters khi có argument mới
  // QUAN TRỌNG: Dùng emit() không phải emit once - tất cả listeners đều nhận
  notifyNewArgument(debateId: string, argument: Argument): void {
    const emitter = this.notifiers.get(debateId);
    if (emitter) emitter.emit('new_argument', argument);
  }
  
  // Wait for new argument với timeout
  // QUAN TRỌNG: Mỗi waiter tự attach listener riêng, tất cả đều được wake
  // Sau khi wake, waiter phải tự verify seq > lastSeenSeq (đã handle trong waitForResponse)
  async waitForArgument(debateId: string, timeoutMs: number): Promise<Argument | null> {
    const emitter = this.getOrCreateNotifier(debateId);
    return new Promise((resolve) => {
      const timer = setTimeout(() => {
        emitter.removeListener('new_argument', handler);
        resolve(null);
      }, timeoutMs);
      
      const handler = (arg: Argument) => {
        clearTimeout(timer);
        emitter.removeListener('new_argument', handler);
        resolve(arg);
      };
      
      // Dùng .on() không phải .once() để có thể removeListener
      emitter.on('new_argument', handler);
    });
  }
}
```

**QUAN TRỌNG - Multi-listener support:**
- Khi có argument mới, `notifyNewArgument()` wake TẤT CẢ waiters (proposer + opponent + multiple clients)
- Mỗi waiter sau khi wake phải tự verify `arg.seq > lastSeenSeq` (đã handle trong `waitForResponse`)
- Tránh "missed signal" race: attach listener TRƯỚC khi check latest (xem Step 7)
- **Invariant:** Khi wake, luôn trả `latestArg` có `seq > lastSeenSeq`

**Lock/Notifier Lifecycle - Cleanup Strategy:**
- `locks` và `notifiers` Map sẽ tăng theo số debates
- **Phase 1:** Dùng TTL/LRU eviction (vd: cleanup sau 30 phút không hoạt động) - đơn giản, không cần track waiters count
- **Phase 2 (optional):** Cleanup khi debate `CLOSED` + không còn waiters (cần refcount)
- **Note:** Phase 1 đủ cho MVP, tránh memory leak mà không phức tạp hóa implementation

#### Step 5: Core Services

**DebateService:**
- [ ] `create(debateId, title, debateType, motionContent, clientRequestId)` → creates debate + MOTION argument
- [ ] `getById(debateId)` → debate + state
- [ ] `getContext(debateId, argumentLimit)` → debate + MOTION + last N arguments

**ArgumentService:**
- [ ] `submit(debateId, role, targetId, content, clientRequestId)` → CLAIM argument
- [ ] `submitAppeal(debateId, targetId, content, clientRequestId)` → APPEAL argument
- [ ] `submitResolution(debateId, targetId, content, clientRequestId)` → RESOLUTION argument
- [ ] `submitRuling(debateId, content, close?, clientRequestId?)` → RULING argument (DEV-ONLY Arbitrator)
- [ ] `submitIntervention(debateId, clientRequestId?)` → INTERVENTION argument (DEV-ONLY Arbitrator)

> **Note:** `clientRequestId` optional cho ruling/intervention để giữ nhất quán idempotency across hệ thống. Nếu không cung cấp, server tự generate (không idempotent).

**QUAN TRỌNG - Thứ tự operations trong critical section:**

Idempotency check PHẢI nằm trong cùng lock + transaction để tránh race condition:

```typescript
async submitArgument(debateId, role, targetId, content, clientRequestId) {
  return this.lockService.withLock(debateId, async () => {
    // BEGIN IMMEDIATE transaction
    // QUAN TRỌNG: Capture result từ transaction để dùng sau commit
    const argument = this.db.transaction(() => {
      // 1. Idempotency check TRONG transaction
      const existing = db.findByClientRequestId(debateId, clientRequestId);
      if (existing) return { argument: existing, isExisting: true };
      
      // 2. Validate state/role
      const debate = db.getDebate(debateId);
      if (!canSubmit(debate.state, role, 'CLAIM')) {
        throw new ActionNotAllowedError(...);
      }
      
      // 3. Compute seq
      const seq = db.getNextSeq(debateId);
      
      // 4. Insert argument
      const newArg = db.insertArgument({
        id: generateUUID(),
        debate_id: debateId,
        parent_id: targetId,
        type: 'CLAIM',
        role,
        content,
        client_request_id: clientRequestId,
        seq,
      });
      
      // 5. Update debate state + updated_at
      const newState = calculateNextState(debate.state, 'CLAIM', role);
      db.updateDebateState(debateId, newState);
      
      return { argument: newArg, isExisting: false };
    })(); // COMMIT
    
    // 6. Notify waiters SAU transaction commit (chỉ nếu là argument mới)
    if (!argument.isExisting) {
      this.lockService.notifyNewArgument(debateId, argument.argument);
    }
    
    return argument.argument;
  });
}
```

**State Transition Mapping:**

| Action | By | From States | To State |
|--------|-----|-------------|----------|
| `create` (MOTION) | Proposer | - | `AWAITING_OPPONENT` |
| `submit` (CLAIM) | Opponent | `AWAITING_OPPONENT` | `AWAITING_PROPOSER` |
| `submit` (CLAIM) | Proposer | `AWAITING_PROPOSER` | `AWAITING_OPPONENT` |
| `appeal` (APPEAL) | Proposer | `AWAITING_PROPOSER` | `AWAITING_ARBITRATOR` |
| `resolution` (RESOLUTION) | Proposer | `AWAITING_PROPOSER` | `AWAITING_ARBITRATOR` |
| `intervention` (INTERVENTION) | Arbitrator | `AWAITING_*` | `INTERVENTION_PENDING` |
| `ruling` (RULING, close=false) | Arbitrator | `AWAITING_ARBITRATOR`, `INTERVENTION_PENDING` | `AWAITING_PROPOSER` |
| `ruling` (RULING, close=true) | Arbitrator | `AWAITING_ARBITRATOR`, `INTERVENTION_PENDING` | `CLOSED` |

#### Step 6: REST API Endpoints

| Method | Endpoint | Handler | Description |
|--------|----------|---------|-------------|
| POST | `/debates` | createDebate | Tạo debate mới + MOTION |
| GET | `/debates/:id` | getDebate | Lấy debate info + arguments (với `?limit=N`) |
| POST | `/debates/:id/arguments` | submitArgument | Submit CLAIM |
| POST | `/debates/:id/appeal` | submitAppeal | Submit APPEAL |
| POST | `/debates/:id/resolution` | requestCompletion | Submit RESOLUTION |
| POST | `/debates/:id/ruling` | submitRuling | Submit RULING (DEV-ONLY Arbitrator) |
| POST | `/debates/:id/intervention` | submitIntervention | Submit INTERVENTION (DEV-ONLY Arbitrator) |
| GET | `/debates/:id/wait` | waitForResponse | Long polling |
| GET | `/debates` | listDebates | List all debates |
| GET | `/health` | healthCheck | Health check |

**API Note:**
- `GET /debates/:id?limit=N` trả về debate + arguments (đúng spec `debate.md`)
- KHÔNG tạo endpoint `/context` riêng để tránh 2 source of truth

**GET /debates/:id Response Schema:**
```json
{
  "success": true,
  "data": {
    "debate": {
      "id": "uuid",
      "title": "string",
      "debate_type": "coding_plan_debate|general_debate",
      "state": "AWAITING_OPPONENT|...",
      "created_at": "YYYY-MM-DD HH:MM:SS",
      "updated_at": "YYYY-MM-DD HH:MM:SS"
    },
    "motion": {
      "id": "uuid",
      "seq": 1,
      "type": "MOTION",
      "role": "proposer",
      "content": "string",
      "created_at": "YYYY-MM-DD HH:MM:SS"
    },
    "arguments": [
      { "id": "...", "seq": 2, "type": "CLAIM", "role": "opponent", "parent_id": "...", "content": "...", "created_at": "..." }
    ]
  }
}
```

> **debate_type enum:** `coding_plan_debate` | `general_debate` (theo spec `debate.md`)
>
> **Datetime format:** `YYYY-MM-DD HH:MM:SS` (SQLite `datetime('now')` format, UTC)

**Semantics của `limit` query param:**
- `motion` LUÔN được include (không tính vào limit)
- `limit=N` trả N arguments gần nhất (không tính MOTION)
- `limit=0` → `arguments=[]` (chỉ debate + motion)
- `limit` không set → trả tất cả arguments
- `limit` âm hoặc không phải int → `INVALID_INPUT` error
- **Invariant:** Agent resume luôn có MOTION để giữ context

**GET /debates (List) Response Schema:**
```json
{
  "success": true,
  "data": {
    "debates": [
      { "id": "...", "title": "...", "state": "...", "created_at": "...", "updated_at": "..." }
    ],
    "total": 42
  }
}
```

**List Query Params:**
- `state`: Filter by state (optional, e.g. `?state=AWAITING_PROPOSER`)
- `limit`: Max results (optional, default 50)
- `offset`: Pagination offset (optional, default 0)
- Order: `updated_at DESC` (most recent first)

**Request/Response Format:**

> **Note:** Server trả JSON envelope ổn định, KHÔNG dùng MCPResponse. CLI sẽ wrap thành MCPResponse cho AI agents.

**Success Response (THỐNG NHẤT cho tất cả endpoints, kể cả wait):**
```json
{
  "success": true,
  "data": { ... }
}
```

**Error Response:**
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

**Error Envelope Structure:**
- `code`: Error code string
- `message`: Human-readable message
- `suggestion`: (Optional) Gợi ý cho user/agent - **top-level trong error object**
- `current_state`, `allowed_roles`: Các fields context-specific - **top-level trong error object** (không nested trong `details`)

> **Note:** CLI wrap error vào MCPResponse. MCPError chỉ chứa `code/message/suggestion`; raw server error (bao gồm `current_state`, `allowed_roles`) nằm trong `content[0].data.server_error`. Xem CLI plan Option B.

**Error Codes:**
- `DEBATE_NOT_FOUND` - Debate không tồn tại
- `ARGUMENT_NOT_FOUND` - Argument không tồn tại
- `ACTION_NOT_ALLOWED` - Action không hợp lệ trong state hiện tại
- `INVALID_INPUT` - Input không hợp lệ
- `CONTENT_TOO_LARGE` - Content vượt quá max size

**Request Schemas (tất cả endpoints):**

```typescript
// POST /debates - Create debate
{
  debate_id: string,           // Required - client-generated UUID
  title: string,               // Required
  debate_type: "coding_plan_debate" | "general_debate",  // Required
  motion_content: string,      // Required - content của MOTION
  client_request_id: string    // Required - idempotency key
}

// POST /debates/:id/arguments - Submit CLAIM
{
  role: "proposer" | "opponent",  // Required
  target_id: string,              // Required - parent argument ID
  content: string,                // Required
  client_request_id: string       // Required - idempotency key
}

// POST /debates/:id/appeal - Submit APPEAL
{
  target_id: string,              // Required - argument đang tranh cãi
  content: string,                // Required - appeal reason + options
  client_request_id: string       // Required - idempotency key
}

// POST /debates/:id/resolution - Request completion
{
  target_id: string,              // Required - last argument ID
  content: string,                // Required - summary of agreed points
  client_request_id: string       // Required - idempotency key
}

// POST /debates/:id/ruling - DEV-ONLY Arbitrator
{
  content: string,                // Required - ruling content
  close?: boolean,                // Optional - close debate (default: false)
  client_request_id?: string      // Optional - idempotency key (auto-gen if missing)
}

// POST /debates/:id/intervention - DEV-ONLY Arbitrator
{
  client_request_id?: string      // Optional - idempotency key (auto-gen if missing)
}

// GET /debates/:id/wait - Long polling (query params)
// ?argument_id=<uuid>&role=<proposer|opponent>
// argument_id: Optional - last seen argument ID (empty = from beginning)
// role: Required
```

#### Step 7: Long Polling Endpoint

- [ ] Implement `/debates/:id/wait` với params: `argument_id`, `role`
- [ ] Server holds connection up to 60s
- [ ] Sử dụng in-memory notifier để wake up (không poll DB mỗi giây)
- [ ] Return appropriate `action` based on role và new argument type
- [ ] Handle connection timeout gracefully

**Wait Endpoint Semantics:**

**Input (query params):**
- `argument_id`: ID của argument cuối cùng mà client đã thấy (last seen). **OPTIONAL**
  - Missing param (`/wait?role=...`) → `lastSeenSeq=0`
  - Empty string (`/wait?argument_id=&role=...`) → `lastSeenSeq=0`
  - Invalid UUID → `INVALID_INPUT` error
  - UUID không thuộc debate → `INVALID_INPUT` error
- `role`: `proposer` hoặc `opponent` (**REQUIRED**)

**Logic:**
```typescript
async waitForResponse(debateId: string, lastSeenArgId: string | null, role: string) {
  // 1. Xác định lastSeenSeq
  let lastSeenSeq = 0;
  if (lastSeenArgId) {
    const lastSeenArg = db.getArgument(lastSeenArgId);
    if (!lastSeenArg || lastSeenArg.debate_id !== debateId) {
      throw new InvalidInputError('argument_id does not belong to this debate');
    }
    lastSeenSeq = lastSeenArg.seq;
  }
  
  // 2. Lấy debate để check state
  const debate = db.getDebate(debateId);
  if (!debate) throw new NotFoundError('Debate not found');
  
  // 3. Check ngay: có argument mới không (seq > lastSeenSeq)
  const latestArg = db.getLatestArgument(debateId);
  if (latestArg && latestArg.seq > lastSeenSeq) {
    // WRAP trong success envelope
    return { 
      success: true, 
      data: buildResponse(latestArg, debate.state, role) 
    };
  }
  
  // 4. Không có argument mới → attach listener rồi double-check
  const listenerPromise = lockService.waitForArgument(debateId, 60000);
  
  // 5. Double-check ngay sau attach (tránh missed signal race)
  const latestArgAfterAttach = db.getLatestArgument(debateId);
  if (latestArgAfterAttach && latestArgAfterAttach.seq > lastSeenSeq) {
    return { 
      success: true, 
      data: buildResponse(latestArgAfterAttach, debate.state, role) 
    };
  }
  
  // 6. Chờ notifier (max 60s)
  const newArg = await listenerPromise;
  
  if (newArg) {
    // Re-fetch debate state sau khi có argument mới
    const updatedDebate = db.getDebate(debateId);
    return { 
      success: true, 
      data: buildResponse(newArg, updatedDebate.state, role) 
    };
  }
  
  // 7. Timeout - CŨNG wrap trong success envelope (không phải error)
  // NOTE: Không kèm debate_state vì timeout chỉ là "không có gì mới"
  // Agent muốn biết state hiện tại có thể gọi GET /debates/:id
  return { 
    success: true, 
    data: { 
      has_new_argument: false,
      debate_id: debateId,
      last_seen_seq: lastSeenSeq
    } 
  };
}

// DECISION: Timeout response KHÔNG kèm debate_state
// Lý do: Đơn giản hóa contract; agent cần state thì gọi GET /debates/:id
// Alternative (future): Thêm debate_state nếu agent feedback cần
```

**Note về listener cleanup:**
- Nếu return sớm ở step 5 (double-check hit), listener vẫn đang chờ
- Listener có setTimeout 60s nên sẽ tự cleanup, không leak
- Nếu muốn cleanup ngay, có thể implement AbortController pattern (optional optimization)

**Response theo role:**
```typescript
function buildResponse(arg: Argument, debateState: string, role: string) {
  // Handle CLOSED state first (không cần map)
  const action = debateState === 'CLOSED' 
    ? 'debate_closed'
    : getAction(arg, role);
  
  // Return đầy đủ fields để CLI/agent không phải suy luận
  return {
    has_new_argument: true,
    action,
    debate_state: debateState,
    argument: {
      id: arg.id,
      seq: arg.seq,
      type: arg.type,
      role: arg.role,
      parent_id: arg.parent_id,
      content: arg.content,
      created_at: arg.created_at
    }
  };
}

function getAction(arg: Argument, role: string): string {
  const actionMap: Record<string, string> = {
    // Opponent vừa CLAIM → Proposer respond
    'CLAIM:opponent:proposer': 'respond',
    // Proposer vừa CLAIM → Opponent respond  
    'CLAIM:proposer:opponent': 'respond',
    // APPEAL → cả 2 wait for ruling
    'APPEAL:proposer:proposer': 'wait_for_ruling',
    'APPEAL:proposer:opponent': 'wait_for_ruling',
    // RESOLUTION → cả 2 wait for ruling
    'RESOLUTION:proposer:proposer': 'wait_for_ruling',
    'RESOLUTION:proposer:opponent': 'wait_for_ruling',
    // RULING → Proposer align, Opponent wait
    'RULING:arbitrator:proposer': 'align_to_ruling',
    'RULING:arbitrator:opponent': 'wait_for_proposer',
    // INTERVENTION → cả 2 wait for ruling
    'INTERVENTION:arbitrator:proposer': 'wait_for_ruling',
    'INTERVENTION:arbitrator:opponent': 'wait_for_ruling',
  };
  
  const key = `${arg.type}:${arg.role}:${role}`;
  return actionMap[key] || 'unknown';
}
```

**Wait Response Fields (đầy đủ cho CLI/agent):**
- `has_new_argument`: boolean
- `action`: string (respond, wait_for_ruling, align_to_ruling, wait_for_proposer, debate_closed)
- `debate_state`: string (state SAU khi insert argument)
- `argument`: object đầy đủ (`id`, `seq`, `type`, `role`, `parent_id`, `content`, `created_at`)

#### Step 8: WebSocket Server (cho Web sau này)

- [ ] Setup WebSocket server on same port
- [ ] Implement room-based subscription per debate_id
- [ ] Broadcast `new_argument` event sau mỗi insert
- [ ] Handle `submit_ruling`, `submit_intervention` từ web client
- [ ] **Note:** WebSocket chủ yếu cho Web UI, CLI dùng Long Polling

**WebSocket Auth Story:**
- Nếu `DEBATE_AUTH_TOKEN` được set:
  - WS handshake PHẢI check token (via query param `?token=...` hoặc header)
  - Reject connection nếu token không match
- Nếu `DEBATE_AUTH_TOKEN` không set:
  - WS không require auth (dev mode)
- **Alternative:** Disable WS hoàn toàn khi auth enabled (simpler, acceptable cho phase 1)

#### Step 9: Middleware

- [ ] Auth middleware: check `Authorization: Bearer <token>` nếu env `DEBATE_AUTH_TOKEN` set
- [ ] Error handler: format errors theo JSON error envelope (`{ success: false, error: { code, message, suggestion?, ...context_fields } }`) - flat, không `details`
- [ ] Request logger

**Error Handler Example:**
```typescript
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  const statusCode = err instanceof NotFoundError ? 404 
    : err instanceof InvalidInputError ? 400
    : err instanceof ActionNotAllowedError ? 403
    : 500;
  
  // Error fields flat (không nested trong details)
  const errorResponse: any = {
    success: false,
    error: {
      code: err.code || 'INTERNAL_ERROR',
      message: err.message,
    }
  };
  
  // Add optional fields flat vào error object
  if (err.suggestion) errorResponse.error.suggestion = err.suggestion;
  if (err instanceof ActionNotAllowedError) {
    errorResponse.error.current_state = err.currentState;
    errorResponse.error.allowed_roles = err.allowedRoles;
  }
  
  res.status(statusCode).json(errorResponse);
});
```

#### Step 10: Configuration

```typescript
// config.ts
import os from 'os';
import path from 'path';

// Expand ~ thành home directory (Node.js không tự expand)
function expandHome(filepath: string): string {
  if (filepath.startsWith('~')) {
    return path.join(os.homedir(), filepath.slice(1));
  }
  return filepath;
}

const DEFAULT_DB_PATH = path.join(os.homedir(), '.aweave', 'debate.db');

export const config = {
  port: parseInt(process.env.DEBATE_SERVER_PORT || '3456'),
  host: process.env.DEBATE_SERVER_HOST || '127.0.0.1',
  authToken: process.env.DEBATE_AUTH_TOKEN, // undefined = no auth
  dbPath: expandHome(process.env.DEBATE_DB_PATH || DEFAULT_DB_PATH),
  pollTimeout: 60, // seconds - cho wait endpoint
  maxContentLength: 10 * 1024, // 10KB
  httpTimeout: 65, // seconds - HTTP keep-alive/timeout (> pollTimeout)
};

// QUAN TRỌNG: Express/Node default timeout có thể < 60s
// PHẢI set explicit để đảm bảo long polling hoạt động
// app.use((req, res, next) => {
//   res.setTimeout(config.httpTimeout * 1000);
//   next();
// });
// Hoặc set server.timeout = config.httpTimeout * 1000;
```

**Startup:**
- [ ] Ensure `.aweave` directory exists (`fs.mkdirSync(dir, { recursive: true })`)
- [ ] Initialize database with schema if not exists
- [ ] Check and run migrations if needed

#### Step 11: Testing

- [ ] Unit tests cho state machine transitions
- [ ] Unit tests cho locking service
- [ ] Integration tests cho API endpoints
- [ ] Test idempotency với duplicate requests
- [ ] Test long polling timeout behavior
- [ ] Test concurrent submissions (race conditions)

## 📊 Summary of Results

> Do not summarize until implementation is done

### ✅ Completed Achievements

- [ ] ...

## 🚧 Outstanding Issues & Follow-up

### ⚠️ Issues/Clarifications

- [ ] WebSocket implementation có thể defer đến khi build Web UI
- [ ] Consider adding rate limiting nếu cần
