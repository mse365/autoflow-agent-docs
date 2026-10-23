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

The new Dimension Set ID is written to the record. The *Global/Shortcut Dimension 1/2 Code* fields are synced directly, without validation. The record is saved with `Modify(triggers)`, and the step emits `rec` and `dimensionSetId`.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `reference` | string | yes | `""` | One SmartField placeholder resolving to the record, e.g. `"{{trigger_Rec}}"`. The table must have a field named *Dimension Set ID*. |
| `tableNo` | integer | yes | `0` | Table of the referenced record. It must match at runtime. |
| `triggers` | boolean | no | `true` | `true` = `Modify(true)`, `false` = `Modify(false)`. |
| `dimensions` | array | no | `[]` | Rows `{ "dimensionCode": "<code>", "value": "<value code or SmartText>" }`. The code is trimmed and upper-cased, and rows with an empty code are skipped. The value is resolved and trimmed, and an empty value removes the dimension. The editor also writes `lineNo`, which the step ignores. |

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `rec` | reference | = `configuration.tableNo` | The modified record. |
| `dimensionSetId` | value | – | New Dimension Set ID, as text. Use `{{<slug>_dimensionSetId}}`. |

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `tableNo` missing/0, or `reference` is not a `{{…}}` placeholder | – (step shown as not configured) |

There are no publish-time checks specific to this step. A Confirm dialog after this step gets a publish warning, because this step writes to the database.

## Runtime errors

| condition | message |
|---|---|
| `tableNo` 0/missing | `Table No. is required for a Set Dimension Values step.` |
| Reference does not resolve | `Reference "%1" cannot be resolved to a record.` |
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
- Use exact dimension value codes, in upper case.
