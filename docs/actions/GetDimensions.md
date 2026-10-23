# Get Dimensions

[← All actions](README.md)

Reads selected dimension values from a record that has a *Dimension Set ID*. Each value is returned as a value output named after its dimension code.

| | |
|---|---|
| Enum name | `GetDimensions` |
| Ordinal | `"action": 5564559` |
| Category | Records |
| Terminating | `false` |
| Group / edges | No |
| Availability | GA |

## What it does

The step resolves `reference`, checks that its table equals `tableNo` and reads the record's dimension set. For each distinct dimension code in `dimensions`, it emits two value outputs:

- `<CODE>`: the dimension value code.
- `<CODE>_Name`: the value's name.

If the record has no value for a code, both outputs are empty. The step only reads.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `reference` | string | yes | `""` | One SmartField placeholder resolving to the record, e.g. `"{{trigger_Rec}}"`. The table must have a *Dimension Set ID* field. |
| `tableNo` | integer | yes | `0` | Table of the referenced record. It must match at runtime. |
| `dimensions` | array | no | `[]` | Rows `{ "dimensionCode": "<code>" }`. Codes are trimmed and upper-cased, and duplicates and empty codes are ignored. The editor also writes `lineNo`, which the step ignores. |

## Outputs

Generated from `dimensions`, in row order, with two entries per distinct code:

| name | type | tableNo | notes |
|---|---|---|---|
| `<DIMENSIONCODE>` | value | – | E.g. `DEPARTMENT`, used as `{{<slug>_DEPARTMENT}}`. |
| `<DIMENSIONCODE>_Name` | value | – | E.g. `{{<slug>_DEPARTMENT_Name}}`. |

There is no `rec` output.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `tableNo` missing/0, or `reference` is not a `{{…}}` placeholder | – (step shown as not configured) |

There are no publish-time checks specific to this step.

## Runtime errors

| condition | message |
|---|---|
| `tableNo` 0/missing | `Table No. is required for a Get Dimensions step.` |
| Reference does not resolve | `Reference "%1" cannot be resolved to a record.` |
| Resolved table ≠ `tableNo` | `Reference resolves to table %1 but the step is configured for table %2.` |
| Table has no *Dimension Set ID* field | `Table "%1" has no "Dimension Set ID" field, so dimensions cannot be set on it.` (the same text as Set Dimension Values) |

Unknown dimension codes do **not** raise an error. Their outputs are simply empty.

## Example

```json
{
  "id": "0B2D4F6A-8C9E-4A1B-8D3F-5A7C9E1B3D0B",
  "type": "action",
  "action": 5564559,
  "description": "Get dimensions from Sales Header",
  "slug": "GetDimensions",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/chart-scatter-3d.svg",
  "terminating": false,
  "configuration": {
    "reference": "{{trigger_Rec}}",
    "tableNo": 36,
    "dimensions": [
      { "dimensionCode": "DEPARTMENT" },
      { "dimensionCode": "PROJECT" }
    ]
  },
  "outputs": [
    { "name": "DEPARTMENT", "type": "value" },
    { "name": "DEPARTMENT_Name", "type": "value" },
    { "name": "PROJECT", "type": "value" },
    { "name": "PROJECT_Name", "type": "value" }
  ]
}
```

## Gotchas

- Output names are the **upper-cased** codes. If you write `"dimensionCode": "department"`, the output is still `DEPARTMENT`.
- Keep `outputs` in sync with `dimensions` by hand when you edit JSON: two entries per code, in order.
