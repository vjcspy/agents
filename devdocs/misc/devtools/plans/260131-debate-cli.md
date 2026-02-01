# 📋 [DEBATE-CLI: 2026-01-31] - Debate CLI (Python)

## References

- Spec document: `devdocs/misc/devtools/debate.md`
- DevTools overview: `devdocs/misc/devtools/OVERVIEW.md`
- **Docs CLI (pattern reference):** `devtools/common/cli/devtool/aweave/docs/cli.py`
- **MCPResponse module:** `devtools/common/cli/devtool/aweave/mcp/response.py`
- **HTTP Client:** `devtools/common/cli/devtool/aweave/http/client.py`
- Debate Server plan: `devdocs/misc/devtools/plans/260131-debate-server.md`

## 🎯 Objective

Xây dựng Python CLI (`aw debate`) để AI agents và human (Arbitrator) có thể tương tác với debate-server. CLI này là cầu nối chính giữa AI agents và hệ thống debate.

**Scope mở rộng:** Vì chưa có Web UI, bổ sung thêm commands cho Arbitrator (ruling, intervention) để test full flow.

### ⚠️ Key Considerations

1. **Reuse existing modules** - Dùng `typer` + `Annotated`, `aweave.mcp.response`, `aweave.http.client`
2. **Long Polling với overall deadline** - Default 5 phút, có thể override qua env
3. **Idempotency** - Auto-generate `client_request_id` nếu không truyền
4. **Arbitrator commands** - Dev-only, không thuộc contract chính, sẽ deprecate khi có Web UI
5. **MCPResponse format** - Cam kết output shape `content[0].data` cho AI agents parse

## 🔄 Implementation Plan

### Phase 1: Analysis & Preparation

- [ ] Review `aw docs` CLI structure và patterns
  - **Outcome**: Hiểu cách organize commands, MCPResponse, error handling, content ingestion (`_read_content`), output formatting
- [ ] Define all CLI commands và options
  - **Outcome**: Full command spec với tất cả parameters
- [ ] Verify HTTP client configuration
  - **Outcome**: Reuse `aweave.http.client.HTTPClient` với config

### Phase 2: Implementation (File/Code Structure)

```
devtools/common/cli/devtool/aweave/debate/
├── __init__.py                     # 🚧 TODO - Package init
├── cli.py                          # 🚧 TODO - Main CLI entry (typer app)
├── config.py                       # 🚧 TODO - Configuration (URLs, tokens)
├── commands/
│   ├── __init__.py                 # 🚧 TODO
│   ├── generate_id.py              # 🚧 TODO - Generate UUID
│   ├── create.py                   # 🚧 TODO - Create debate
│   ├── get_context.py              # 🚧 TODO - Get debate context
│   ├── submit.py                   # 🚧 TODO - Submit argument
│   ├── wait.py                     # 🚧 TODO - Wait for response
│   ├── appeal.py                   # 🚧 TODO - Submit appeal
│   ├── request_completion.py       # 🚧 TODO - Request completion
│   ├── ruling.py                   # 🚧 TODO - Submit ruling (DEV-ONLY)
│   ├── intervention.py             # 🚧 TODO - Submit intervention (DEV-ONLY)
│   └── list_debates.py             # 🚧 TODO - List debates
└── README.md                       # 🚧 TODO - CLI documentation
```

**Note:** Không tạo `models/` và `utils/` - dùng thin client pass-through JSON từ server, reuse `aweave.mcp.response` và `aweave.http.client`.

### Phase 3: Detailed Implementation Steps

#### Step 1: Project Setup

- [ ] Create package directory `devtools/common/cli/devtool/aweave/debate/`
- [ ] Setup `__init__.py` files
- [ ] Register `debate` subcommand trong main CLI (`aweave/cli.py`)
- [ ] Verify dependencies: `typer`, `httpx` (đã có qua `aweave.http.client`)

#### Step 2: Configuration

