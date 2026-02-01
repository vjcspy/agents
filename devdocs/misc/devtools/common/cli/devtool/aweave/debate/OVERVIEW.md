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
# Lấy data object
jq -r '.content[0].data'

# Lấy field cụ thể
jq -r '.content[0].data.id'
jq -r '.content[0].data.argument.id'
```

## Content Input Methods

Các commands có content (`create`, `submit`, `appeal`, `request-completion`, `ruling`) hỗ trợ 3 cách input:

| Option | Description |
|--------|-------------|
| `--file PATH` / `-f PATH` | Đọc content từ file |
| `--content TEXT` | Inline content |
| `--stdin` | Đọc từ stdin (pipe) |

**Lưu ý:** Chỉ được dùng MỘT trong 3 options. Error nếu không có hoặc có nhiều hơn 1.

---

## Commands Reference

### `generate-id`

Generate UUID để dùng cho `debate_id` hoặc `client_request_id`.

**Usage:**
```bash
aw debate generate-id [--format json|markdown]
```

**Options:**

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--format` | ❌ | `json` | Output format |

**Response:**
```json
{
  "success": true,
  "content": [{
    "type": "json",
    "data": {
      "id": "93d81b1a-0e66-4510-abfd-aa33b26cb82e"
    }
  }],
  "metadata": { "message": "Use this ID for debate_id or client_request_id" }
}
```

**Extract ID:**
```bash
aw debate generate-id | jq -r '.content[0].data.id'
```

---

### `create`

Tạo debate mới với MOTION. **Chỉ Proposer sử dụng.**

**Usage:**
```bash
aw debate create \
  --debate-id <uuid> \
  --title <string> \
  --type <debate_type> \
  (--file <path> | --content <text> | --stdin) \
  [--client-request-id <uuid>] \
  [--format json|markdown]
```

**Options:**

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--debate-id` | ✅ | - | UUID cho debate (dùng `generate-id`) |
| `--title` | ✅ | - | Tiêu đề debate |
| `--type` | ✅ | - | `coding_plan_debate` hoặc `general_debate` |
| `--file` / `-f` | ⚡ | - | Path đến file MOTION content |
| `--content` | ⚡ | - | Inline MOTION content |
| `--stdin` | ⚡ | - | Đọc MOTION từ stdin |
| `--client-request-id` | ❌ | auto | Idempotency key |
| `--format` | ❌ | `json` | Output format |

> ⚡ Một trong `--file`, `--content`, `--stdin` là **required**

**Response:**
```json
{
  "success": true,
  "content": [{
    "type": "json",
    "data": {
      "debate": {
        "id": "<debate_uuid>",
        "title": "Review implementation plan",
        "debate_type": "coding_plan_debate",
        "state": "AWAITING_OPPONENT",
        "created_at": "2026-01-31T10:00:00Z",
        "updated_at": "2026-01-31T10:00:00Z"
      },
      "argument": {
        "id": "<motion_uuid>",
        "debate_id": "<debate_uuid>",
        "parent_id": null,
        "type": "MOTION",
        "role": "proposer",
        "seq": 1,
        "content": "...",
        "created_at": "2026-01-31T10:00:00Z"
      }
    }
  }],
  "metadata": { "message": "Debate created successfully", "client_request_id": "<uuid>" }
}
```

**Quan trọng:**
- `data.argument.id` là MOTION ID, cần cho `wait` command tiếp theo
- State ban đầu luôn là `AWAITING_OPPONENT`

---

### `get-context`

Lấy thông tin debate + motion + arguments gần nhất. **Dùng khi resume debate.**

**Usage:**
```bash
aw debate get-context \
  --debate-id <uuid> \
  [--limit <N>] \
  [--format json|markdown]
```

**Options:**

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--debate-id` | ✅ | - | Debate UUID |
| `--limit` / `-l` | ❌ | 10 | Số arguments gần nhất |
| `--format` | ❌ | `json` | Output format |

**Response:**
```json
{
  "success": true,
  "content": [{
    "type": "json",
    "data": {
      "debate": {
        "id": "<debate_uuid>",
        "title": "...",
        "debate_type": "coding_plan_debate",
        "state": "AWAITING_PROPOSER",
        "created_at": "...",
        "updated_at": "..."
      },
      "motion": {
        "id": "<motion_uuid>",
        "debate_id": "<debate_uuid>",
        "parent_id": null,
        "seq": 1,
        "type": "MOTION",
        "role": "proposer",
        "content": "...",
        "created_at": "..."
      },
      "arguments": [
        {
          "id": "<argument_uuid>",
          "debate_id": "<debate_uuid>",
          "parent_id": "<motion_uuid>",
          "seq": 2,
          "type": "CLAIM",
          "role": "opponent",
          "content": "...",
          "created_at": "..."
        }
      ]
    }
  }]
}
```

