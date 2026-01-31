# 📋 [DEBATE-CLI: 2026-01-31] - Debate CLI (Python)

## References

- Spec document: `devdocs/misc/devtools/debate.md`
- DevTools overview: `devdocs/misc/devtools/OVERVIEW.md`
- Docs CLI (pattern reference): `devtools/common/cli/devtool/aweave/docs/`
- Debate Server plan: `devdocs/misc/devtools/plans/260131-debate-server.md`

## 🎯 Objective

Xây dựng Python CLI (`aw debate`) để AI agents và human (Arbitrator) có thể tương tác với debate-server. CLI này là cầu nối chính giữa AI agents và hệ thống debate.

**Scope mở rộng:** Vì chưa có Web UI, bổ sung thêm commands cho Arbitrator (ruling, intervention) để test full flow.

### ⚠️ Key Considerations

1. **Follow pattern từ `aw docs`** - Copy structure, error handling, MCPResponse format
2. **Long Polling với overall deadline** - Default 5 phút, có thể override qua env
3. **Idempotency** - Tất cả submit commands đều generate `client_request_id`
4. **Arbitrator commands** - Tạm thời để test, có thể deprecate khi có Web UI
5. **MCPResponse format** - Output phải parse được bởi AI agents

## 🔄 Implementation Plan

### Phase 1: Analysis & Preparation

- [ ] Review `aw docs` CLI structure và patterns
  - **Outcome**: Hiểu cách organize commands, error handling, DB interaction
- [ ] Define all CLI commands và options
  - **Outcome**: Full command spec với tất cả parameters
- [ ] Setup HTTP client configuration
  - **Outcome**: Base URL, auth token, timeout settings

### Phase 2: Implementation (File/Code Structure)

```
devtools/common/cli/devtool/aweave/debate/
├── __init__.py                     # 🚧 TODO - Package init
├── cli.py                          # 🚧 TODO - Main CLI entry (click commands)
├── client.py                       # 🚧 TODO - HTTP client wrapper
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
│   ├── ruling.py                   # 🚧 TODO - Submit ruling (Arbitrator)
│   └── intervention.py             # 🚧 TODO - Submit intervention (Arbitrator)
├── models/
│   ├── __init__.py                 # 🚧 TODO
│   ├── debate.py                   # 🚧 TODO - Debate model
│   └── argument.py                 # 🚧 TODO - Argument model
├── utils/
│   ├── __init__.py                 # 🚧 TODO
│   ├── response.py                 # 🚧 TODO - MCPResponse formatter
│   └── errors.py                   # 🚧 TODO - Error codes và handling
└── README.md                       # 🚧 TODO - CLI documentation
```

### Phase 3: Detailed Implementation Steps

#### Step 1: Project Setup

- [ ] Create package directory `devtools/common/cli/devtool/aweave/debate/`
- [ ] Setup `__init__.py` files
- [ ] Register `debate` subcommand trong main CLI (`aweave/cli.py`)
- [ ] Add dependencies nếu cần (requests đã có)

#### Step 2: Configuration

```python
# config.py
import os

DEBATE_SERVER_URL = os.getenv('DEBATE_SERVER_URL', 'http://127.0.0.1:3456')
DEBATE_AUTH_TOKEN = os.getenv('DEBATE_AUTH_TOKEN')  # None = no auth
DEBATE_WAIT_DEADLINE = int(os.getenv('DEBATE_WAIT_DEADLINE', 300))  # 5 minutes
POLL_TIMEOUT = 65  # seconds, > server 60s
```

#### Step 3: HTTP Client

```python
# client.py
class DebateClient:
    def __init__(self, base_url: str, auth_token: str | None = None):
        self.base_url = base_url
        self.session = requests.Session()
        if auth_token:
            self.session.headers['Authorization'] = f'Bearer {auth_token}'
    
    def get(self, path: str, params: dict = None, timeout: int = 30) -> dict:
        ...
    
    def post(self, path: str, json: dict, timeout: int = 30) -> dict:
        ...
```

#### Step 4: MCPResponse Formatter

Copy pattern từ `aw docs`:
```python
# utils/response.py
def success_response(data: dict, message: str = None) -> dict:
    return {
        "success": True,
        "content": [{"type": "json", "data": data}],
        "metadata": {"message": message} if message else {}
    }

def error_response(code: str, message: str, suggestion: str = None) -> dict:
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "suggestion": suggestion
        }
    }
```

#### Step 5: Command Implementations

##### `aw debate generate-id`

```bash
aw debate generate-id
```

- Generate và return UUID
- Simple, no server call needed

##### `aw debate create`