```python
# config.py
import os

DEBATE_SERVER_URL = os.getenv('DEBATE_SERVER_URL', 'http://127.0.0.1:3456')
DEBATE_AUTH_TOKEN = os.getenv('DEBATE_AUTH_TOKEN')  # None = no auth
DEBATE_WAIT_DEADLINE = int(os.getenv('DEBATE_WAIT_DEADLINE', 300))  # 5 minutes
POLL_TIMEOUT = 65  # seconds, > server 60s
```

#### Step 3: Reuse Existing Modules

**HTTP Client:** Reuse `aweave.http.client.HTTPClient`

> **Note:** HTTPClient signature: `HTTPClient(base_url, auth=None, headers=None, timeout=...)` 
> - Không có `auth_token` param, dùng `auth` hoặc `headers`
> - Timeout set ở constructor, không per-request
> - Raise `HTTPClientError` (không phải `httpx.HTTPStatusError`)

```python
# Trong commands
from aweave.http.client import HTTPClient, HTTPClientError
from .config import DEBATE_SERVER_URL, DEBATE_AUTH_TOKEN, POLL_TIMEOUT

def get_client(timeout: int = 30) -> HTTPClient:
    headers = {}
    if DEBATE_AUTH_TOKEN:
        headers['Authorization'] = f'Bearer {DEBATE_AUTH_TOKEN}'
    
    return HTTPClient(
        base_url=DEBATE_SERVER_URL,
        headers=headers if headers else None,
        timeout=timeout
    )

# Cho long polling cần timeout dài hơn
def get_poll_client() -> HTTPClient:
    return get_client(timeout=POLL_TIMEOUT)
```

**MCPResponse:** Reuse `aweave.mcp.response`

> **Note:** `MCPContent.type` expect `ContentType` enum, không phải string

```python
from aweave.mcp.response import MCPResponse, MCPError, MCPContent, ContentType

# Success
response = MCPResponse(
    success=True,
    content=[MCPContent(type=ContentType.JSON, data=server_data)]
)

# Error
response = MCPResponse(
    success=False,
    error=MCPError(code="ACTION_NOT_ALLOWED", message="...", suggestion="...")
)
```

**OutputFormat:** Define locally (giống `aw docs`)

> **Note:** `OutputFormat` KHÔNG có trong `aweave.mcp.response`, cần define locally

```python
# Trong cli.py hoặc riêng file
from enum import Enum

class OutputFormat(str, Enum):
    json = "json"
    markdown = "markdown"
```

**Content Reading:** Reuse pattern từ `aw docs`

> **Note:** Error phải output MCPResponse + exit code (agent-first), KHÔNG dùng typer auto-format

```python
def _read_content(
    file: Path | None,
    content: str | None,
    stdin: bool
) -> str | None:
    """
    Return content string, hoặc None nếu invalid input.
    Caller phải handle None và output MCPResponse error.
    """
    count = sum([file is not None, content is not None, stdin])
    if count != 1:
        return None  # Invalid - caller handle error
    
    if stdin:
        return sys.stdin.read()
    if file:
        if not file.exists():
            return None  # File not found - caller handle error
        return file.read_text()
    return content

# Usage trong command
def create_command(...):
    content = _read_content(file, content_str, stdin)
    if content is None:
        _output_error(
            MCPResponse(
                success=False,
                error=MCPError(
                    code="INVALID_INPUT",
                    message="Must provide exactly one of --file, --content, or --stdin",
                    suggestion="Use --file <path>, --content <text>, or --stdin"
                )
            ),
            format
        )
        raise typer.Exit(code=4)
```

#### Step 4: Output Format & Shape Cam Kết

**Align với `aw docs` pattern:**
- Chỉ support `json` và `markdown` (không có `plain` vì không có use-case)
- Default: `json`

```python
from enum import Enum

class OutputFormat(str, Enum):
    json = "json"
    markdown = "markdown"
```

**Output Shape Cam Kết (cho tất cả commands):**

