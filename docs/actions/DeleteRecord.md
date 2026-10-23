# Delete Record

[← All actions](README.md)

Deletes the record that a SmartField reference points to.

| | |
|---|---|
| Enum name | `DeleteRecord` |
| Ordinal | `"action": 5564407` |
| Category | Records |
| Terminating | `false` |
| Group / edges | No |
| Availability | GA |

## What it does

The step resolves `reference` to a record ID, re-reads the record and deletes it with `Delete(triggers)`. Any table is accepted: unlike the other record steps, there is no `tableNo` in the configuration. The delete runs in the flow's database transaction. The step has no outputs.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `reference` | string | yes | `""` | Exactly one SmartField placeholder that resolves to a record reference, e.g. `"{{FindCustomer_results}}"` or `"{{trigger_Rec}}"`. An array reference resolves to its first element. A bare name without `{{ }}` is rejected. |
| `triggers` | boolean | no | `true` | `true` = `Delete(true)` (OnDelete runs, related records are cleaned up by the table code). `false` = `Delete(false)`. |

## Outputs

None.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `reference` is empty (the Reference field is required) | `Please fill in the highlighted fields.` |

There are no publish-time checks specific to this step. A Confirm dialog after this step gets a publish warning, because this step writes to the database.

## Runtime errors

| condition | message |
|---|---|
| `reference` is not a single `{{…}}` placeholder, or does not resolve | `Reference "%1" cannot be resolved to a record.` |
| Record no longer exists | Business Central's "record does not exist" error |
| OnDelete refuses (e.g. open entries) | Business Central's own error |

## Example

```json
{
  "id": "8A2C4E6F-1B3D-4F5A-8C7E-9D1F2A3B4C83",
  "type": "action",
  "action": 5564407,
  "description": "Delete Customer",
  "slug": "DeleteCustomer",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/database-x.svg",
  "terminating": false,
  "configuration": {
    "reference": "{{FindCustomer_results}}",
    "triggers": true
  },
  "outputs": []
}
```

## Gotchas

- With an array reference such as `{{FindX_results}}`, only the **first** record is deleted. To delete all matches, put this step in a For Each loop over the results and reference the loop item.
- Do not reference the deleted record in later steps.
