# Debate CLI Commands

Quick reference cho tất cả `aw debate` commands.

## Commands Quick Reference

| Command | Description | Role |
|---------|-------------|------|
| [`generate-id`](commands/generate-id.md) | Generate UUID cho debate_id hoặc client_request_id | All |
| [`create`](commands/create.md) | Tạo debate mới với MOTION | Proposer |
| [`get-context`](commands/get-context.md) | Lấy debate info + arguments gần nhất (resume) | All |
| [`submit`](commands/submit.md) | Submit CLAIM argument | Proposer, Opponent |
| [`wait`](commands/wait.md) | Long polling chờ argument mới | Proposer, Opponent |
| [`appeal`](commands/appeal.md) | Submit APPEAL yêu cầu Arbitrator phán xử | Proposer |
| [`request-completion`](commands/request-completion.md) | Request kết thúc debate (RESOLUTION) | Proposer |
| [`ruling`](commands/ruling.md) | Submit RULING ⚠️ DEV-ONLY | Arbitrator |
| [`intervention`](commands/intervention.md) | Submit INTERVENTION (pause) ⚠️ DEV-ONLY | Arbitrator |
| [`list`](commands/list.md) | Liệt kê debates | All |

## Commands by Role

### Proposer Commands

| Command | When to Use |
|---------|-------------|
| `generate-id` | Trước khi tạo debate |
| `create` | Bắt đầu debate với MOTION |
| `submit` | Phản hồi CLAIM của Opponent |
| `wait` | Chờ response từ Opponent/Arbitrator |
| `appeal` | Yêu cầu Arbitrator khi không đồng ý với Opponent |
| `request-completion` | Yêu cầu kết thúc debate |
| `get-context` | Resume debate đang dở |

### Opponent Commands

| Command | When to Use |
|---------|-------------|
| `get-context` | Lấy context khi được invite vào debate |
| `submit` | Phản hồi MOTION hoặc CLAIM của Proposer |
| `wait` | Chờ response từ Proposer/Arbitrator |

### Arbitrator Commands (DEV-ONLY)

| Command | When to Use |
|---------|-------------|
| `list` | Xem debates đang chờ |
| `get-context` | Lấy context debate cần xử lý |
| `ruling` | Phán xử sau APPEAL hoặc RESOLUTION |
| `intervention` | Pause debate để can thiệp |

## Common Patterns

### Proposer Flow

```bash
# 1. Generate debate ID
DEBATE_ID=$(aw debate generate-id | jq -r '.content[0].data.id')

# 2. Create debate with MOTION (response chỉ chứa IDs, không có content)
MOTION_ID=$(aw debate create --debate-id $DEBATE_ID --title "..." --type coding_plan_debate -f motion.md | jq -r '.content[0].data.argument_id')

# 3. Wait for Opponent
RESULT=$(aw debate wait --debate-id $DEBATE_ID --role proposer --argument-id $MOTION_ID)

# 4. Loop: analyze + submit + wait
```

### Opponent Flow

```bash
# 1. Get context (response chứa full content để rebuild context)
CONTEXT=$(aw debate get-context --debate-id $DEBATE_ID)

# 2. Submit response (response chỉ chứa IDs, không có content)
ARG_ID=$(aw debate submit --debate-id $DEBATE_ID --role opponent --target-id $MOTION_ID -f response.md | jq -r '.content[0].data.argument_id')

# 3. Wait for Proposer
RESULT=$(aw debate wait --debate-id $DEBATE_ID --role opponent --argument-id $ARG_ID)
```

## Response Format Notes

### Write Commands (create, submit, appeal, request-completion, ruling, intervention)

**Token Optimization:** Response chỉ chứa metadata, KHÔNG chứa content.

```json
{
  "content[0].data": {
    "argument_id": "<uuid>",
    "argument_type": "CLAIM",
    "argument_seq": 3,
    "debate_id": "<uuid>",
    "debate_state": "AWAITING_OPPONENT",
    "client_request_id": "<uuid>"
  }
}
```

**Lý do:** Agent vừa submit content → đã biết content → trả lại = tốn token vô ích.

### Read Commands (get-context, wait)

Response chứa **full content** vì agent cần đọc để xử lý:
- `get-context`: Rebuild context khi resume
- `wait`: Đọc response từ đối phương

**Readable Content:** Content fields được output với **actual newlines** thay vì escaped `\n`.
Điều này giúp AI agents đọc markdown content trực tiếp:

```json
// Thay vì: "content": "## Title\\n\\nParagraph"
// Output là:
"content": "## Title

Paragraph"
```

## Content Input Methods

Các commands có content (`create`, `submit`, `appeal`, `request-completion`, `ruling`) hỗ trợ 3 cách input:

| Option | Description |
|--------|-------------|
| `--file PATH` / `-f PATH` | Đọc content từ file |
| `--content TEXT` | Inline content |
| `--stdin` | Đọc từ stdin (pipe) |

> **Lưu ý:** Chỉ được dùng MỘT trong 3 options.