**Notes:**
- `motion` luôn được include (là argument đầu tiên)
- `arguments` chứa N arguments gần nhất (không bao gồm motion), theo thứ tự `seq` tăng dần
- Dùng `debate.state` để xác định lượt của ai
- Dùng `arguments[-1]` để lấy argument cuối cùng

---

### `submit`

Submit CLAIM argument. **Proposer và Opponent sử dụng.**

**Usage:**
```bash
aw debate submit \
  --debate-id <uuid> \
  --role <proposer|opponent> \
  --target-id <argument_uuid> \
  (--file <path> | --content <text> | --stdin) \
  [--client-request-id <uuid>] \
  [--format json|markdown]
```

**Options:**

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--debate-id` | ✅ | - | Debate UUID |
| `--role` | ✅ | - | `proposer` hoặc `opponent` |
| `--target-id` | ✅ | - | UUID của argument đang phản hồi |
| `--file` / `-f` | ⚡ | - | Path đến file content |
| `--content` | ⚡ | - | Inline content |
| `--stdin` | ⚡ | - | Đọc từ stdin |
| `--client-request-id` | ❌ | auto | Idempotency key |
| `--format` | ❌ | `json` | Output format |

**Prerequisites:**
- State phải là `AWAITING_OPPONENT` nếu role = `opponent`
- State phải là `AWAITING_PROPOSER` nếu role = `proposer`

**Response:**
```json
{
  "success": true,
  "content": [{
    "type": "json",
    "data": {
      "argument": {
        "id": "<new_argument_uuid>",
        "debate_id": "<debate_uuid>",
        "parent_id": "<target_uuid>",
        "type": "CLAIM",
        "role": "proposer",
        "seq": 3,
        "content": "...",
        "created_at": "..."
      },
      "debate_state": "AWAITING_OPPONENT"
    }
  }],
  "metadata": { "message": "Argument submitted", "client_request_id": "<uuid>" }
}
```

**Quan trọng:**
- `data.argument.id` cần cho `wait` command tiếp theo
- `debate_state` cho biết state mới sau khi submit

---

### `wait`

Long polling chờ argument mới. **Proposer và Opponent sử dụng.**

**Usage:**
```bash
aw debate wait \
  --debate-id <uuid> \
  --role <proposer|opponent> \
  [--argument-id <uuid>] \
  [--format json|markdown]
```

**Options:**

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--debate-id` | ✅ | - | Debate UUID |
| `--role` | ✅ | - | `proposer` hoặc `opponent` |
| `--argument-id` | ❌ | - | Argument UUID đang chờ response |
| `--format` | ❌ | `json` | Output format |

**Behavior:**
- CLI poll server với timeout 65s per request
- Server giữ connection tối đa 60s
- Overall deadline mặc định 5 phút (`DEBATE_WAIT_DEADLINE`)

**Response (có argument mới):**
```json
{
  "success": true,
  "content": [{
    "type": "json",
    "data": {
      "status": "new_argument",
      "action": "respond",
      "debate_state": "AWAITING_PROPOSER",
      "argument": {
        "id": "<argument_uuid>",
        "debate_id": "<debate_uuid>",
        "parent_id": "<prev_uuid>",
        "seq": 2,
        "type": "CLAIM",
        "role": "opponent",
        "content": "...",
        "created_at": "..."
      },
      "next_argument_id_to_wait": "<argument_uuid>"
    }
  }]
}
```

**Response (timeout):**
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

**Action Values:**

| Action | Ý nghĩa | Hành động tiếp theo |
|--------|---------|---------------------|
| `respond` | Bên kia đã submit CLAIM | Phân tích và submit response |
| `wait_for_ruling` | Đang chờ Arbitrator | Call `wait` tiếp với `argument.id` |
| `align_to_ruling` | Arbitrator đã ruling (Proposer only) | Align theo ruling rồi submit |
| `wait_for_proposer` | Chờ Proposer align (Opponent only) | Call `wait` tiếp |
| `debate_closed` | Debate đã kết thúc | Dừng |

---

### `appeal`

Submit APPEAL yêu cầu Arbitrator phán xử. **Chỉ Proposer sử dụng.**

