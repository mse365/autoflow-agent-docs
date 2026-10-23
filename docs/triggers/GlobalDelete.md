# When a record is deleted

[← All triggers](README.md)

Starts a background run whenever a record of the configured table is deleted, and carries selected field values of the deleted record into the flow.

| | |
|---|---|
| Enum name | `GlobalDelete` |
| Ordinal | `"trigger": 5564451` |
| Category | Records |
| Terminating | n/a (trigger) |
| Group / edges | no |
| Availability | GA |

## What it does

Hooks Business Central's global delete event for `tableNo`. When the deleted record matches `filters`, the values of the `outputFields` are captured as text and a pending execution is created inside the deleting transaction. A recurring Job Queue entry (every 5 minutes, created at publish) queues one background run per pending execution, and each run commits after every step. Because the record is gone by then, there is **no `Rec` reference**, only the captured values.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `tableNo` | integer | yes | `0` | Table to watch. |
| `filters` | array | no | `[]` | `[{ "fieldNo": int, "filter": "text" }]`. These are standard filter expressions, applied literally with no placeholders, max. 250 characters. |
| `outputFields` | array | no | `[]` | `[{ "fieldNo": int, "name": "text" }]`. Each entry is one field to capture. `name` is the output name (max. 30 characters). The editor fills it from the caption in PascalCase (`No.` becomes `No`, `Größe` becomes `Groesse`). |

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| *outputFields[].name* | value | – | One per configured field. The value is locale-invariant text, for example `12345.67` or `2026-10-23`. |

Reference them as `{{trigger_<name>}}`.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `tableNo` present and > 0 | (no message) |
| runtime | info | an invalid filter means the record does not match (no error) | (no message) |

There is no publish-time trigger check.

## Runtime errors

None raised to the deleting user.

## Example

```json
{
  "id": "4E5F6A7B-8C9D-4E0F-9A1B-2C3D4E5F6A7B",
  "type": "trigger",
  "trigger": 5564451,
  "description": "When a Customer is deleted",
  "slug": "trigger",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/bolt.svg",
  "configuration": {
    "tableNo": 18,
    "filters": [],
    "outputFields": [
      { "fieldNo": 2, "name": "Name" },
      { "fieldNo": 102, "name": "E-Mail" }
    ]
  },
  "outputs": [
    { "name": "Name", "type": "value" },
    { "name": "E-Mail", "type": "value" }
  ],
  "level": 0
}
```

The example sets `name` to the field's own name on purpose. See the first gotcha.

## Gotchas

- **Name mismatch.** The flow declares the output as `outputFields[].name`, but the run stores the value under the table field's own name, for example `No.` rather than `No`. When the two differ, `{{trigger_<name>}}` stays empty. Use the field's exact name as `name`, and check with a test run. Fields whose names contain spaces or dots may not be referenceable at all.
- No `Rec` output. List every field you need in `outputFields`.
- A **Confirm dialog** step gets a publish warning, because it runs inside the record change that started the flow.
- Trigger-response steps are hidden in this flow type.
