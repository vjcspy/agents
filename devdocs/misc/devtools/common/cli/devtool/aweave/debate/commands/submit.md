# `submit`

Submit CLAIM argument. **Proposer và Opponent sử dụng.**

## Usage

```bash
aw debate submit \
  --debate-id <uuid> \
  --role <proposer|opponent> \
  --target-id <argument_uuid> \
  (--file <path> | --content <text> | --stdin) \
  [--client-request-id <uuid>] \
  [--format json|markdown]
```

## Options

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

> ⚡ Một trong `--file`, `--content`, `--stdin` là **required**

## Prerequisites

- State phải là `AWAITING_OPPONENT` nếu role = `opponent`
- State phải là `AWAITING_PROPOSER` nếu role = `proposer`

## Response

> **Token Optimization:** Response chỉ chứa metadata cần thiết. Content không được trả về vì agent vừa submit, đã biết nội dung.

```json
{
  "success": true,
  "content": [{
    "type": "json",
    "data": {
      "argument_id": "<new_argument_uuid>",
      "argument_type": "CLAIM",
      "argument_seq": 3,
      "debate_id": "<debate_uuid>",
      "debate_state": "AWAITING_OPPONENT",
      "client_request_id": "<uuid>"
    }
  }],
  "metadata": { "message": "Argument submitted" }
}
```

## Notes

- `data.argument_id` cần cho `wait` command tiếp theo
- `debate_state` cho biết state mới sau khi submit
- **Content không được trả về** để tối ưu token cho AI agents
