# Set Dimension Values

[← All actions](README.md)

Adds, changes or removes dimension values on a record that has a *Dimension Set ID*.

| | |
|---|---|
| Enum name | `SetDimensionValues` |
| Ordinal | `"action": 5564558` |
| Category | Records |
| Terminating | `false` |
| Group / edges | No |
| Availability | GA |

## What it does

The step resolves `reference`, checks that its table equals `tableNo` and loads the record's current dimension set. It then processes the `dimensions` rows in order:

- A row with a value **adds or updates** that dimension.
- A row with an empty value **removes** that dimension.
- Dimensions that are not listed are **kept**.

The new Dimension Set ID is written to the record. The *Global/Shortcut Dimension 1/2 Code* fields are synced directly, without validation. The record is saved with `Modify(triggers)` (`OnModify` runs when `triggers` is `true`), and the step emits `rec` and `dimensionSetId`.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `reference` | string | yes | `""` | One SmartField placeholder resolving to the record, e.g. `"{{trigger_Rec}}"`. The table must have a field named *Dimension Set ID*. |
| `tableNo` | integer | yes | `0` | Table of the referenced record. The editor derives it from the reference. It must match at runtime. |
| `triggers` | boolean | no | `true` | `true` = `Modify(true)`, `false` = `Modify(false)`. |
| `dimensions` | array | no | `[]` | Rows `{ "dimensionCode": "<code>", "value": "<value code or SmartText>" }`. The code is trimmed and upper-cased, and rows with an empty code are skipped. The value is resolved and trimmed, and an empty value removes the dimension. If a code is listed twice, the last row wins. The editor also writes `lineNo` (10000, 20000, …), which the step ignores. |

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `rec` | reference | = `configuration.tableNo` | The modified record. |
| `dimensionSetId` | value | – | New Dimension Set ID, as text. Use `{{<slug>_dimensionSetId}}`. |

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `reference` is empty (required field in the config canvas) | `Please fill in the highlighted fields.` |

There are no publish-time checks for this step. A missing `tableNo` or a `reference` that isn't a single `{{…}}` placeholder is only caught at runtime (see below). A Confirm dialog placed after this step gets a publish warning, because this step writes to the database.

## Runtime errors

| condition | message |
|---|---|
| `tableNo` 0/missing | `Table No. is required for a Set Dimension Values step.` |
| `reference` is not a single `{{…}}` placeholder, or does not resolve | `Reference "%1" cannot be resolved to a record.` |
| Referenced record no longer exists | Business Central's standard "record does not exist" error |
| Resolved table ≠ `tableNo` | `Reference resolves to table %1 but the step is configured for table %2.` |
| Table has no *Dimension Set ID* field | `Table "%1" has no "Dimension Set ID" field, so dimensions cannot be set on it.` |
| Unknown dimension | `Dimension "%1" does not exist.` |
| Unknown dimension value | `Dimension value "%1" does not exist for dimension "%2".` |
| Blocked value | `Dimension value "%1" for dimension "%2" is blocked and cannot be used.` |
| Heading/Total/Begin-Total/End-Total value | `Dimension value "%1" for dimension "%2" is not a standard value and cannot be used in a dimension set.` |

## Example

```json
{
  "id": "7F9B1D3E-5A6C-4E8F-9B0D-2C4E6A8B0D9A",
  "type": "action",
  "action": 5564558,
  "description": "Set dimensions on Sales Header",
  "slug": "SetDimensionsOnSales",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/chart-scatter-3d.svg",
  "terminating": false,
  "configuration": {
    "reference": "{{trigger_Rec}}",
    "tableNo": 36,
    "triggers": true,
    "dimensions": [
      { "dimensionCode": "DEPARTMENT", "value": "SALES" },
      { "dimensionCode": "PROJECT", "value": "{{GetDimensions_PROJECT}}" },
      { "dimensionCode": "AREA", "value": "" }
    ]
  },
  "outputs": [
    { "name": "rec", "type": "reference", "tableNo": 36 },
    { "name": "dimensionSetId", "type": "value" }
  ]
}
```

## Gotchas

- An empty `value` **removes** the dimension. Leave a dimension out completely to keep it.
- On document headers, the step changes only the header's dimension set. Lines are not updated.
- `value` must be an existing, non-blocked, Standard value code of that dimension after resolution. A dimension name or value name doesn't work.
