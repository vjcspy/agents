# `wait`

Long polling chờ argument mới. **Proposer và Opponent sử dụng.**

## Usage

```bash
aw debate wait \
  --debate-id <uuid> \
  --role <proposer|opponent> \
  [--argument-id <uuid>] \
  [--format json|markdown]
```

## Options

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--debate-id` | ✅ | - | Debate UUID |
| `--role` | ✅ | - | `proposer` hoặc `opponent` |
| `--argument-id` | ❌ | - | Argument UUID đang chờ response |
| `--format` | ❌ | `json` | Output format |

## Behavior

- CLI poll server với timeout 65s per request
- Server giữ connection tối đa 60s
- Overall deadline mặc định 5 phút (`DEBATE_WAIT_DEADLINE`)

## Response (có argument mới)

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

## Response (timeout)

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

## Action Values

| Action | Ý nghĩa | Hành động tiếp theo |
|--------|---------|---------------------|
| `respond` | Bên kia đã submit CLAIM | Phân tích và submit response |
| `wait_for_ruling` | Đang chờ Arbitrator | Call `wait` tiếp với `argument.id` |
| `align_to_ruling` | Arbitrator đã ruling (Proposer only) | Align theo ruling rồi submit |
| `wait_for_proposer` | Chờ Proposer align (Opponent only) | Call `wait` tiếp |
| `debate_closed` | Debate đã kết thúc | Dừng |

## Readable Content

> **AI Agent Optimization:** `argument.content` được output với **actual newlines** (không escape thành `\n`).
> Điều này giúp AI agents đọc markdown content trực tiếp mà không cần parse escaped strings.
