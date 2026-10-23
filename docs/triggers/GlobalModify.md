# When a record is modified

[← All triggers](README.md)

Starts a background run whenever a record of the configured table is modified, optionally only when certain fields changed.

| | |
|---|---|
| Enum name | `GlobalModify` |
| Ordinal | `"trigger": 5564450` |
| Category | Records |
| Terminating | n/a (trigger) |
| Group / edges | no |
| Availability | GA |

## What it does

Hooks Business Central's global modify event for `tableNo`. When the after-image matches `filters` and, if `watchFields` are configured, at least one watched field changed, a pending execution is created inside the modifying transaction. A recurring Job Queue entry (every 5 minutes, created at publish) queues one background run per pending execution, and each run commits after every step.

Changes are detected against AutoFlow's own snapshot of the watched fields, not against the record's previous version. Publishing fills the snapshot for every existing record, and it is updated on every insert and modify. Values are compared by hash of their locale-invariant text.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `tableNo` | integer | yes | `0` | Table to watch. |
| `filters` | array | no | `[]` | `[{ "fieldNo": int, "filter": "text" }]`. These are standard filter expressions on the modified record, applied literally with no placeholder resolution, max. 250 characters. |
| `watchFields` | array | no | `[]` | `[{ "fieldNo": int }]`. Fire only when one of these fields changed. Leave it empty to fire on every matching modify. |

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `Rec` | reference | `tableNo` | The modified record. It is declared as `value` while `tableNo` is 0. |
| `ChangedFields` | value | – | JSON array text: `[{"fieldNo":5,"fieldName":"Name","oldValue":"Old","newValue":"New"}]`. It holds only the watched fields that changed, and is `"[]"` without watch fields. Values are locale-invariant text, max. 2048 characters. |

Reference them as `{{trigger_Rec}}` and `{{trigger_ChangedFields}}`. To work with `ChangedFields`, parse it with a JSON or Parser step.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `tableNo` set and > 0 (the config canvas marks Table as required) | Please fill in the highlighted fields. |
| runtime | info | an invalid filter means the record does not match (no error) | (no message) |

There is **no publish-time trigger check**. A flow whose `tableNo` is 0 or does not exist publishes and never fires.

## Runtime errors

None raised to the modifying user. Flow errors appear on the execution and in the Job Queue log.

## Example

```json
{
  "id": "3D4E5F6A-7B8C-4D9E-8F0A-1B2C3D4E5F6A",
  "type": "trigger",
  "trigger": 5564450,
  "description": "When a Customer is modified",
  "slug": "trigger",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/bolt.svg",
  "configuration": {
    "tableNo": 18,
    "filters": [
      { "fieldNo": 39, "filter": "' '" }
    ],
    "watchFields": [
      { "fieldNo": 20 },
      { "fieldNo": 39 }
    ]
  },
  "outputs": [
    { "name": "Rec", "type": "reference", "tableNo": 18 },
    { "name": "ChangedFields", "type": "value" }
  ],
  "level": 0
}
```

## Gotchas

- If a record has no snapshot yet, every watched field counts as changed (even an empty one) and `oldValue` is `""`. The snapshot fills in after the first modify.
- Every `watchFields[].fieldNo` must exist in the table. An unknown field number makes publishing fail (when the table has records) and, while the flow is published, makes every insert and modify of that table fail.
- The snapshot belongs to the table, not the flow. Several flows on the same table share it.
- A flow that writes to its own table again (for example Modify Record) re-triggers itself, whether or not the write runs table triggers. Use `watchFields` or `filters` to stop the loop.
- A **Confirm dialog** step gets a publish warning, because it runs inside the record change that started the flow.
- Trigger-response steps (Respond to Webhook, Return SubFlow Output, Return PDF, Set report file name, Set document field values, Prevent page close) are hidden here.