Success:
```json
{
  "success": true,
  "content": [
    {
      "type": "json",
      "data": { /* command-specific data */ }
    }
  ],
  "metadata": { "message": "..." }
}
```

Error (Option B - MCPError tối giản + raw server error trong content):
```json
{
  "success": false,
  "error": {
    "code": "ACTION_NOT_ALLOWED",
    "message": "Role 'opponent' cannot submit in state 'AWAITING_PROPOSER'",
    "suggestion": "Wait for proposer to submit their argument"
  },
  "content": [
    {
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
    }
  ]
}
```

> **Note (Option B):**
> - `error` object chỉ chứa `code`, `message`, `suggestion` (MCPError core fields)
> - Context-specific fields (`current_state`, `allowed_roles`) nằm trong `content[0].data.server_error`
> - Agent cần parse cả `.error` (header) và `.content[0].data.server_error` (full context)

**Invariants:**
1. **Luôn có đúng 1 JSON content block** trong `content[]` (cả success và error)
2. **MCPError giữ nguyên core fields** - không extend class
3. **Agent có thể parse** bằng:
   - Success: `jq -r '.content[0].data'`
   - Error header: `jq -r '.error'`
   - Error context: `jq -r '.content[0].data.server_error'`

#### Step 5: Command Implementations

##### `aw debate generate-id`

```bash
aw debate generate-id
```

- Generate và return UUID
- No server call needed
- **Output shape cam kết:** `{ "success": true, "content": [{ "type": "json", "data": { "id": "<uuid>" } }] }`

##### `aw debate create`

```bash
aw debate create \
  --debate-id <uuid> \
  --title "Review implementation plan" \
  --debate-type coding_plan_debate \
  --file ./plan.md
  
# Hoặc với stdin
cat plan.md | aw debate create --debate-id ... --title ... --debate-type ... --stdin
```

| Option | Required | Description |
|--------|----------|-------------|
| `--debate-id` | ✅ | UUID từ generate-id |
| `--title, -t` | ✅ | Tiêu đề debate |
| `--debate-type` | ✅ | `coding_plan_debate`, `general_debate` |
| `--file, -f` | One of 3 | Path đến file MOTION content |
| `--content` | One of 3 | Content trực tiếp |
| `--stdin` | One of 3 | Read content từ stdin |
| `--client-request-id` | ❌ | Auto-generate nếu thiếu |
| `--format` | ❌ | `json` (default), `markdown` |

**Implementation:**
- [ ] Read content via `_read_content()`
- [ ] Auto-generate `client_request_id` nếu không truyền
- [ ] POST `/debates` với body
- [ ] Return debate_id, argument_id (MOTION), client_request_id (cho retry/debug)

##### `aw debate get-context`

```bash
aw debate get-context --debate-id <uuid> --argument-limit 10
```

| Option | Required | Description |
|--------|----------|-------------|
| `--debate-id` | ✅ | ID của debate |
| `--argument-limit, -l` | ❌ | Số arguments (default: 10) |
| `--format` | ❌ | `json` (default), `markdown` |

**Implementation:**
- [ ] GET `/debates/{id}?limit=N` (dùng endpoint có sẵn trong spec, thêm query param)
- [ ] Server response unwrap từ `response["data"]`
- [ ] Return debate + motion + arguments

**API Note:** Dùng `GET /debates/{id}?limit=N` (đúng spec trong `debate.md`), KHÔNG tạo endpoint `/context` mới.

**Response Schema (from server):**
```json
{
  "success": true,
  "data": {
    "debate": { "id": "...", "title": "...", "state": "...", ... },
    "motion": { "id": "...", "seq": 1, "type": "MOTION", ... },
    "arguments": [ { "id": "...", "seq": 2, "type": "CLAIM", ... } ]
  }
}
```

**Limit Semantics:**
- `motion` LUÔN included (không tính vào limit)
- `limit=N` → N arguments gần nhất (không tính MOTION)
- **Invariant:** Agent resume luôn có MOTION để giữ context

