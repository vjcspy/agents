# `generate-id`

Generate UUID để dùng cho `debate_id` hoặc `client_request_id`.

## Usage

```bash
aw debate generate-id [--format json|markdown]
```

## Options

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--format` | ❌ | `json` | Output format |

## Response

```json
{
  "success": true,
  "content": [{
    "type": "json",
    "data": {
      "id": "93d81b1a-0e66-4510-abfd-aa33b26cb82e"
    }
  }],
  "metadata": { "message": "Use this ID for debate_id or client_request_id" }
}
```

## Extract ID

```bash
aw debate generate-id | jq -r '.content[0].data.id'
```
