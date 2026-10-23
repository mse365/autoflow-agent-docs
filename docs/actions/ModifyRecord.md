# Modify Record

[← All actions](README.md)

Updates non-key fields on an existing record that a SmartField reference points to.

| | |
|---|---|
| Enum name | `ModifyRecord` |
| Ordinal | `"action": 5564406` |
| Category | Records |
| Terminating | `false` |
| Group / edges | No |
| Availability | GA |

## What it does

The step resolves `reference` to a record ID and checks that it belongs to table `tableNo`. It re-reads the record from the database, applies the `values` rows in ascending `lineNo` order (Validate or direct assignment per row), and saves with `Modify(triggers)`. It emits the record as `rec`. Primary-key fields cannot be changed here; use [Rename Record](RenameRecord.md) for those.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `reference` | string | yes | `""` | Exactly one SmartField placeholder that resolves to a record reference, e.g. `"{{FindCustomer_results}}"`, `"{{trigger_Rec}}"` or `"{{InsertCustomer_rec}}"`. An array reference resolves to its first element. Dotted paths are walked through SmartField definitions. A bare name without `{{ }}` is rejected. |
| `tableNo` | integer | yes | `0` | Table of the referenced record. The editor derives it from the reference. At runtime it must equal the resolved record's table. |
| `triggers` | boolean | no | `true` | `true` = `Modify(true)` (OnModify runs), `false` = `Modify(false)`. |
| `values` | array | no | `[]` | Rows `{lineNo, fieldNo, value, validate?, inputFormat?}`, the same shape as in [Insert Record](InsertRecord.md#values-row-shared-by-insert--modify--rename--set-document-field-values). **Non-key fields only.** |

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `rec` | reference | = `configuration.tableNo` | The modified record (same record ID as the input). `{{<slug>_rec}}`. |

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `reference` is empty (the Reference field is required) | `Please fill in the highlighted fields.` |

There are no publish-time checks specific to this step. A Confirm dialog after this step gets a publish warning, because this step writes to the database.

## Runtime errors

| condition | message |
|---|---|
| `tableNo` 0/missing | `Table No. is required for a Modify Record step.` |
| `reference` is not a single `{{…}}` placeholder, or does not resolve | `Reference "%1" cannot be resolved to a record.` |
| Resolved table ≠ `tableNo` | `Reference resolves to table %1 but the step is configured for table %2.` |
| A `values` row targets a primary-key field | `Field "%1" is part of the primary key and cannot be modified. Use a Rename Record step instead.` |
| `fieldNo` not in table | `Field %1 does not exist in table %2.` |
| Invalid `inputFormat`, conversion errors | Same as Insert Record (`Cannot convert value "%1" to %2 for field "%3".` …) |
| Record deleted meanwhile, validation or OnModify errors | Business Central's own error |

## Example

```json
{
  "id": "1F7B3C2D-5E6A-4B8C-9D0E-2A3B4C5D6E72",
  "type": "action",
  "action": 5564406,
  "description": "Modify Customer",
  "slug": "ModifyCustomer",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/database-edit.svg",
  "terminating": false,
  "configuration": {
    "reference": "{{FindCustomer_results}}",
    "tableNo": 18,
    "triggers": true,
    "values": [
      { "lineNo": 10000, "fieldNo": 39, "value": "All", "validate": true },
      { "lineNo": 20000, "fieldNo": 102, "value": "{{trigger_Rec.email}}", "validate": false }
    ]
  },
  "outputs": [
    { "name": "rec", "type": "reference", "tableNo": 18 }
  ]
}
```

(Customer field 39 = *Blocked*, an Option/Enum given by member name; field 102 = *E-Mail*.)

## Gotchas

- `reference` must include the braces: `"{{FindCustomer_results}}"`, not `"FindCustomer_results"`.
- `tableNo` must match the referenced record's table. A copy-pasted step pointed at another table fails at runtime.
- The record is re-read before the change, so values written by earlier steps are not lost.
- The values rules (unique `lineNo`, `fieldNo` numbers, `inputFormat`, Option names) are the same as for Insert Record.