##### `aw debate submit`

```bash
aw debate submit \
  --debate-id <uuid> \
  --role proposer \
  --target-id <argument_uuid> \
  --content "My response..."

# Hoặc với stdin
cat response.md | aw debate submit --debate-id ... --role ... --target-id ... --stdin
```

| Option | Required | Description |
|--------|----------|-------------|
| `--debate-id` | ✅ | ID của debate |
| `--role` | ✅ | `proposer` hoặc `opponent` |
| `--target-id` | ✅ | ID argument đang phản hồi |
| `--file, -f` | One of 3 | Path đến file content |
| `--content` | One of 3 | Content trực tiếp |
| `--stdin` | One of 3 | Read content từ stdin |
| `--client-request-id` | ❌ | Auto-generate nếu thiếu |
| `--format` | ❌ | `json` (default), `markdown` |

**Implementation:**
- [ ] Read content via `_read_content()`
- [ ] Auto-generate `client_request_id` nếu không truyền
- [ ] POST `/debates/{id}/arguments`
- [ ] Return new argument_id, client_request_id

##### `aw debate wait`

```bash
aw debate wait \
  --debate-id <uuid> \
  --argument-id <uuid> \
  --role proposer

# Hoặc không có argument-id (wait from beginning)
aw debate wait --debate-id <uuid> --role opponent
```

| Option | Required | Description |
|--------|----------|-------------|
| `--debate-id` | ✅ | ID của debate |
| `--argument-id` | ❌ | ID argument cuối đã thấy (**CLI-level extension**: optional) |
| `--role` | ✅ | `proposer` hoặc `opponent` |
| `--format` | ❌ | `json` (default), `markdown` |

**CLI-level Extension - `--argument-id` optional:**
- Spec mô tả `argument_id` là required
- CLI cho phép omit để UX tốt hơn khi mới join debate
- Khi omit: CLI gửi empty string, server treat như `lastSeenSeq=0` → trả latest argument ngay

**Implementation:**
- [ ] Long polling với overall deadline (default 5 min)
- [ ] Retry loop với poll timeout 65s
- [ ] Return response với đầy đủ data cho agent ra quyết định

**Timeout Semantics:**
- Timeout là **expected control flow**, KHÔNG phải error
- Return `success=True` với `status: "timeout"`

```python
import httpx  # QUAN TRỌNG: cần import để catch TimeoutException

def wait_for_response(debate_id, argument_id, role, deadline):
    client = get_poll_client()  # timeout = POLL_TIMEOUT
    start = time.time()
    last_seen_seq = 0  # Track cho debug/resume
    
    while time.time() - start < deadline:
        try:
            response = client.get(
                f'/debates/{debate_id}/wait',
                params={'argument_id': argument_id or '', 'role': role}
            )
            # QUAN TRỌNG: Server trả envelope {success, data}
            # Unwrap để lấy actual data
            data = response.get("data", {})
            
            if data.get('has_new_argument'):
                # Return đầy đủ data cho agent
                return MCPResponse(
                    success=True,
                    content=[MCPContent(type=ContentType.JSON, data={
                        "status": "new_argument",
                        "action": data["action"],
                        "debate_state": data["debate_state"],
                        "argument": data["argument"],
                        "next_argument_id_to_wait": data["argument"]["id"]
                    })]
                )
            # has_new_argument=False → server poll timeout, retry
            # Lưu last_seen_seq cho debug (nếu server trả về)
            last_seen_seq = data.get("last_seen_seq", 0)
            
        except httpx.TimeoutException:
            # QUAN TRỌNG: httpx timeout throw TimeoutException, KHÔNG phải HTTPClientError
            continue  # retry on connection/read timeout
        except HTTPClientError as e:
            raise  # HTTP errors propagate (4xx/5xx)
    
    # Overall deadline reached - timeout là expected, không phải error
    return MCPResponse(
        success=True,
        content=[MCPContent(type=ContentType.JSON, data={
            "status": "timeout",
            "message": f"No response after {deadline}s",
            "debate_id": debate_id,
            "last_argument_id": argument_id,
            "last_seen_seq": last_seen_seq  # QoL cho debug/resume
        })]
    )
```

