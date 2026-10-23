# Log

[← All actions](README.md)

Writes an Info message to the execution log without stopping the flow.

| | |
|---|---|
| Enum name | `Log` |
| Ordinal | `"action": 104` |
| Category | Utilities |
| Terminating | `false` |
| Group / edges | No |
| Availability | GA |

## What it does

The step resolves `Message` (SmartFields, SmartFormulas and SmartControls) and writes the result as an Info entry to the run's execution log. It shows nothing to the user and produces no outputs. The flow continues with the next step. Use it to record intermediate values when debugging or auditing a flow.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `Message` | string | no | `""` | Text to log. Note the capital `M`, because keys are case-sensitive. Supports `{{..}}`, `[[..]]` and `{#..#}`. If the key is missing, an empty entry is written. |

## Outputs

None.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| – | – | No checks exist for this step. | – |

## Runtime errors

None from the step itself.

## Example

```json
{
  "id": "7B8C9D0E-1F2A-4B3C-8D4E-5F6A7B8C9D01",
  "type": "action",
  "action": 104,
  "description": "Log",
  "slug": "Log",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/log.svg",
  "terminating": false,
  "configuration": {
    "Message": "Processed {{LoopOverSalesLines_iteration}} of {{LoopOverSalesLines_total}} lines."
  },
  "outputs": []
}
```

## Gotchas

- Use `Message` with a capital M. A lowercase `message` key is ignored, and the log entry is empty.
