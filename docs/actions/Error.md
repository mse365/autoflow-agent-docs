# Error

[← All actions](README.md)

Stops the flow with an error message.

| | |
|---|---|
| Enum name | `Error` |
| Ordinal | `"action": 102` |
| Category | Utilities |
| Terminating | `true` |
| Group / edges | No |
| Availability | GA |

## What it does

When the flow reaches this step, it resolves the configured message and raises it as an error. The step fails, and the run ends with status Error. In flows that run as one transaction, or inline in the user's session, this also rolls back the work done so far. Because the step always fails, it is a terminating step and must be the last step of its path.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `Error` | string | yes | – | The error message. Note the capital `E`, because keys are case-sensitive. Supports SmartFields `{{..}}`, SmartFormulas `[[..]]` and SmartControls `{#..#}`. |

**Translatable** ([translations](../flow-definition.md#translations)): `Error`.

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `Errormessage` | value | – | Declared but never filled, because the step always raises an error. Nothing downstream can use it. |

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| publish | warning | A terminating step has a next step in the same sequence, or has edges | `Step "%1" is a terminating step but has a successor – terminating steps must end the path.` |

The editor performs no other check. In particular, an empty message is accepted.

## Runtime errors

| condition | message |
|---|---|
| Always, when the key `Error` is present | the resolved message text |
| The key `Error` is missing | `No error message configured.` |

## Example

```json
{
  "id": "9A1B2C3D-4E5F-4A6B-8C7D-0E1F2A3B4C01",
  "type": "action",
  "action": 102,
  "description": "Error",
  "slug": "Error",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/alert-triangle.svg",
  "terminating": true,
  "configuration": {
    "Error": "Customer {{trigger_Rec.no}} has no e-mail address."
  },
  "outputs": [ { "name": "Errormessage", "type": "value" } ]
}
```

## Gotchas

- Place it at the end of a branch (typically the `false` branch of a Decision). A step after it would never run, and publishing warns about it.
- The publish check uses the `terminating` flag in the step JSON. Always write `"terminating": true` for this step.
- Use a non-empty message. An empty message still fails the step, but leaves nothing useful in the execution log.