> **QUAN TRỌNG - Timeout Exception:**
> - `httpx.TimeoutException`: Connection/read timeout (retry)
> - `HTTPClientError`: HTTP 4xx/5xx errors (propagate)
> - Phải import `httpx` và catch đúng loại exception

##### `aw debate appeal`

```bash
aw debate appeal \
  --debate-id <uuid> \
  --target-id <argument_uuid> \
  --content "Appeal content with options..."

# Hoặc với stdin  
cat appeal.md | aw debate appeal --debate-id ... --target-id ... --stdin
```

| Option | Required | Description |
|--------|----------|-------------|
| `--debate-id` | ✅ | ID của debate |
| `--target-id` | ✅ | ID argument đang tranh cãi |
| `--file, -f` | One of 3 | Path đến file content |
| `--content` | One of 3 | Content trực tiếp |
| `--stdin` | One of 3 | Read content từ stdin |
| `--client-request-id` | ❌ | Auto-generate nếu thiếu |
| `--format` | ❌ | `json` (default), `markdown` |

**Implementation:**
- [ ] POST `/debates/{id}/appeal`
- [ ] Return new argument_id (APPEAL)

##### `aw debate request-completion`

```bash
aw debate request-completion \
  --debate-id <uuid> \
  --target-id <argument_uuid> \
  --content "Summary of agreed points..."
```

| Option | Required | Description |
|--------|----------|-------------|
| `--debate-id` | ✅ | ID của debate |
| `--target-id` | ✅ | ID argument cuối |
| `--file, -f` | One of 3 | Path đến file content |
| `--content` | One of 3 | Content trực tiếp |
| `--stdin` | One of 3 | Read content từ stdin |
| `--client-request-id` | ❌ | Auto-generate nếu thiếu |
| `--format` | ❌ | `json` (default), `markdown` |

**Implementation:**
- [ ] POST `/debates/{id}/resolution`
- [ ] Return new argument_id (RESOLUTION)

##### `aw debate ruling` (DEV-ONLY - Arbitrator)

> **⚠️ DEV-ONLY:** Command này KHÔNG thuộc contract chính. Dùng để test trước khi có Web UI. Server cần implement `/debates/{id}/ruling` endpoint (sync với server plan).

```bash
aw debate ruling \
  --debate-id <uuid> \
  --content "My ruling is..." \
  --close  # optional, để close debate
```

| Option | Required | Description |
|--------|----------|-------------|
| `--debate-id` | ✅ | ID của debate |
| `--file, -f` | One of 3 | Path đến file content |
| `--content` | One of 3 | Content trực tiếp |
| `--stdin` | One of 3 | Read content từ stdin |
| `--close` | ❌ | Flag để close debate |
| `--client-request-id` | ❌ | Auto-generate nếu thiếu (idempotency) |
| `--format` | ❌ | `json` (default), `markdown` |

**Implementation:**
- [ ] POST `/debates/{id}/ruling` với body `{ content, close?, client_request_id? }`
- [ ] Return new argument_id (RULING)

##### `aw debate intervention` (DEV-ONLY - Arbitrator)

> **⚠️ DEV-ONLY:** Command này KHÔNG thuộc contract chính. Dùng để test trước khi có Web UI. Server cần implement `/debates/{id}/intervention` endpoint (sync với server plan).

```bash
aw debate intervention --debate-id <uuid>
```

| Option | Required | Description |
|--------|----------|-------------|
| `--debate-id` | ✅ | ID của debate |
| `--client-request-id` | ❌ | Auto-generate nếu thiếu (idempotency) |
| `--format` | ❌ | `json` (default), `markdown` |

