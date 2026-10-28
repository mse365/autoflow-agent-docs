# Insert Record

[← All actions](README.md)

Creates a new record in a table, optionally pre-filled from a template, and returns a reference to it.

| | |
|---|---|
| Enum name | `InsertRecord` |
| Ordinal | `"action": 5564405` |
| Category | Records |
| Terminating | `false` |
| Group / edges | No |
| Availability | GA |

## What it does

The step opens the table `tableNo` and initialises an empty record. What happens with `templateCode` depends on the table:

- **Customer (18), Vendor (23), Item (27), Employee (5200)**: `templateCode` names a Business Central template (`Customer Templ.`, `Vendor Templ.`, `Item Templ.`, `Employee Templ.`). The step applies the `values` rows, takes the number from the template's No. Series if the number is still empty, inserts with `Insert(triggers)`, and then runs BC's `Apply<X>Template` with *UpdateExistingValues = false*: the template fills only fields that are still empty, copies its default dimensions (items: also the base unit of measure) and ends with `Modify(true)` – also when `triggers` is `false`. If no such template exists but a Configuration Template with that code exists for the same table, the step uses it the Configuration Template way (below).
- **Every other table**: `templateCode` names a Configuration Template (RapidStart). Its field lines are validated into the record first, then the `values` rows are applied, then `Insert(triggers)`.

The `values` rows are applied in ascending `lineNo` order, with Validate or direct assignment per row, and win over the template for the same field. The new record is emitted as the reference output `rec`.

The insert runs inside the flow's database transaction. Any error (conversion, validation, duplicate key) fails the step.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `tableNo` | integer | yes | `0` | Table number to insert into, as a JSON number (e.g. `18` = Customer). |
| `triggers` | boolean | no | `true` | Run Triggers. `true` = `Insert(true)`, so OnInsert and its subscribers run. `false` = insert without the table trigger. |
| `templateCode` | string | no | `""` | Template code (max 20). Customer/Vendor/Item/Employee: a Business Central template of that table, with a Configuration Template of the same table as fallback. Other tables: a Configuration Template (max 10) whose table must be `tableNo`. `values` win over the template. |
| `values` | array | no | `[]` | Field assignments, see below. Primary-key fields are allowed. The editor pre-fills one row per primary-key field. |

### `values[]` row (shared by Insert / Modify / Rename / Set document field values)

| key | type | required | default | description |
|---|---|---|---|---|
| `lineNo` | integer | yes | – | Order and row key. Must be **unique** in the array. The editor writes `10000, 20000, …`. |
| `fieldNo` | integer | yes | – | Field **number**, not the field name. A row with `0` is skipped. |
| `value` | string | no | `""` | SmartText. `{{slug_output}}`, `[[formula]]` and SmartControls are resolved, then the text is converted to the field type. |
| `validate` | boolean | no | `true` | `true` = `Validate(field, value)` (OnValidate runs). `false` = direct assignment. |
| `inputFormat` | string | no | `""` (omitted) | How the text is parsed. Empty = regional format of the running session. `"9"`/`"xml"` = invariant (`1234.5`, `2026-07-16`, `true`). Or a date/time pattern from `yyyy yy MM dd HH mm ss` plus separators (e.g. `yyyyMMdd`, `dd.MM.yyyy HH:mm`), for Date/Time/DateTime fields only. Max 30 chars. |

Conversion per field type:
- **Integer, BigInteger, Decimal, Boolean, Duration**: Evaluate, regional or invariant.
- **Date, Time, DateTime**: Evaluate, or the pattern.
- **Option**: the ordinal, the English member name or the localized caption. Names must match exactly, including case.
- **Guid**: `""` gives an empty GUID.
- **Code, Text**: taken as-is.
- **RecordId**: only from a reference SmartField such as `{{FindItem_results}}`.
- **Blob, Media**: a bare binary SmartField is streamed. Otherwise the value is base64-decoded, with UTF-8 text as the fallback. MediaSet is not supported.

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `rec` | reference | = `configuration.tableNo` | The inserted record. Use `{{<slug>_rec}}` as a `reference`, or `{{<slug>_rec.No.}}` for a field. |

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `tableNo` missing or `0` (the Table field is required) | `Please fill in the highlighted fields.` |

