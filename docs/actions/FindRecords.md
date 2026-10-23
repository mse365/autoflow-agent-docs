# Find Records

[← All actions](README.md)

Searches a table using field filters, an optional SmartFilter and a sort key, and returns the matching records as a reference array.

| | |
|---|---|
| Enum name | `FindRecords` |
| Ordinal | `"action": 5564409` |
| Category | Records |
| Terminating | `false` |
| Group / edges | No |
| Availability | GA |

## What it does

The step opens table `tableNo`, applies the sort key (`keyFields` and `ascending`) and sets one database filter per `filters` row. It then reads the records in order. If `smartFilter` is set, it is evaluated for each record and only records where it is true are kept. Reading stops after `limit` kept records. Each kept record is emitted as `results[0]`, `results[1]`, … plus the alias `results` (= first record), and the number of kept records is emitted as `count`. With `errorOnEmpty`, an empty result fails the step. The step only reads and does not lock anything.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `tableNo` | integer | yes | `0` | Table to search, as a JSON number. |
| `filters` | array | no | `[]` | Database filters: `[{ "fieldNo": <int>, "filter": "<BC filter>" }]`. See below. |
| `smartFilter` | string | no | `""` | SmartFilter expression evaluated per record. It is a **plain string, not JSON**. See below. |
| `limit` | integer | no | `100` | Maximum number of records returned. Missing, `0` or negative means 100. |
| `errorOnEmpty` | boolean | no | `false` | `true` = fail with an error when nothing matches. |
| `keyFields` | string | no | `""` | Sort key, given as the comma-joined **field names** of an active table key, exactly as declared and without spaces after commas, e.g. `"Document Type,Sell-to Customer No."`. Empty = primary key. Unknown values silently fall back to the primary key. |
| `ascending` | boolean | no | `true` | Sort direction. |

### `filters[]`

| key | type | description |
|---|---|---|
| `fieldNo` | integer | Field **number**. Rows with `0` are skipped. If several rows target the same field, the last one wins. |
| `filter` | string | Business Central filter syntax, as in the filter pane: `10000..20000`, `<>0`, `A*\|B*`, `@*gmbh*`, `''` (empty), `<>''`. `{{SmartFields}}` are resolved against the **flow context** before filtering. The result is truncated to 250 characters. On a RecordId field, a filter that is exactly one reference SmartField (e.g. `{{trigger_Rec}}`) filters on that record. |

The editor also writes `lineNo` on each row. The step ignores it.

### `smartFilter` grammar

- Comparison: `left op right`, where `op` is one of `=`, `!=`, `>`, `<`, `>=`, `<=`, `~` (contains), `^=` (starts with), `$=` (ends with). Both sides are compared as numbers when both parse as numbers, otherwise as case-sensitive text. `''` stands for an empty string.
- Combination: `(A) & (B)`, `(A) | (B)`. **Wrap each side in parentheses.** For three or more conditions, nest them pairwise: `((A) & (B)) & (C)`.
- Negation: `!(A)`.
- `{{FieldName}}` is the current record's field, by its **AL field name** (e.g. `{{Balance}}`, `{{Country/Region Code}}`), formatted with regional settings. Other `{{slug_output}}` SmartFields come from the flow context.
- Not available: Blob, Media, MediaSet, Guid, RecordId and TableFilter fields, and FlowFields. FlowFields are not calculated, so filter on them with `filters` instead.

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `count` | value | – | Number of returned records, as text. Always set (`"0"` when nothing matched). |
| `results` | reference | = `configuration.tableNo` | Reference array. Use `{{<slug>_results}}` (= first record), `{{<slug>_results[0]}}`, `{{<slug>_results[1]}}`, … It is the usual source of a For Each loop. Only set when at least one record matched. |

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `tableNo` missing or `0` | – (step shown as not configured) |

There are no publish-time checks specific to this step. As for every step, `{{x_y}}` placeholders whose part before the first underscore is not a known slug produce a publish warning, and that includes SmartFilter field names that contain `_`.

## Runtime errors

| condition | message |
|---|---|
| `errorOnEmpty` = true and nothing matched | `No records found in table %1 matching the specified filters.` |
| `tableNo` is 0 or the table does not exist | Business Central's error opening the table |
| Invalid filter expression for the field type, or unknown `fieldNo` | Business Central's own filter / field error |

## Example

```json
{
  "id": "5E7A9C1B-3D5F-4B7A-9C1E-3F5A7B9D1E06",
  "type": "action",
  "action": 5564409,
  "description": "Find Sales Header",
  "slug": "FindSalesHeader",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/database-search.svg",
  "terminating": false,
  "configuration": {
    "tableNo": 36,
    "filters": [
      { "fieldNo": 1, "filter": "Order" },
      { "fieldNo": 2, "filter": "{{trigger_Rec.no}}" },
      { "fieldNo": 120, "filter": "Open" }
    ],
    "smartFilter": "({{Your Reference}} != '') & ({{Location Code}} ^= WH)",
    "limit": 10,
    "errorOnEmpty": false,
    "keyFields": "Document Type,Sell-to Customer No.,No.",
    "ascending": false
  },
  "outputs": [
    { "name": "count", "type": "value" },
    { "name": "results", "type": "reference", "tableNo": 36 }
  ]
}
```

(Sales Header: field 1 = *Document Type*, 2 = *Sell-to Customer No.*, 120 = *Status*. Check that the key you name in `keyFields` really exists in your BC version.)

## Gotchas

- Sorting is stored as `keyFields` + `ascending`. The editor uses internal `sortKey` / `sortOrder` values, but they are **not** stored in the configuration.
- `filters` (BC filter syntax, applied by the database) and `smartFilter` (AutoFlow expression, evaluated per record) are different languages. Use `filters` wherever possible: they are faster, and `limit` counts only records that pass the SmartFilter, so a selective SmartFilter can read the whole table.
- Without parentheses, the SmartFilter evaluator matches `=` before `&` / `|`, so `A = 1 & B = 2` is **wrong**. Write `(A = 1) & (B = 2)`. Literal `&`, `|`, `(` or `)` inside values break the expression.
- In `smartFilter`, a `.` inside `{{…}}` is read as a path separator and `;` starts a format suffix. Record fields whose name contains a dot (`No.`, `External Document No.`) therefore cannot be used as `{{FieldName}}`. Filter on them with `filters` instead.
- In SmartFilter comparisons, decimals and dates are formatted with the regional settings of the session that runs the flow.
- Field-filter SmartFields cannot refer to fields of the records being searched. Use `smartFilter` for that.
- Keep `outputs` in this order and keep `results.tableNo` equal to `configuration.tableNo`.
