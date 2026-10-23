# When a record is created or modified (interactive)

[← All triggers](README.md)

Runs synchronously in the user's session while a record of a supported table is being saved. The flow can block the save or adjust field values.

| | |
|---|---|
| Enum name | `OnDocumentModify` (enum caption "When a document is modified (interactive)") |
| Ordinal | `"trigger": 5564529` |
| Category | Interactive |
| Terminating | n/a (trigger) |
| Group / edges | no |
| Availability | GA. Only for supported tables. The subscription-contract tables need Microsoft's Subscription Billing app (BC26+). |

## What it does

Hooks the before-insert and before-modify events of the configured table. When the record matches `filters` and, on a modify, a watched field changed, the flow runs **inline in the user's transaction, without any commit**:

- An error in the flow, such as an **Error** step, stops the save. The user sees the flow's message, and the record, the flow's own work and the execution entry all roll back.
- A **Set document field values** step writes values onto the record before it is stored.

Only writes that run table triggers fire the flow. With `guiOnly` (the default), sessions without a UI are ignored. A write that the running flow causes itself does not re-enter the trigger.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `tableNo` | integer | yes | `0` | One of: Customer `18`, Vendor `23`, Item `27`, Sales Header `36`, Sales Line `37`, Purchase Header `38`, Purchase Line `39`, Project `167`, Project Task `1001`, Project Budget Line `1003`, Contact `5050`, Customer Subscription Contract `8052`*, Customer Subscription Contract Line `8062`*. Tables marked * need the Subscription Billing app. Extensions can register more. |
| `guiOnly` | boolean | no | `true` | Run only in interactive sessions. |
| `triggerOnInsert` | boolean | no | `false` | Run while a record is created. |
| `triggerOnModify` | boolean | no | `true` | Run while a record is changed. |
| `timeoutSec` | integer | no | `30` | Maximum run time. Keep it short, because the user waits. |
| `filters` | array | no | `[]` | `[{ "fieldNo": int, "filter": "text" }]`. These are filters on the record being saved, applied literally, max. 250 characters. |
| `watchFields` | array | no | `[]` | `[{ "fieldNo": int, "name": "Identifier" }]`. On a modify, fire only if one of these fields changed. Each entry produces `xRec_<name>` and `Rec_<name>` outputs. |

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `Rec` | reference | `tableNo` | The record being saved. |
| `xRec_<name>` | value | – | Per watch field: the value before the change. Empty on insert. |
| `Rec_<name>` | value | – | Per watch field: the value after the change. |

Values are locale-invariant text, for example `1234.5` or `2026-10-23`. Reference them as `{{trigger_Rec}}`, `{{trigger_xRec_Status}}` and `{{trigger_Rec_Status}}`.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| publish | error (hard stop) | `tableNo` set | Pick the table the flow should watch. |
| publish | error (hard stop) | `tableNo` supported | Table %1 is not one of the supported tables. |
| publish | error (hard stop) | insert or modify enabled | Choose when the flow runs: on insert, on modify, or both. |
| publish | warning | **Confirm dialog** step in the flow | The confirm dialog '%1' runs inside the record change that started the flow. Business Central does not open dialogs there, so when a user triggers the flow it fails at this step. It only works when the flow runs in the background, where the answer under 'Without a user interface' applies. |
| editor | error | live status for an unsupported table | Table %1 is not supported by this trigger, so the flow would never run. |
| editor | warning | watch-field `name` is a valid unique identifier (`^[A-Za-z_][A-Za-z0-9_]{0,29}$`) | (no message) |

Trigger errors are reported as `This flow's trigger cannot be published:` followed by the list.

## Runtime errors

| condition | effect |
|---|---|
| any error in the flow | The flow's message is shown to the user and the save is rolled back. |

## Example

```json
{
  "id": "9D0E1F2A-3B4C-4D5E-8F6A-7B8C9D0E1F2A",
  "type": "trigger",
  "trigger": 5564529,
  "description": "When a Sales Header is created or modified (interactive)",
  "slug": "trigger",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/pointer-bold.svg",
  "configuration": {
    "tableNo": 36,
    "guiOnly": true,
    "triggerOnInsert": false,
    "triggerOnModify": true,
    "timeoutSec": 30,
    "filters": [
      { "fieldNo": 1, "filter": "Order" }
    ],
    "watchFields": [
      { "fieldNo": 2, "name": "SellToCustomerNo" }
    ]
  },
  "outputs": [
    { "name": "Rec", "type": "reference", "tableNo": 36 },
    { "name": "xRec_SellToCustomerNo", "type": "value" },
    { "name": "Rec_SellToCustomerNo", "type": "value" }
  ],
  "level": 0
}
```

## Gotchas

- Everything is one transaction. Do not use steps that need a commit or must wait, such as Sleep or HTTP calls with side effects you cannot roll back.
- A **Confirm dialog** fails here when a user triggers the flow. Use a release or post trigger to ask the user.
- **Set document field values** is offered for this trigger and the other interactive document triggers. Respond to Webhook, Return SubFlow Output, Return PDF, Set report file name and Prevent page close are hidden.
- `watchFields` limit modifies only. Inserts fire on every record that matches `filters`.
- `guiOnly: true` (the default) keeps validation errors from breaking posting routines and background jobs.
