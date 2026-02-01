# `list`

Liệt kê debates.

## Usage

```bash
aw debate list \
  [--state <state>] \
  [--limit <N>] \
  [--offset <N>] \
  [--format json|markdown]
```

## Options

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--state` | ❌ | - | Filter theo state |
| `--limit` / `-l` | ❌ | - | Max kết quả |
| `--offset` | ❌ | 0 | Pagination offset |
| `--format` | ❌ | `json` | Output format |

## Response

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