There are no publish-time checks specific to this step. A Confirm dialog placed after it gets a publish warning, because this step writes to the database.

## Runtime errors

| condition | message |
|---|---|
| `tableNo` is 0 or missing | `Table No. is required for an Insert Record step.` |
| Template not found (Customer/Vendor/Item/Employee) | `There is no %1 template "%2".` (%1 = table caption) |
| Template not found (other tables) | `Configuration Template "%1" does not exist.` |
| Template table ≠ `tableNo` | `Configuration Template "%1" is for table %2, but the step is configured for table %3.` |
| `fieldNo` not in table | `Field %1 does not exist in table %2.` |
| Invalid `inputFormat` (not empty, `9`, `xml` or a valid pattern) | `"%1" is not a valid input format. Leave it empty for the regional format, enter 9 or xml for the invariant XML notation, or enter a date/time pattern such as yyyyMMdd (tokens yyyy, yy, MM, dd, HH, mm, ss plus separators).` |
| Pattern used on a non-date field | `Input format "%1" is a date/time pattern and can only be used for Date, Time, or DateTime fields. Field "%2" is of type %3.` |
| Value not convertible | `Cannot convert value "%1" to %2 for field "%3".` / `Cannot convert value "%1" to %2 for field "%3" using input format "%4".` |
| Duplicate `lineNo` in `values` | Platform "record already exists" error |
| Validation / OnInsert / duplicate primary key | Business Central's own error |

## Example

```json
{
  "id": "6C1A2E3F-4B5D-4E6F-8A7B-9C0D1E2F3A41",
  "type": "action",
  "action": 5564405,
  "description": "Insert Customer",
  "slug": "InsertCustomer",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/database-plus.svg",
  "terminating": false,
  "configuration": {
    "tableNo": 18,
    "triggers": true,
    "templateCode": "",
    "values": [
      { "lineNo": 10000, "fieldNo": 1, "value": "NEW-{{trigger_Rec.no}}", "validate": true },
      { "lineNo": 20000, "fieldNo": 2, "value": "{{trigger_Rec.name}}", "validate": true },
      { "lineNo": 30000, "fieldNo": 35, "value": "DE", "validate": true },
      { "lineNo": 40000, "fieldNo": 20, "value": "5000.00", "validate": true, "inputFormat": "9" }
    ]
  },
  "outputs": [
    { "name": "rec", "type": "reference", "tableNo": 18 }
  ]
}
```

## Gotchas

- Fields are addressed by **number** (`fieldNo`), never by name.
- `lineNo` must be unique. Two rows without `lineNo` both become 0 and the step fails. The editor renumbers rows `10000, 20000, …` on every save.
- Rows are applied in `lineNo` order, and that order matters with `validate: true`: validating e.g. *Sell-to Customer No.* later overwrites fields you set earlier.
- Keep `outputs[0].tableNo` equal to `configuration.tableNo`.
- Without `inputFormat`, decimals and dates are parsed in the **regional format of the user or job-queue session that runs the flow**. Use `"inputFormat": "9"` for machine-generated values such as `1234.50` or `2026-07-16`.
- If you omit primary-key fields, the table's OnInsert (`triggers: true`) must fill them, e.g. from a number series. Otherwise the insert fails or creates a record with an empty key.
- Scalar SmartFields anywhere in the configuration are resolved before the step runs. Reference SmartFields are kept for the step to resolve.
- Up to AutoFlow 27.0.40, `templateCode` always named a Configuration Template (max 10 characters), also on Customer, Vendor, Item and Employee. Business Central templates are used from the release after 27.0.40.
