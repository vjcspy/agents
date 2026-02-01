# `ruling` ⚠️ DEV-ONLY

Submit RULING. **Chỉ Arbitrator sử dụng. DEV-ONLY - dùng để test trước khi có Web UI.**

## Usage

```bash
aw debate ruling \
  --debate-id <uuid> \
  (--file <path> | --content <text> | --stdin) \
  [--close] \
  [--client-request-id <uuid>] \
  [--format json|markdown]
```

## Options

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--debate-id` | ✅ | - | Debate UUID |
| `--file` / `-f` | ⚡ | - | Path đến file content |
| `--content` | ⚡ | - | Inline content |
| `--stdin` | ⚡ | - | Đọc từ stdin |
| `--close` | ❌ | `false` | Close debate sau ruling |
| `--client-request-id` | ❌ | auto | Idempotency key |
| `--format` | ❌ | `json` | Output format |

> ⚡ Một trong `--file`, `--content`, `--stdin` là **required**

## Prerequisites

- State phải là `AWAITING_ARBITRATOR` hoặc `INTERVENTION_PENDING`

## Response

> **Token Optimization:** Response chỉ chứa metadata cần thiết. Content không được trả về vì agent vừa submit, đã biết nội dung.

```json
{
  "success": true,
  "content": [{
    "type": "json",
    "data": {
      "argument_id": "<ruling_uuid>",
      "argument_type": "RULING",
      "argument_seq": 6,
      "debate_id": "<debate_uuid>",
      "debate_state": "AWAITING_PROPOSER",
      "client_request_id": "<uuid>"
    }
  }],
  "metadata": { "message": "Ruling submitted", "closed": false }
}
```

## Notes

- Nếu `--close`: `debate_state` = `CLOSED`
- Không có `--close`: `debate_state` = `AWAITING_PROPOSER` (Proposer phải align)
- **Content không được trả về** để tối ưu token
