# Rename Record

[← All actions](README.md)

Changes the primary-key values of an existing record (Business Central `Rename`).

| | |
|---|---|
| Enum name | `RenameRecord` |
| Ordinal | `"action": 5564408` |
| Category | Records |
| Terminating | `false` |
| Group / edges | No |
| Availability | GA |

## What it does

The step resolves `reference`, checks that its table equals `tableNo` and re-reads the record. For **every** primary-key field of the table, in key order, it takes the matching `values` row, converts the value to the field type and calls `Rename(...)` with the full new key. Business Central then updates related records (OnRename). The step emits the renamed record, under its new key, as `rec`.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `reference` | string | yes | `""` | One SmartField placeholder resolving to the record, e.g. `"{{FindItem_results}}"`. Same rules as Modify Record. |
| `tableNo` | integer | yes | `0` | Table of the referenced record. It must match the resolved table at runtime. |
| `values` | array | yes | `[]` | One row per primary-key field: `{ "lineNo", "fieldNo", "value", "inputFormat"? }`. Rows for non-key fields are ignored. If several rows target the same key field, the row with the lowest `lineNo` wins. A `validate` key is ignored. The editor pre-fills the key rows when the table is known. |

`value` is SmartText. `inputFormat` works as described for [Insert Record](InsertRecord.md#values-row-shared-by-insert--modify--rename--set-document-field-values), and is useful for Date key fields.

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `rec` | reference | = `configuration.tableNo` | The record under its **new** key. Use `{{<slug>_rec}}` in later steps, not the original reference. |

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `reference` is empty (the Reference field is required) | `Please fill in the highlighted fields.` |

There are no publish-time checks specific to this step. A Confirm dialog after this step gets a publish warning, because this step writes to the database.

## Runtime errors

| condition | message |
|---|---|
| `tableNo` 0/missing | `Table No. is required for a Rename Record step.` |
| `reference` is not a single `{{…}}` placeholder, or does not resolve | `Reference "%1" cannot be resolved to a record.` |
| Resolved table ≠ `tableNo` | `Reference resolves to table %1 but the step is configured for table %2.` |
| A key field has no row | `All primary key fields must be provided. Missing field "%1".` |
| Key has more than 16 fields | `Tables with more than 16 primary key fields are not supported by Rename.` |
| Invalid `inputFormat`, conversion errors | `Cannot convert value "%1" to %2 for field "%3".` (and the variants listed for Insert Record) |
| Target key already exists | Business Central's own error |

## Example

```json
{
  "id": "3B5D7F91-2C4E-4A6B-8D0F-1E3A5C7B9D24",
  "type": "action",
  "action": 5564408,
  "description": "Rename Item",
  "slug": "RenameItem",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/database-star.svg",
  "terminating": false,
  "configuration": {
    "reference": "{{FindItem_results}}",
    "tableNo": 27,
    "values": [
      { "lineNo": 10000, "fieldNo": 1, "value": "NEW-{{trigger_Rec.no}}" }
    ]
  },
  "outputs": [
    { "name": "rec", "type": "reference", "tableNo": 27 }
  ]
}
```

## Gotchas

- You must supply **all** key fields, including the ones that do not change (e.g. *Document Type* and *No.* for a Sales Header).
- `lineNo` must still be unique across rows.
- Renames cascade through related tables and can be slow on heavily used records.
