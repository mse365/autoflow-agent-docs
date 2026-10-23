# When invoked as a SubFlow

[← All triggers](README.md)

Makes the flow a reusable building block. Another flow calls it with a **Run SubFlow** step, passes typed inputs, and gets values back through **Return SubFlow Output**.

| | |
|---|---|
| Enum name | `SubFlow` |
| Ordinal | `"trigger": 5564404` |
| Category | Base |
| Terminating | n/a (trigger) |
| Group / edges | no |
| Availability | GA. Publishing requires a **Code** on the flow card. Does not count against the licensed-flow limit. |

## What it does

A SubFlow never starts on its own. The calling flow's Run SubFlow step runs it **synchronously, inline**: in the caller's session and as part of the caller's run, with its steps logged under the calling step. The declared inputs become trigger outputs that the body reads like any other trigger output. Publishing marks the flow as a SubFlow, writes no trigger registration and creates no Job Queue entry. Callers find it by its Code.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `inputs` | array | no | `[]` | `[{ "name": "CustomerNo", "type": "Value", "required": true }, { "name": "Order", "type": "Reference", "tableNo": 36, "required": false }]`. `name` may only contain letters, digits and `_`, and must be unique. `type` is `"Value"` (default) or `"Reference"`. `tableNo` applies to Reference parameters only (`0` = any table). |
| `subFlowCode` | string | no | – | Written automatically when the SubFlow is saved as a template. On import it restores the flow's Code. Do not set it by hand for normal use. |
| `iconUrl` | string | no | – | Written automatically on template save. On import it restores the flow's icon (https only). |

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| *inputs[].name* | `value` or `reference` | `inputs[].tableNo` for Reference | One per input parameter, name truncated to 30 characters. |

Inside the SubFlow, reference them as `{{trigger_<name>}}`, for example `{{trigger_CustomerNo}}`.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `inputs[].name` non-empty, `[A-Za-z0-9_]+`, unique | (no message) |
| publish | error | the flow header needs a Code | A Code must be set on the Flow Card before this SubFlow can be published. Run-SubFlow steps and templates reference SubFlows by Code, not by No. |

## Runtime errors

| condition | message |
|---|---|
| a Job Queue entry tries to run the SubFlow on its own | Execution %1 belongs to a SubFlow. SubFlows run only as part of the flow that calls them and cannot be started directly. |
| a yielding step (Respond to Webhook, Return PDF, Set report file name) runs in the SubFlow | Step %1 (%2) requested an HTTP yield, but it is running inside a SubFlow. Yield is only valid in the synchronous phase of a Webhook flow. |

## Example

```json
{
  "id": "6A7B8C9D-0E1F-4A2B-9C3D-4E5F6A7B8C9D",
  "type": "trigger",
  "trigger": 5564404,
  "description": "When invoked as a SubFlow",
  "slug": "trigger",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/subtask-trigger.svg",
  "configuration": {
    "inputs": [
      { "name": "CustomerNo", "type": "Value", "required": true },
      { "name": "Order", "type": "Reference", "tableNo": 36, "required": false }
    ]
  },
  "outputs": [
    { "name": "CustomerNo", "type": "value" },
    { "name": "Order", "type": "reference", "tableNo": 36 }
  ],
  "level": 0
}
```

## Gotchas

- Set a **Code** before publishing. Callers bind to the Code, not the flow number.
- **Return SubFlow Output** is only offered in SubFlow flows. Respond to Webhook, Return PDF, Set report file name, Set document field values and Prevent page close are not.
- `required` is metadata for the caller's input binding. The SubFlow itself does not reject missing values.
- Because it runs inside the caller's run, how a SubFlow's writes are committed follows the caller's trigger.
