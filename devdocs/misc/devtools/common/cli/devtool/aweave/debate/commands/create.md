# `create`

Tạo debate mới với MOTION. **Chỉ Proposer sử dụng.**

## Usage

```bash
aw debate create \
  --debate-id <uuid> \
  --title <string> \
  --type <debate_type> \
  (--file <path> | --content <text> | --stdin) \
  [--client-request-id <uuid>] \
  [--format json|markdown]
```

## Options

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

## Response

> **Token Optimization:** Response chỉ chứa metadata cần thiết. Content không được trả về vì agent vừa submit, đã biết nội dung.

```json
{
  "success": true,
  "content": [{
    "type": "json",
    "data": {
      "argument_id": "<motion_uuid>",
      "argument_type": "MOTION",
      "argument_seq": 1,
      "debate_id": "<debate_uuid>",
      "debate_state": "AWAITING_OPPONENT",
      "debate_type": "coding_plan_debate",
      "client_request_id": "<uuid>"
    }
  }],
  "metadata": { "message": "Debate created successfully" }
}
```

## Notes

- `data.argument_id` là MOTION ID, cần cho `wait` command tiếp theo
- State ban đầu luôn là `AWAITING_OPPONENT`
- **Content không được trả về** để tối ưu token cho AI agents