**Implementation:**
- [ ] POST `/debates/{id}/intervention` với body `{ client_request_id? }`
- [ ] Return new argument_id (INTERVENTION)

##### `aw debate list` (Utility)

```bash
aw debate list
aw debate list --state AWAITING_PROPOSER --limit 20
```

| Option | Required | Description |
|--------|----------|-------------|
| `--state` | ❌ | Filter by state (e.g. `AWAITING_PROPOSER`) |
| `--limit` | ❌ | Max results (default: 50) |
| `--offset` | ❌ | Pagination offset (default: 0) |
| `--format` | ❌ | `json` (default), `markdown` |

**Implementation:**
- [ ] GET `/debates?state=...&limit=...&offset=...`
- [ ] Server response unwrap từ `response["data"]`
- [ ] Order: `updated_at DESC` (most recent first)

**Response Schema (from server):**
```json
{
  "success": true,
  "data": {
    "debates": [ { "id": "...", "title": "...", "state": "...", ... } ],
    "total": 42
  }
}
```

#### Step 6: Error Handling & Exit Codes

**Align với `aw docs` exit codes:**

| Exit Code | Error Code | Description |
|-----------|------------|-------------|
| 0 | - | Success |
| 2 | `DEBATE_NOT_FOUND`, `ARGUMENT_NOT_FOUND` | Not found |
| 3 | `SERVER_ERROR`, `CONNECTION_ERROR` | Server/internal error |
| 4 | `INVALID_INPUT` | Invalid input |
| 5 | `ACTION_NOT_ALLOWED` | Action not allowed in current state |

**Pass-through server errors:**
- Server trả `ACTION_NOT_ALLOWED` với `current_state`, `allowed_roles`, `suggestion`
- CLI pass-through nguyên vẹn trong MCPResponse để agent handle
- **QUAN TRỌNG:** Giữ nguyên error payload từ server, đặc biệt các fields `current_state`, `allowed_roles`, `suggestion`

```python
# Example error handling - dùng HTTPClientError (không phải httpx.HTTPStatusError)
from aweave.http.client import HTTPClientError

def handle_server_error(e: HTTPClientError, format: OutputFormat):
    """
    Pass-through server error to MCPResponse.
    
    QUAN TRỌNG - HTTPClient hiện tại:
    - HTTPClientError chỉ có code/message (không có raw response body)
    - Để pass-through nguyên vẹn server error, CẦN extend HTTPClient
      hoặc catch response trước khi raise
    
    Hướng tiếp cận (Option B - không sửa MCPError):
    - MCPError giữ nguyên (code/message/suggestion only) làm "header"
    - Raw server error object đưa vào MCPResponse.content (JSON)
    """
    # Option 1: Nếu đã extend HTTPClient để giữ raw response
    # server_error = e.response_json.get("error", {}) if hasattr(e, 'response_json') else {}
    
    # Option 2 (fallback): Chỉ dùng code/message từ HTTPClientError
    code = getattr(e, 'code', 'SERVER_ERROR')
    message = str(e)
    
    exit_code = {
        "DEBATE_NOT_FOUND": 2,
        "ARGUMENT_NOT_FOUND": 2,
        "INVALID_INPUT": 4,
        "ACTION_NOT_ALLOWED": 5,
    }.get(code, 3)
    
    # MCPError chỉ giữ header (code/message/suggestion)
    # Nếu cần context-specific data (current_state, allowed_roles),
    # agent phải đọc từ MCPResponse.content
    _output_error(
        MCPResponse(
            success=False,
            error=MCPError(
                code=code,
                message=message,
                suggestion=getattr(e, 'suggestion', None),
            ),
            # Option B: Raw server error trong content (nếu có)
            # content=[MCPContent(type=ContentType.JSON, data=server_error)]
        ),
        format
    )
    raise typer.Exit(code=exit_code)
```

**Error Handling Strategy:**

