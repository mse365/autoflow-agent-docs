# Draw number from number series

[← All actions](README.md)

Draws (consumes) the next number from a Business Central number series and returns it as the `Number` output.

| | |
|---|---|
| Enum name | `NoSeriesDraw` |
| Ordinal | `"action": 5564554` |
| Category | Records |
| Terminating | `false` |
| Group / edges | No |
| Availability | GA |

## What it does

The step resolves `noSeriesCode` and the optional `usageDate` (empty = work date) and checks that the No. Series exists. It then calls Business Central's standard *get next number* for that date. The series advances, so the same number is never drawn twice. The number is emitted as the value output `Number` and logged. The default description in the editor is "Draw Number". Once a series is chosen, it becomes "Draw Number from <code>".

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `noSeriesCode` | string | yes | `""` | No. Series code, e.g. `"P-INV"`, or a SmartField that yields it. Max 20 characters. |
| `usageDate` | string | no | `""` | Date that selects the No. Series line (Starting Date). Empty = work date. It can be a literal or a SmartField and is parsed in the **regional date format** of the session that runs the flow. |

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `Number` | value | – | The drawn number. Reference it as `{{<slug>_Number}}`, with a capital N. |

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `noSeriesCode` is empty (a `{{…}}` placeholder is accepted) | `Select the number series to draw the next number from.` |

There are no publish-time checks specific to this step. A Confirm dialog after this step gets a publish warning, because this step writes to the database.

## Runtime errors

| condition | message |
|---|---|
| `usageDate` not parseable | `The usage date "%1" is not a valid date.` |
| Series does not exist | `The number series %1 does not exist.` |
| Series not drawable (no line for the date, exhausted, no default numbers) | Business Central's own No. Series error |

## Example

```json
{
  "id": "4C6E8A0B-2D3F-4E5A-8B7C-9D1E3F5A7B89",
  "type": "action",
  "action": 5564554,
  "description": "Draw Number from P-INV",
  "slug": "DrawNumberFromPINV",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/number.svg",
  "terminating": false,
  "configuration": {
    "noSeriesCode": "P-INV",
    "usageDate": ""
  },
  "outputs": [
    { "name": "Number", "type": "value" }
  ]
}
```

A later step can use it, e.g. `{ "lineNo": 10000, "fieldNo": 3, "value": "{{DrawNumberFromPINV_Number}}" }`.

## Gotchas

- The output name is fixed as `Number`. If a flow has several draw steps, the slug tells them apart.
- A drawn number is consumed even if you never use it.
- Leave `usageDate` empty unless the series has date-dependent lines. If you do set it, it must match the regional format of the session that runs the flow; there is no invariant option.
