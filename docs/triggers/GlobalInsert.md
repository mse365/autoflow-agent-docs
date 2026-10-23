# When a record is inserted

[← All triggers](README.md)

Starts a background run whenever a record is inserted into the configured table and matches the field filters.

| | |
|---|---|
| Enum name | `GlobalInsert` |
| Ordinal | `"trigger": 5564402` |
| Category | Records |
| Terminating | n/a (trigger) |
| Group / edges | no |
| Availability | GA |

## What it does

Hooks Business Central's global insert event for `tableNo`. Each matching insert creates a pending execution inside the inserting transaction. If that transaction rolls back, the execution goes with it. A recurring Job Queue entry created at publish runs every 5 minutes, picks up pending executions and queues one Job Queue run per execution. The flow therefore runs **asynchronously**, with up to about five minutes of delay, and commits after every step. A bad filter never blocks the user's insert. The record simply counts as not matching.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `tableNo` | integer | yes | `0` | Table to watch. `0` never fires. |
| `filters` | array | no | `[]` | `[{ "fieldNo": int, "filter": "text" }]`. Each is a standard Business Central filter expression on one field of the inserted record, such as `"<>''"`, `"DOMESTIC"` or `"1000..5000"`. Applied literally: placeholders are not resolved. Max. 250 characters. Duplicate `fieldNo` rows: the last one wins. |

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `Rec` | reference | `tableNo` | The inserted record. It is declared as `value` while `tableNo` is 0. |

Reference it as `{{trigger_Rec}}`.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `tableNo` required and > 0 (canvas marks it required) | (no message) |
| runtime | info | an invalid filter makes the record not match (no error) | (no message) |

There is **no publish-time trigger check**. A flow whose `tableNo` is 0 or does not exist publishes and never fires.

## Runtime errors

None raised to the inserting user. Errors in the flow show up on the execution and in the Job Queue log.

## Example

```json
{
  "id": "2C3D4E5F-6A7B-4C8D-9E0F-1A2B3C4D5E6F",
  "type": "trigger",
  "trigger": 5564402,
  "description": "When a Customer is inserted",
  "slug": "trigger",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/bolt.svg",
  "configuration": {
    "tableNo": 18,
    "filters": [
      { "fieldNo": 21, "filter": "DOMESTIC" }
    ]
  },
  "outputs": [
    { "name": "Rec", "type": "reference", "tableNo": 18 }
  ],
  "level": 0
}
```

## Gotchas

- Fires for inserts from any session: UI, API, posting and Job Queue.
- Do not use a **Confirm dialog** step in these flows. Publishing warns that the confirm runs inside the record change that started the flow.
- Trigger-response steps (Respond to Webhook, Return SubFlow Output, Return PDF, Set report file name, Set document field values, Prevent page close) are hidden in this flow type.
- An auto-increment key is assigned only after the insert. The engine re-resolves `Rec` by SystemId when the run starts, so `Rec` points at the stored row.
