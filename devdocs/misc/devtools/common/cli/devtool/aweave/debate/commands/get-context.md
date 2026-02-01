# `get-context`

Lấy thông tin debate + motion + arguments gần nhất. **Dùng khi resume debate.**

## Usage

```bash
aw debate get-context \
  --debate-id <uuid> \
  [--limit <N>] \
  [--format json|markdown]
```

## Options

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--debate-id` | ✅ | - | Debate UUID |
| `--limit` / `-l` | ❌ | 10 | Số arguments gần nhất |
| `--format` | ❌ | `json` | Output format |

## Response

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

## Notes

- `motion` luôn được include (là argument đầu tiên)
- `arguments` chứa N arguments gần nhất (không bao gồm motion), theo thứ tự `seq` tăng dần
- Dùng `debate.state` để xác định lượt của ai
- Dùng `arguments[-1]` để lấy argument cuối cùng

## Readable Content

> **AI Agent Optimization:** Content fields được output với **actual newlines** (không escape thành `\n`).
> Điều này giúp AI agents đọc markdown content trực tiếp mà không cần parse escaped strings.
>
> Ví dụ thay vì: `"content": "## Title\\n\\nParagraph 1"`
> Output sẽ là:
> ```json
> "content": "## Title
>
> Paragraph 1"
> ```
