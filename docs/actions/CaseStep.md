# Case

[← All actions](README.md)

Routes the flow to the branch whose match value equals a given value, with an "Otherwise" branch for everything else.

| | |
|---|---|
| Enum name | `CaseStep` |
| Ordinal | `"action": 105` |
| Category | Control |
| Terminating | `false` |
| Group / edges | Yes: dynamic, one edge per branch plus a fixed default edge `"__default__"` (last) |
| Availability | GA |

## What it does

The step resolves `value` and compares it exactly (case-sensitive text equality) with each entry of `branches`. On a match, it writes that value to `result`, and the engine runs the edge with the same `value`. Without a match, it writes `__default__`, and the "Otherwise" edge runs. If the chosen edge has no steps, the flow continues after the Case step.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `value` | string | yes | – | Value to route on. Supports SmartFields `{{..}}`, SmartFormulas `[[..]]` and SmartControls `{#..#}`. |
| `branches` | array of string | yes (see note) | – | The explicit match values: every edge value except `__default__`, in edge order. Required for "Otherwise" routing. If it is missing, the step runs in legacy mode: an unmatched value continues after the Case step, and `__default__` is never taken. |

`branches` and `edges` must agree. An edge whose value is not listed in `branches` is unreachable.

## Edges

| value | description | meaning |
|---|---|---|
| *any text* (one edge per branch) | branch label | Taken when the resolved `value` equals this text exactly. |
| `__default__` | `Otherwise` | Always present and always the **last** edge. Taken when nothing matches, including an empty value. |

The value `__default__` is reserved. A user branch must not use it.

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `result` | value | – | The matched value, or `__default__`. Referenced as `{{<slug>_result}}`. |

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `value` is empty (required field in the configuration dialog) | `Please fill in the highlighted fields.` |

Nothing checks for duplicate branch values or for a branch that uses the reserved value `__default__`.

## Runtime errors

None from the step itself.

## Example

```json
{
  "id": "1A2B3C4D-5E6F-4A7B-8C9D-0E1F2A3B4C01",
  "type": "action",
  "action": 105,
  "description": "Route by country",
  "slug": "RouteByCountry",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/arrows-split-2.svg",
  "terminating": false,
  "configuration": {
    "value": "{{trigger_Rec.countryregioncode}}",
    "branches": [ "DE", "AT" ]
  },
  "outputs": [ { "name": "result", "type": "value" } ],
  "edges": [
    { "id": "1A2B3C4D-5E6F-4A7B-8C9D-0E1F2A3B4C02", "value": "DE", "description": "Germany", "steps": [] },
    { "id": "1A2B3C4D-5E6F-4A7B-8C9D-0E1F2A3B4C03", "value": "AT", "description": "Austria", "steps": [] },
    { "id": "1A2B3C4D-5E6F-4A7B-8C9D-0E1F2A3B4C04", "value": "__default__", "description": "Otherwise", "steps": [] }
  ]
}
```

(The `trigger_…` placeholder is illustrative. Use an output that exists in your flow.)

## Gotchas

- Whenever you add, rename or remove a branch edge, update `branches` too. The step routes only on `branches` and never looks at the edges itself.
- Matching is plain text: `"1"` ≠ `"1.0"` ≠ `" 1"`, and `de` ≠ `DE`. Normalise the value with a SmartFormula if needed.
- Avoid duplicate branch values and single quotes (`'`) in branch values. Keep branch values to 100 characters or fewer.
- Don't put an empty string in `branches`: the step then emits an empty `result`, which never routes, so no branch runs.
- Outputs of steps inside a branch are deleted once the flow leaves the branch.