**Usage:**
```bash
aw debate appeal \
  --debate-id <uuid> \
  --target-id <argument_uuid> \
  (--file <path> | --content <text> | --stdin) \
  [--client-request-id <uuid>] \
  [--format json|markdown]
```

**Options:**

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--debate-id` | ✅ | - | Debate UUID |
| `--target-id` | ✅ | - | UUID argument đang tranh chấp |
| `--file` / `-f` | ⚡ | - | Path đến file content |
| `--content` | ⚡ | - | Inline content |
| `--stdin` | ⚡ | - | Đọc từ stdin |
| `--client-request-id` | ❌ | auto | Idempotency key |
| `--format` | ❌ | `json` | Output format |

**Prerequisites:**
- State phải là `AWAITING_PROPOSER`

**Response:**
```json
{
  "success": true,
  "content": [{
    "type": "json",
    "data": {
      "argument": {
        "id": "<appeal_uuid>",
        "debate_id": "<debate_uuid>",
        "parent_id": "<target_uuid>",
        "type": "APPEAL",
        "role": "proposer",
        "seq": 4,
        "content": "...",
        "created_at": "..."
      },
      "debate_state": "AWAITING_ARBITRATOR"
    }
  }],
  "metadata": { "message": "Appeal submitted", "client_request_id": "<uuid>" }
}
```

**Sau khi appeal:** Call `wait` với `argument.id` để chờ RULING

---

### `request-completion`

Request kết thúc debate (submit RESOLUTION). **Chỉ Proposer sử dụng.**

**Usage:**
```bash
aw debate request-completion \
  --debate-id <uuid> \
  --target-id <argument_uuid> \
  (--file <path> | --content <text> | --stdin) \
  [--client-request-id <uuid>] \
  [--format json|markdown]
```

**Options:**

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--debate-id` | ✅ | - | Debate UUID |
| `--target-id` | ✅ | - | UUID argument cuối cùng |
| `--file` / `-f` | ⚡ | - | Path đến file content |
| `--content` | ⚡ | - | Inline content |
| `--stdin` | ⚡ | - | Đọc từ stdin |
| `--client-request-id` | ❌ | auto | Idempotency key |
| `--format` | ❌ | `json` | Output format |

**Prerequisites:**
- State phải là `AWAITING_PROPOSER`

**Response:**
```json
{
  "success": true,
  "content": [{
    "type": "json",
    "data": {
      "argument": {
        "id": "<resolution_uuid>",
        "debate_id": "<debate_uuid>",
        "parent_id": "<target_uuid>",
        "type": "RESOLUTION",
        "role": "proposer",
        "seq": 5,
        "content": "...",
        "created_at": "..."
      },
      "debate_state": "AWAITING_ARBITRATOR"
    }
  }],
  "metadata": { "message": "Resolution submitted", "client_request_id": "<uuid>" }
}
```

**Sau khi request:** Call `wait` để chờ Arbitrator close hoặc reject

---

### `ruling` ⚠️ DEV-ONLY

Submit RULING. **Chỉ Arbitrator sử dụng. DEV-ONLY - dùng để test trước khi có Web UI.**

**Usage:**
```bash
aw debate ruling \
  --debate-id <uuid> \
  (--file <path> | --content <text> | --stdin) \
  [--close] \
  [--client-request-id <uuid>] \
  [--format json|markdown]
```

**Options:**

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--debate-id` | ✅ | - | Debate UUID |
| `--file` / `-f` | ⚡ | - | Path đến file content |
| `--content` | ⚡ | - | Inline content |
| `--stdin` | ⚡ | - | Đọc từ stdin |
| `--close` | ❌ | `false` | Close debate sau ruling |
| `--client-request-id` | ❌ | auto | Idempotency key |
| `--format` | ❌ | `json` | Output format |

**Prerequisites:**
- State phải là `AWAITING_ARBITRATOR` hoặc `INTERVENTION_PENDING`

**Response:**
```json
{
  "success": true,
  "content": [{
    "type": "json",
    "data": {
      "argument": {
        "id": "<ruling_uuid>",
        "debate_id": "<debate_uuid>",
        "parent_id": null,
        "type": "RULING",
        "role": "arbitrator",
        "seq": 6,
        "content": "...",
        "created_at": "..."
      },
      "debate_state": "AWAITING_PROPOSER"
    }
  }],
  "metadata": { "message": "Ruling submitted", "closed": false }
}
```

**Notes:**
- Nếu `--close`: `debate_state` = `CLOSED`
- Không có `--close`: `debate_state` = `AWAITING_PROPOSER` (Proposer phải align)

---

### `intervention` ⚠️ DEV-ONLY

Submit INTERVENTION (pause debate). **Chỉ Arbitrator. DEV-ONLY.**

**Usage:**
```bash
aw debate intervention \
  --debate-id <uuid> \
  [--client-request-id <uuid>] \
  [--format json|markdown]
