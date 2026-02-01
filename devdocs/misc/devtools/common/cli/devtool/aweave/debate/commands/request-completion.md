# `request-completion`

Request kết thúc debate (submit RESOLUTION). **Chỉ Proposer sử dụng.**

## Usage

```bash
aw debate request-completion \
  --debate-id <uuid> \
  --target-id <argument_uuid> \
  (--file <path> | --content <text> | --stdin) \
  [--client-request-id <uuid>] \
  [--format json|markdown]
```

## Options

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--debate-id` | ✅ | - | Debate UUID |
| `--target-id` | ✅ | - | UUID argument cuối cùng |
| `--file` / `-f` | ⚡ | - | Path đến file content |
| `--content` | ⚡ | - | Inline content |
| `--stdin` | ⚡ | - | Đọc từ stdin |
| `--client-request-id` | ❌ | auto | Idempotency key |
| `--format` | ❌ | `json` | Output format |

> ⚡ Một trong `--file`, `--content`, `--stdin` là **required**

## Prerequisites

- State phải là `AWAITING_PROPOSER`

## Response

> **Token Optimization:** Response chỉ chứa metadata cần thiết. Content không được trả về vì agent vừa submit, đã biết nội dung.

```json
{
  "success": true,
  "content": [{
    "type": "json",
    "data": {
      "argument_id": "<resolution_uuid>",
      "argument_type": "RESOLUTION",
      "argument_seq": 5,
      "debate_id": "<debate_uuid>",
      "debate_state": "AWAITING_ARBITRATOR",
      "client_request_id": "<uuid>"
    }
  }],
  "metadata": { "message": "Resolution submitted" }
}
```

## Next Steps

Sau khi request: Call `wait` với `data.argument_id` để chờ Arbitrator close hoặc reject
