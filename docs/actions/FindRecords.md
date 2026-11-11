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
| `filters` | array | no | `[]` | Database filters: `[{ "fieldNo": <int>, "filter": "<BC filter>", "filterMode"?: "fixed" \| "rules", "filterRules"?: {…} }]`. See below. |
| `smartFilter` | string | no | `""` | SmartFilter expression evaluated per record. It is a **plain string, not JSON**. See below. |
| `limit` | integer | no | `100` | Maximum number of records returned. Missing, `0` or negative means 100. |
| `errorOnEmpty` | boolean | no | `false` | `true` = fail with an error when nothing matches. |
| `keyFields` | string | no | `""` | Sort key, given as the comma-joined **field names** of an active table key, exactly as declared and without spaces after commas, e.g. `"Document Type,Sell-to Customer No."`. Empty = primary key. Unknown values silently fall back to the primary key. |
| `ascending` | boolean | no | `true` | Sort direction. |

### `filters[]`

| key | type | description |
|---|---|---|
| `fieldNo` | integer | Field **number**. Rows with `0` are skipped. If several rows target the same field, the last one wins. |
| `filter` | string | Business Central filter syntax, as in the filter pane: `10000..20000`, `<>0`, `A*\|B*`, `@*gmbh*`, `''` (empty), `<>''`. `{{SmartFields}}` are resolved against the **flow context** before filtering. The text is cut to 250 characters. On a RecordId field, a filter that is exactly one reference SmartField (e.g. `{{trigger_Rec}}`) filters on that record. With `filterMode: "fixed"` it is an Option/Enum value **name** instead; with `filterMode: "rules"` it is ignored. |
| `filterMode` | string | Optional. `"fixed"` or `"rules"` switch an Option/Enum field's row to a single value (below); anything else or absent = the free filter expression above. Compared case-insensitively. The editor offers the modes only for Option and Enum fields and omits the key in SmartText mode. |
| `filterRules` | object | Only with `filterMode: "rules"`: `{ "rules": [ { "condition": "<SmartFilter>", "value": "<value name>" } ], "otherwise": "<value name>" }`, as in [Insert Record](InsertRecord.md#option-and-enum-fields-valuemode). Also accepted as a JSON string holding that object. |

The editor saves each row as `{fieldNo, filter, filterMode?, filterRules?}`, one row per field. `lineNo` and `fieldCaption` keys are dropped.

#### Option and Enum fields: `filterMode`

In `fixed` and `rules` mode the field is filtered on **exactly one value** (`SetRange` on its ordinal): in `fixed` mode the value named in `filter`, in `rules` mode the value of the first rule whose condition is true, else `otherwise`. The name is matched like a field value (exact name, exact caption, case-insensitive name or caption, then an ordinal number); anything else fails with `'%1' is not a value of %2. Allowed: %3.` (%2 = field caption, %3 = the value names). A Rules row where no rule matches and `otherwise` is empty or absent does **not** filter the field at all. Both modes only work on Option/Enum fields; on any other field the same error is raised with an empty `Allowed:` list.

Ranges, alternatives and wildcards (`Open|Released`, `<>Open`) need the free expression: omit `filterMode` and write the captions or ordinals Business Central's filter syntax expects, e.g. `"filter": "Open|Released"`.

### `smartFilter` grammar

- Comparison: `left op right`, where `op` is one of `=`, `!=`, `>`, `<`, `>=`, `<=`, `~` (contains), `^=` (starts with), `$=` (ends with). Both sides are compared as numbers when both parse as numbers, otherwise as case-sensitive text. `''` stands for an empty string.
- Combination: `(A) & (B)`, `(A) | (B)`. **Wrap each side in parentheses.** For three or more conditions, nest them pairwise: `((A) & (B)) & (C)`.
- Negation: `!(A)`.
- `{{FieldName}}` is the current record's field, by its **AL field name** (e.g. `{{Balance}}`, `{{Country/Region Code}}`), formatted with regional settings. Other `{{slug_output}}` SmartFields come from the flow context.
- Not available: Blob, Media, MediaSet, Guid, RecordId and TableFilter fields, and FlowFields. FlowFields are not calculated, so filter on them with `filters` instead.

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `count` | value | – | Number of returned records, as text in the regional format (`1,000` and up carry a thousands separator). Always set (`"0"` when nothing matched). |
| `results` | reference | = `configuration.tableNo` | Reference array. Use `{{<slug>_results}}` (= first record), `{{<slug>_results[0]}}`, `{{<slug>_results[1]}}`, … It is the usual source of a For Each loop. Only set when at least one record matched. |

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `tableNo` missing or `0` (the Table field is required) | `Please fill in the highlighted fields.` |
| editor (status line) | warning | A `filters` row in Rules mode has a rule with a blank condition or an empty value. Advisory, does not block saving; at runtime such a rule never matches. | `Filters, row 2: Rule 1 needs a condition and a value.` |

There are no publish-time checks specific to this step. As for every step, `{{x_y}}` placeholders whose part before the first underscore is not a known slug produce a publish warning, and that includes SmartFilter field names that contain `_`.

## Runtime errors

| condition | message |
|---|---|
| `errorOnEmpty` = true and nothing matched | `No records found in table %1 matching the specified filters.` |
| `filterMode` `fixed` / `rules` names a value the field does not have, or the field is not Option/Enum | `'%1' is not a value of %2. Allowed: %3.` |
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
      { "fieldNo": 1, "filter": "Order", "filterMode": "fixed" },
      { "fieldNo": 2, "filter": "{{trigger_Rec.no}}" },
      { "fieldNo": 120, "filter": "Open", "filterMode": "fixed" }
    ],
    "smartFilter": "({{Your Reference}} != '') & ({{Location Code}} ^= WH)",
    "limit": 10,
    "errorOnEmpty": false,
    "keyFields": "Document Type,Sell-to Customer No.",
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
- For an Option/Enum field, prefer `filterMode: "fixed"` with the value **name**: it is language-independent, whereas a free expression such as `"filter": "Offen"` depends on the caption language of the session that runs the flow. Use the free expression only for ranges or alternatives.
- Before 27.0.41: `filterMode` / `filterRules` did not exist; every row was a free filter expression (a hand-written `filterMode` was ignored), and the editor saved rows as `{fieldNo, filter}` only.
- Keep `outputs` in this order and keep `results.tableNo` equal to `configuration.tableNo`.
