# `intervention` ⚠️ DEV-ONLY

Submit INTERVENTION (pause debate). **Chỉ Arbitrator. DEV-ONLY.**

## Usage

```bash
aw debate intervention \
  --debate-id <uuid> \
  [--client-request-id <uuid>] \
  [--format json|markdown]
```

## Options

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--debate-id` | ✅ | - | Debate UUID |
| `--client-request-id` | ❌ | auto | Idempotency key |
| `--format` | ❌ | `json` | Output format |

## Prerequisites

- State phải là `AWAITING_OPPONENT` hoặc `AWAITING_PROPOSER`

## Response

> **Token Optimization:** Response chỉ chứa metadata cần thiết.

```json
{
  "success": true,
  "content": [{
    "type": "json",
    "data": {
      "argument_id": "<intervention_uuid>",
      "argument_type": "INTERVENTION",
      "argument_seq": 3,
      "debate_id": "<debate_uuid>",
      "debate_state": "INTERVENTION_PENDING",
      "client_request_id": "<uuid>"
    }
  }],
  "metadata": { "message": "Intervention submitted" }
}
```

## Next Steps

Sau intervention: Phải submit `ruling` để tiếp tục hoặc close debate