> **QUYẾT ĐỊNH:** Chọn **Option B** - MCPError tối giản, raw server error vào content (nếu cần).
>
> **Lý do:**
> 1. Không cần sửa MCPError core class
> 2. Agent có thể parse raw error từ content nếu cần context (current_state, allowed_roles)
> 3. Giữ backward compatibility
>
> **TODO khi implement:**
> - Extend HTTPClient hoặc catch pattern để giữ raw response body trước khi raise
> - Nếu có raw body, include vào `MCPResponse.content` kèm `success=False`

#### Step 7: CLI Registration

```python
# cli.py
import typer
from typing import Annotated, Optional
from .commands import (
    generate_id, create, get_context, submit, wait,
    appeal, request_completion, ruling, intervention, list_debates
)

app = typer.Typer(help="Debate CLI - AI Agent debate management")

app.command("generate-id")(generate_id.command)
app.command("create")(create.command)
app.command("get-context")(get_context.command)
app.command("submit")(submit.command)
app.command("wait")(wait.command)
app.command("appeal")(appeal.command)
app.command("request-completion")(request_completion.command)
app.command("ruling")(ruling.command)  # DEV-ONLY
app.command("intervention")(intervention.command)  # DEV-ONLY
app.command("list")(list_debates.command)
```

#### Step 8: README Documentation

- [ ] Create `README.md` với:
  - Overview
  - All commands với examples
  - Configuration (env vars)
  - Exit codes
  - AI Agent workflow examples
  - **Output shape cam kết** (MCPResponse JSON structure)

#### Step 9: Testing

**Unit Tests:**
- [ ] Test generate-id
- [ ] Test content reading (`_read_content`)
- [ ] Test auto-generate client_request_id
- [ ] Test timeout handling (success=True với status=timeout)

**Integration Tests:**
- [ ] Test create debate (mock server hoặc integration)
- [ ] Test wait với timeout
- [ ] Test error responses pass-through
- [ ] Test ACTION_NOT_ALLOWED với current_state/allowed_roles/suggestion

**Invariant Tests từ spec:**
- [ ] "Submit sai lượt" → `ACTION_NOT_ALLOWED` với fields `current_state`, `allowed_roles`, `suggestion`
- [ ] Idempotency: submit cùng `client_request_id` 2 lần → return existing argument

**Full Flow Integration Test:**
- Terminal 1: Proposer
- Terminal 2: Opponent
- Terminal 3: Arbitrator (ruling/intervention)

#### Step 10: Integration Test Script

```bash
#!/bin/bash
# test_debate_flow.sh
# Cam kết output shape: content[0].data

# Terminal 1 - Proposer creates debate
DEBATE_ID=$(aw debate generate-id | jq -r '.content[0].data.id')

# client_request_id auto-generated nếu không truyền
RESULT=$(aw debate create \
  --debate-id $DEBATE_ID \
  --title "Test Debate" \
  --debate-type general_debate \
  --file ./motion.md)

MOTION_ID=$(echo $RESULT | jq -r '.content[0].data.argument_id')
CLIENT_REQ=$(echo $RESULT | jq -r '.content[0].data.client_request_id')

echo "Debate created: $DEBATE_ID"
echo "Motion ID: $MOTION_ID"
echo "Client Request ID: $CLIENT_REQ"
echo "Run in Terminal 2: aw debate get-context --debate-id $DEBATE_ID"
```

## 📊 Summary of Results

> Do not summarize until implementation is done

### ✅ Completed Achievements

- [ ] ...

## 🚧 Outstanding Issues & Follow-up

### ⚠️ Issues/Clarifications

- [ ] `ruling` và `intervention` commands là DEV-ONLY, sẽ deprecate khi có Web UI
- [ ] Server cần implement `/debates/{id}/ruling` và `/debates/{id}/intervention` endpoints (sync với server plan)
- [ ] Server endpoint `GET /debates/{id}` cần support query param `?limit=N` cho argument limit
- [ ] Consider adding `--verbose` flag cho debug output
- [ ] Verify `HTTPClientError` có `response_json` attribute để extract server error details