```

**Options:**

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--debate-id` | ✅ | - | Debate UUID |
| `--client-request-id` | ❌ | auto | Idempotency key |
| `--format` | ❌ | `json` | Output format |

**Prerequisites:**
- State phải là `AWAITING_OPPONENT` hoặc `AWAITING_PROPOSER`

**Response:**
```json
{
  "success": true,
  "content": [{
    "type": "json",
    "data": {
      "argument": {
        "id": "<intervention_uuid>",
        "debate_id": "<debate_uuid>",
        "parent_id": null,
        "type": "INTERVENTION",
        "role": "arbitrator",
        "seq": 3,
        "content": "",
        "created_at": "..."
      },
      "debate_state": "INTERVENTION_PENDING"
    }
  }],
  "metadata": { "message": "Intervention submitted" }
}
```

**Sau intervention:** Phải submit `ruling` để tiếp tục hoặc close debate

---

### `list`

Liệt kê debates.

**Usage:**
```bash
aw debate list \
  [--state <state>] \
  [--limit <N>] \
  [--offset <N>] \
  [--format json|markdown]
```

**Options:**

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--state` | ❌ | - | Filter theo state |
| `--limit` / `-l` | ❌ | - | Max kết quả |
| `--offset` | ❌ | 0 | Pagination offset |
| `--format` | ❌ | `json` | Output format |

**Response:**
```json
{
  "success": true,
  "content": [{
    "type": "json",
    "data": {
      "debates": [
        {
          "id": "<debate_uuid>",
          "title": "...",
          "debate_type": "coding_plan_debate",
          "state": "AWAITING_PROPOSER",
          "created_at": "...",
          "updated_at": "..."
        }
      ]
    }
  }],
  "total_count": 42,
  "has_more": true
}
```

---

## Error Handling

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "ACTION_NOT_ALLOWED",
    "message": "Role 'opponent' cannot submit in state 'AWAITING_PROPOSER'",
    "suggestion": "Wait for proposer to submit their argument"
  },
  "content": [{
    "type": "json",
    "data": {
      "server_error": {
        "code": "ACTION_NOT_ALLOWED",
        "message": "...",
        "suggestion": "...",
        "current_state": "AWAITING_PROPOSER",
        "allowed_roles": ["proposer"]
      }
    }
  }]
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

---

## State Machine Reference

### States

| State | Description | Proposer | Opponent | Arbitrator |
|-------|-------------|----------|----------|------------|
| `AWAITING_OPPONENT` | Chờ Opponent phản hồi | wait | submit | intervention |
| `AWAITING_PROPOSER` | Chờ Proposer phản hồi | submit/appeal/request-completion | wait | intervention |
| `AWAITING_ARBITRATOR` | Chờ Arbitrator ruling | wait | wait | ruling |
| `INTERVENTION_PENDING` | Arbitrator đã intervention | wait | wait | ruling |
| `CLOSED` | Debate kết thúc | - | - | - |

### Allowed Actions by State

| State | `submit` | `appeal` | `request-completion` | `ruling` | `intervention` |
|-------|----------|----------|----------------------|----------|----------------|
| `AWAITING_OPPONENT` | opponent | ❌ | ❌ | ❌ | ✅ |
| `AWAITING_PROPOSER` | proposer | proposer | proposer | ❌ | ✅ |
| `AWAITING_ARBITRATOR` | ❌ | ❌ | ❌ | ✅ | ❌ |
| `INTERVENTION_PENDING` | ❌ | ❌ | ❌ | ✅ | ❌ |
| `CLOSED` | ❌ | ❌ | ❌ | ❌ | ❌ |

---

## Idempotency

- Tất cả write commands auto-generate `client_request_id` nếu không truyền
- Có thể truyền explicit `--client-request-id` để retry safely
- Server trả existing result nếu request đã xử lý (same `client_request_id` + `debate_id`)

---

## Related

- **Spec:** `devdocs/misc/devtools/debate.md`
- **Server:** `devtools/common/debate-server/`
- **Server Overview:** `devdocs/misc/devtools/common/debate-server/OVERVIEW.md`
- **Plan:** `devdocs/misc/devtools/plans/260131-debate-cli.md`
- **HTTP Client:** `aweave/http/client.py`
- **MCPResponse:** `aweave/mcp/response.py`
