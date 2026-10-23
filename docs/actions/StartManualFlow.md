# Start flow

[← All actions](README.md)

Starts another manual flow in the background and continues without waiting for it.

| | |
|---|---|
| Enum name | `StartManualFlow` |
| Ordinal | `"action": 5564424` |
| Category | SubFlows |
| Terminating | `false` |
| Group / edges | No |
| Availability | GA. Hidden from the generic step picker: every published manual flow that has a Code (except the flow being edited and SubFlows) appears as its own tile, which creates this step. |

## What it does

The step finds the target flow by its **Code**. It checks that the target is a published flow started by **When manually started**, and that the record matches the target's table, if the target runs on one. It then creates a new execution of the target plus a Job Queue entry, and continues immediately.

The started flow runs on its own: this flow does not wait for it and gets no results back, only the new execution's number.

The new execution and its job are written in the caller's transaction:

- In normal background flows, the engine commits after each step, so the start is committed right after this step.
- In interactive trigger flows, SubFlow bodies and "Run atomically" flows, the start is only committed when the caller's run commits, and it is rolled back with it.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `flowCode` | string (≤ 60) | yes | `""` | Code of the target flow (`[NAMESPACE.]CODE`). It is resolved by Code at run time; the flow No. is never stored. No SmartFields. |
| `record` | string | when the target runs on a table | `""` | A wrapped Reference SmartField pointing at a record of the target's table, e.g. `{{trigger_Rec}}`. Leave it empty for standalone targets. |
| `customIconUrl` | string | no | `""` | Display only. The target's icon, mirrored to the step's top-level `customIconUrl`. |

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `ExecutionNo` | value | – | Entry number of the started execution. |

Reference it downstream as `{{<slug>_ExecutionNo}}`.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `flowCode` empty | Choose the flow to start. |
| editor | error | The target runs on a table and `record` is empty | The flow %1 runs on a record. Select the record to start it for. |
| editor (status line) | error | The target is missing or is not a published manual flow | The flow %1 is not an active manual flow on this system. Publish it, then reopen this step. |
| editor (status line) | error | `record` points at another table | The flow runs on records of table %1, but the selected reference points at table %2. |

No publish-time check exists for this step.

## Runtime errors

| condition | message |
|---|---|
| Unknown Code | There is no flow with the code %1 to start. |
| The record cannot be resolved | The record "%1" to start the flow for cannot be resolved. |
| The target is not published | The flow %1 is not active. Publish it before starting it. |
| The target is not a manual flow | The flow %1 cannot be started this way, because it is not started by the trigger "When manually started". |
| The target needs a record | The flow %1 runs on a record of the table %2. Pass a record to start it. |
| The record is from the wrong table | The flow %1 runs on records of the table %2, not of the table %3. |

## Example

```json
{
  "id": "E4DA3B7F-BBCE-4345-9D77-7A1E2C8F6B13",
  "type": "action",
  "action": 5564424,
  "description": "Send order confirmation",
  "slug": "SendConfirmation",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/player-play.svg",
  "customIconUrl": "",
  "terminating": false,
  "configuration": {
    "flowCode": "ACME.SEND_ORDER_CONF",
    "record": "{{trigger_Rec}}",
    "customIconUrl": ""
  },
  "outputs": [
    { "name": "ExecutionNo", "type": "value" }
  ]
}
```

## Gotchas

- Cross-environment: nothing is re-mapped on import. A flow with the same Code must be published as a manual flow in the target company before this step runs.
- The target must not be a SubFlow. To call a SubFlow and get results back, use [Run SubFlow](RunSubFlow.md).
- Whether the job starts on its own depends on the AutoFlow Setup option for manually started flows.
