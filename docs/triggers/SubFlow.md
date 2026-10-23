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
| Availability | GA. Publishing requires a **Code** on the flow card, as for every flow. Does not count against the free-tier flow limit. |

## What it does

A SubFlow never starts on its own. The calling flow's Run SubFlow step runs it **synchronously, inline**: in the caller's session and as part of the calling step. It gets its own child execution with its own step log, linked from the caller's log entry "SubFlow '%1' was executed.". It does not commit step by step; its work is committed or rolled back together with the calling step. The declared inputs become trigger outputs that the body reads like any other trigger output. Publishing marks the flow as a SubFlow, writes no trigger registration and creates no Job Queue entry. Callers find it by its Code.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `inputs` | array | no | `[]` | `[{ "name": "CustomerNo", "type": "Value", "required": true }, { "name": "Order", "type": "Reference", "tableNo": 36, "required": false }]`. Use only letters, digits and `_` in `name`, and keep names unique (nothing checks this). `type` is `"Value"` (default) or `"Reference"`; only the exact string `"Reference"` makes a reference parameter. `tableNo` applies to Reference parameters only (`0` = any table). |
| `subFlowCode` | string | no | – | Written automatically when the SubFlow is saved as a template. On import it is applied to the flow's Code (after the root `code`), unless another flow already uses it. Prefer the root `code`; if you write `subFlowCode`, make it the same value. |
| `iconUrl` | string | no | – | Written automatically on template save. On import it restores the flow's icon (https only). |

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| *inputs[].name* | `value` or `reference` | `inputs[].tableNo` for Reference | One per input parameter, name truncated to 30 characters. |

Inside the SubFlow, reference them as `{{trigger_<name>}}`, for example `{{trigger_CustomerNo}}`.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| publish | error | the flow needs a Code (root `code` on import); checked for every flow, before the other publish checks | Flow %1 (%2) has no Code. Enter a Code on the flow card before activating it – for example YOURCOMPANY.FLOW-NAME. The Code identifies the flow across companies and environments. |

Before 27.0.40 the missing Code was reported as "A Code must be set on the Flow Card before this SubFlow can be published. Run-SubFlow steps and templates reference SubFlows by Code, not by No."

The input names are not checked anywhere. Keep them to letters, digits and `_`, and unique.

## Runtime errors

| condition | message |
|---|---|
| a Job Queue entry tries to run the SubFlow on its own | Execution %1 belongs to a SubFlow. SubFlows run only as part of the flow that calls them and cannot be started directly. |
| a step that answers a caller (Respond to Webhook, Return PDF, Set report file name, Set document field values, Prevent page close) runs in the SubFlow | Step %1 (%2) requested an HTTP yield, but it is running inside a SubFlow. Yield is only valid in the synchronous phase of a Webhook flow. |
| a Sleep step runs in the SubFlow | Step %1 (%2) requested a deferred resume, but the flow is running synchronously. Use Sleep or other time-based deferral steps only outside of synchronous frames (Webhook sync phase or SubFlow body). |

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
- Because it runs inside the calling step, a SubFlow's writes are committed together with that step, the way the caller's trigger commits.