```bash
aw debate create \
  --debate-id <uuid> \
  --title "Review implementation plan" \
  --debate-type coding_plan_debate \
  --file ./plan.md \
  --client-request-id <uuid>
```

| Option | Required | Description |
|--------|----------|-------------|
| `--debate-id` | ✅ | UUID từ generate-id |
| `--title, -t` | ✅ | Tiêu đề debate |
| `--debate-type` | ✅ | `coding_plan_debate`, `general_debate` |
| `--file, -f` | ✅ | Path đến file MOTION content |
| `--client-request-id` | ✅ | UUID cho idempotency |
| `--format` | ❌ | `json` (default), `markdown` |

**Implementation:**
- [ ] Read file content
- [ ] POST `/debates` với body
- [ ] Return debate_id, argument_id (MOTION)

##### `aw debate get-context`

```bash
aw debate get-context \
  --debate-id <uuid> \
  --argument-limit 10
```

| Option | Required | Description |
|--------|----------|-------------|
| `--debate-id` | ✅ | ID của debate |
| `--argument-limit, -l` | ❌ | Số arguments (default: 10) |
| `--format` | ❌ | `json` (default), `markdown` |

**Implementation:**
- [ ] GET `/debates/{id}/context?limit=N`
- [ ] Return debate + arguments

##### `aw debate submit`

```bash
aw debate submit \
  --debate-id <uuid> \
  --role proposer \
  --target-id <argument_uuid> \
  --content "My response..." \
  --client-request-id <uuid>
```

| Option | Required | Description |
|--------|----------|-------------|
| `--debate-id` | ✅ | ID của debate |
| `--role` | ✅ | `proposer` hoặc `opponent` |
| `--target-id` | ✅ | ID argument đang phản hồi |
| `--content` | One of | Content trực tiếp |
| `--file, -f` | One of | Path đến file content |
| `--client-request-id` | ✅ | UUID cho idempotency |
| `--format` | ❌ | `json` (default), `markdown` |

**Implementation:**
- [ ] Read content từ --content hoặc --file
- [ ] POST `/debates/{id}/arguments`
- [ ] Return new argument_id

##### `aw debate wait`

```bash
aw debate wait \
  --debate-id <uuid> \
  --argument-id <uuid> \
  --role proposer
```

| Option | Required | Description |
|--------|----------|-------------|
| `--debate-id` | ✅ | ID của debate |
| `--argument-id` | ✅ | ID argument đang chờ response |
| `--role` | ✅ | `proposer` hoặc `opponent` |
| `--format` | ❌ | `json` (default), `markdown` |

**Implementation:**
- [ ] Long polling với overall deadline (default 5 min)
- [ ] Retry loop với poll timeout 65s
- [ ] Return response với `action` field
- [ ] Handle timeout gracefully

```python
def wait_for_response(debate_id, argument_id, role, deadline):
    start = time.time()
    while time.time() - start < deadline:
        try:
            response = client.get(
                f'/debates/{debate_id}/wait',
                params={'argument_id': argument_id, 'role': role},
                timeout=POLL_TIMEOUT
            )
            if response.get('has_new_argument'):
                return success_response(response)
        except requests.Timeout:
            continue  # retry
    
    return error_response('TIMEOUT', f'No response after {deadline}s')
```

##### `aw debate appeal`

```bash
aw debate appeal \
  --debate-id <uuid> \
  --target-id <argument_uuid> \
  --content "Appeal content with options..." \
  --client-request-id <uuid>
```

| Option | Required | Description |
|--------|----------|-------------|
| `--debate-id` | ✅ | ID của debate |
| `--target-id` | ✅ | ID argument đang tranh cãi |
| `--content` | One of | Content trực tiếp |
| `--file, -f` | One of | Path đến file content |
| `--client-request-id` | ✅ | UUID cho idempotency |
| `--format` | ❌ | `json` (default), `markdown` |

**Implementation:**
- [ ] POST `/debates/{id}/appeal`
- [ ] Return new argument_id (APPEAL)

##### `aw debate request-completion`

```bash
aw debate request-completion \
  --debate-id <uuid> \
  --target-id <argument_uuid> \
  --content "Summary of agreed points..." \
  --client-request-id <uuid>
```

| Option | Required | Description |
|--------|----------|-------------|
| `--debate-id` | ✅ | ID của debate |
| `--target-id` | ✅ | ID argument cuối |
| `--content` | One of | Content trực tiếp |
| `--file, -f` | One of | Path đến file content |
| `--client-request-id` | ✅ | UUID cho idempotency |
| `--format` | ❌ | `json` (default), `markdown` |

**Implementation:**
- [ ] POST `/debates/{id}/resolution`
- [ ] Return new argument_id (RESOLUTION)

