# Create Element

[← All actions](README.md)

Declares a single-slot variable that holds one text value or one record reference, with an optional initial value.

| | |
|---|---|
| Enum name | `ElementCreate` |
| Ordinal | `"action": 202` |
| Category | Data |
| Terminating | `false` |
| Group / edges | no |
| Availability | GA |

## What it does

The step creates a named slot and publishes it as an output, so that later steps can read it and [Set Element](ElementSet.md) steps can overwrite it. A Value element always writes its slot at run time: the resolved `initialValue`, or `''` if none is given. As a result, references to it resolve even before any Set Element step runs. A Reference element writes its slot only when `initialValue` is given. Otherwise the slot stays unset until a Set Element step fills it.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `elementName` | string (max 30) | yes | `""` | Name of the element and of the step's output. Plain text. The name is truncated to 30 characters at run time, so keep it to 30 characters or fewer. |
| `elementType` | integer | yes | `0` | `0` = Value, `1` = Reference. A missing or unknown value is treated as `0`. |
| `tableNo` | integer | if `elementType` = 1 | `0` | Table that the reference points to. The editor writes `0` for Value elements. |
| `initialValue` | string | no | `""` | **Value:** SmartText (SmartFields, SmartFormulas, SmartControls), resolved at run time. **Reference:** a single `{{name}}` that resolves to an upstream Reference output of the same table, or empty. |

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `<elementName>` | `value` | – | when `elementType` = 0 |
| `<elementName>` | `reference` | `<tableNo>` | when `elementType` = 1 |

To reference the element, use `{{<slug>_<elementName>}}`, for example `{{Total_Amount}}`. For a Reference element you can also use field paths such as `{{BestCust_Customer.name}}` (see [field paths](../references-and-smart-fields.md#13-walking-a-path-through-records)).

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `elementName` non-empty | Please fill in the highlighted fields. |
| editor | error | `elementType` is 0 or 1 | – |
| editor | error | `tableNo` non-zero when `elementType` = 1 | Please fill in the highlighted fields. |
| runtime | warning | `elementName` longer than 30 characters is truncated, so the declared output does not match | – |

Publishing does not re-run the editor checks.

## Runtime errors

- `Reference elements require a single SmartField placeholder for the initial value, e.g. '{{name}}'. Got: %1`: occurs for a Reference element whose `initialValue` is not a single placeholder.
- `Reference '%1' not found in context.`: the placeholder does not resolve to a Reference in the current run.

## Example

```json
{
  "id": "9A8B7C6D-5E4F-4A3B-8C2D-1E0F9A8B7C6D",
  "type": "action",
  "action": 202,
  "description": "Create Amount Element",
  "slug": "Total",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/createelement.svg",
  "terminating": false,
  "configuration": {
    "elementName": "Amount",
    "elementType": 0,
    "tableNo": 0,
    "initialValue": "0"
  },
  "outputs": [
    { "name": "Amount", "type": "value" }
  ]
}
```

## Gotchas

- Neither the editor nor the run time checks that a Reference `initialValue` belongs to the same table as `tableNo`. Keep them consistent yourself.
- If the step sits inside a loop or branch body, its slot is removed when the body is left. Create elements at the level where you need to read them.
