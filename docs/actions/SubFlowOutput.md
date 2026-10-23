# Return SubFlow Output

[← All actions](README.md)

Ends a SubFlow and returns the configured values to the calling Run SubFlow step.

| | |
|---|---|
| Enum name | `SubFlowOutput` |
| Ordinal | `"action": 5564412` |
| Category | Trigger Responses |
| Terminating | `true` |
| Group / edges | No |
| Availability | GA. Only offered in flows whose trigger is **When invoked as a SubFlow** (`"trigger": 5564404`). |

## What it does

The engine resolves the SmartFields in each `outputs[].value`. The step then builds a JSON object `{ "<name>": "<value>", … }`, with every value as a string, and stops the SubFlow immediately. That object goes back to the caller's [Run SubFlow](RunSubFlow.md) step, which adds one output per key.

If a SubFlow ends without reaching this step, it returns no outputs. That is not an error.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `outputs` | array | no | `[]` | One object per returned value: `{ "name": string, "type": "Value" \| "Reference", "tableNo": integer, "value": string }`. |

The fields of each `outputs[]` entry:

- `name` is the output name the caller sees (truncated to 30 characters there). Make it non-empty and unique: nothing checks this before run time, and a duplicate name fails the step.
- `type` is `"Value"` or `"Reference"` (exact case); anything else, or a missing `type`, counts as `Value`.
- `value` is SmartText for Value rows, or a wrapped reference selector such as `{{FindCustomer_Rec}}` for Reference rows.
- `tableNo` is derived by the editor from the chosen reference, and is `0` for Value rows.

## Outputs

The step's own `outputs[]` mirror `configuration.outputs`: a `value` entry, or a `reference` entry with `tableNo` for `"Reference"` rows. They are informational, because the step ends the SubFlow. The values surface on the caller as `{{<runSubFlowSlug>_<name>}}`.

### Contract with the caller

The caller's Run SubFlow step builds its `outputs[]` from this step's `configuration.outputs`, taken from the SubFlow version it pins.

- If the SubFlow has several Return SubFlow Output steps (for example one per branch), only the **first one found** defines the caller's declared outputs. The search goes in document order, depth-first into edges. Keep the `outputs` names and types identical in all of them.
- Every branch that should return data must end with this step.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| publish | warning | The step has a successor (a following step in the same path, or edges) | Step "%1" is a terminating step but has a successor – terminating steps must end the path. |
| runtime | error | Two `outputs[]` entries have the same `name` | *(platform JSON error about a duplicate key)* |

The step is only offered in the step picker of flows whose trigger is **When invoked as a SubFlow**. Nothing stops it in other flows, but there it has no caller.

## Runtime errors

Apart from duplicate names, none of its own. SmartField resolution errors in `value` fail the step as usual.

## Example

```json
{
  "id": "9B2E61D7-0F3A-4C85-B6E4-17D8A3C5F902",
  "type": "action",
  "action": 5564412,
  "description": "Return SubFlow Output",
  "slug": "ReturnSubFlowOutput",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/arrow-back-up.svg",
  "terminating": true,
  "configuration": {
    "outputs": [
      { "name": "CreditLimit", "type": "Value", "tableNo": 0, "value": "{{FindCustomer_CreditLimitLCY}}" },
      { "name": "Blocked", "type": "Value", "tableNo": 0, "value": "{{FindCustomer_Blocked}}" }
    ]
  },
  "outputs": [
    { "name": "CreditLimit", "type": "value" },
    { "name": "Blocked", "type": "value" }
  ]
}
```

(`FindCustomer_*` stand for outputs of earlier steps in the SubFlow.)

## Gotchas

- Type strings are case-sensitive here: `"Value"` / `"Reference"` (capitalized). This differs from the lowercase `outputs[].type` (`"value"` / `"reference"`) of step objects.
- Reference-typed returns: a selector that points at a record (such as `{{FindCustomer_Rec}}`) is not replaced with text when SmartFields are resolved, so the caller receives the selector text itself as a plain value, not a record. Return a scalar value (No., SystemId) and find the record again in the caller.
- `terminating` must be `true` in the step JSON, and nothing may follow the step in its path.