##### `aw debate ruling` (Arbitrator - tạm thời)

```bash
aw debate ruling \
  --debate-id <uuid> \
  --content "My ruling is..." \
  --close  # optional, để close debate
```

| Option | Required | Description |
|--------|----------|-------------|
| `--debate-id` | ✅ | ID của debate |
| `--content` | One of | Content trực tiếp |
| `--file, -f` | One of | Path đến file content |
| `--close` | ❌ | Flag để close debate |
| `--format` | ❌ | `json` (default), `markdown` |

**Implementation:**
- [ ] POST `/debates/{id}/ruling`
- [ ] Return new argument_id (RULING)
- [ ] **Note:** Command này cho Arbitrator (human) test trước khi có Web UI

##### `aw debate intervention` (Arbitrator - tạm thời)

```bash
aw debate intervention --debate-id <uuid>
```

| Option | Required | Description |
|--------|----------|-------------|
| `--debate-id` | ✅ | ID của debate |
| `--format` | ❌ | `json` (default), `markdown` |

**Implementation:**
- [ ] POST `/debates/{id}/intervention`
- [ ] Return new argument_id (INTERVENTION)
- [ ] **Note:** Command này cho Arbitrator (human) test trước khi có Web UI

##### `aw debate list` (Optional utility)

```bash
aw debate list
aw debate list --state AWAITING_PROPOSER
```

| Option | Required | Description |
|--------|----------|-------------|
| `--state` | ❌ | Filter by state |
| `--limit` | ❌ | Limit results |
| `--format` | ❌ | `json` (default), `markdown` |

#### Step 6: Error Handling

```python
# utils/errors.py
ERROR_CODES = {
    'DEBATE_NOT_FOUND': (2, 'Debate not found'),
    'ARGUMENT_NOT_FOUND': (2, 'Argument not found'),
    'ACTION_NOT_ALLOWED': (5, 'Action not allowed in current state'),
    'INVALID_INPUT': (4, 'Invalid input'),
    'SERVER_ERROR': (3, 'Server error'),
    'TIMEOUT': (6, 'Request timeout'),
    'CONNECTION_ERROR': (7, 'Cannot connect to server'),
}
```

#### Step 7: CLI Registration

```python
# cli.py
import click
from .commands import (
    generate_id, create, get_context, submit, wait,
    appeal, request_completion, ruling, intervention, list_debates
)

@click.group()
def debate():
    """Debate CLI - AI Agent debate management"""
    pass

debate.add_command(generate_id.command, 'generate-id')
debate.add_command(create.command, 'create')
debate.add_command(get_context.command, 'get-context')
debate.add_command(submit.command, 'submit')
debate.add_command(wait.command, 'wait')
debate.add_command(appeal.command, 'appeal')
debate.add_command(request_completion.command, 'request-completion')
debate.add_command(ruling.command, 'ruling')
debate.add_command(intervention.command, 'intervention')
debate.add_command(list_debates.command, 'list')
```

#### Step 8: README Documentation

- [ ] Create `README.md` với:
  - Overview
  - All commands với examples
  - Configuration (env vars)
  - Error codes
  - AI Agent workflow examples

#### Step 9: Testing

- [ ] Test generate-id
- [ ] Test create debate (mock server hoặc integration)
- [ ] Test wait với timeout
- [ ] Test error responses
- [ ] **Integration test:** Full debate flow giữa 2 terminals
  - Terminal 1: Proposer
  - Terminal 2: Opponent
  - Terminal 3: Arbitrator (ruling/intervention)

#### Step 10: Integration Test Script

```bash
#!/bin/bash
# test_debate_flow.sh

# Terminal 1 - Proposer creates debate
DEBATE_ID=$(aw debate generate-id | jq -r '.content[0].data.id')
CLIENT_REQ=$(aw debate generate-id | jq -r '.content[0].data.id')

aw debate create \
  --debate-id $DEBATE_ID \
  --title "Test Debate" \
  --debate-type general_debate \
  --file ./motion.md \
  --client-request-id $CLIENT_REQ

echo "Debate created: $DEBATE_ID"
echo "Run in Terminal 2: aw debate get-context --debate-id $DEBATE_ID"
```

## 📊 Summary of Results

> Do not summarize until implementation is done

### ✅ Completed Achievements

- [ ] ...

## 🚧 Outstanding Issues & Follow-up

### ⚠️ Issues/Clarifications

- [ ] `ruling` và `intervention` commands là tạm thời, sẽ deprecate khi có Web UI
- [ ] Consider adding `--verbose` flag cho debug output
- [ ] May need `aw debate status` command để quick check debate state
