# Decision

[← All actions](README.md)

Evaluates a condition to yes or no and continues along the matching branch.

| | |
|---|---|
| Enum name | `Decision` |
| Ordinal | `"action": 100` |
| Category | Control |
| Terminating | `false` |
| Group / edges | Yes: two fixed edges, `"true"` and `"false"` |
| Availability | GA |

## What it does

At runtime the step substitutes all `{{slug_output}}` placeholders in `condition`, evaluates the resulting text as a SmartFilter expression and writes `"true"` or `"false"` to its `result` output. The engine then runs the steps of the edge whose `value` equals `result`. When that edge has no steps (or does not exist), the flow continues with the step after the Decision. A malformed or empty condition does not raise an error. It evaluates to `false`.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `condition` | string | no (but without it the result is always `false`) | `""` | SmartFilter expression. Supports SmartFields `{{..}}` (resolved before evaluation), and SmartFormulas/SmartControls inside operands. See the grammar below. |

The branch labels ("True label" / "False label" in the editor) are **not** configuration keys. They are stored as `edges[0].description` and `edges[1].description`.

### Condition grammar

| form | example |
|---|---|
| Comparison `<left> <op> <right>` | `{{trigger_Rec.balancelcy}} > 1000` |
| Negation `!(<expr>)` | `!({{trigger_Rec.status}} = Released)` |
| AND `(<expr>) & (<expr>)` | `({{a}} = 1) & ({{b}} > 2)` |
| OR `(<expr>) \| (<expr>)` | `({{a}} = 1) \| ({{b}} > 2)` |
| Literal | `true`, `false` |

Operators: `=`, `!=`, `>`, `<`, `>=`, `<=`, `~` (contains), `^=` (starts with), `$=` (ends with).

- When **both** operands parse as numbers, the comparison is numeric. Otherwise it is a case-sensitive text comparison.
- `''` (two single quotes) is the empty string, e.g. `{{trigger_Rec.email}} != ''`. Other quotes are **not** stripped, so write text literals without quotes: `{{trigger_Rec.status}} = Open`.
- Each combinator takes exactly two parenthesised operands. To combine three or more terms, nest them: `(({{a}} = 1) & ({{b}} = 2)) & ({{c}} = 3)`.

## Edges

| value | default description | taken when |
|---|---|---|
| `true` | `Yes` | condition evaluates to true |
| `false` | `No` | condition evaluates to false |

Keep the order `true` then `false`, because the editor reads the labels by position. Either edge may have `"steps": []`.

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `result` | value | – | `"true"` or `"false"`. Referenced as `{{<slug>_result}}`. |

Every action also gets an engine-supplied `iteration` value at runtime. It is not declared in `outputs`.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| – | – | No editor or publish checks exist for this step. | – |

## Runtime errors

None from the step itself. A condition that cannot be parsed evaluates to `false` instead of failing.

## Example

```json
{
  "id": "6E0B4C1A-2F3D-4E5A-8B7C-9D0E1F2A3B01",
  "type": "action",
  "action": 100,
  "description": "Credit limit exceeded?",
  "slug": "CreditCheck",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/arrows-split-2.svg",
  "terminating": false,
  "configuration": {
    "condition": "({{trigger_Rec.balancelcy}} > {{trigger_Rec.creditlimitlcy}}) & ({{trigger_Rec.creditlimitlcy}} != 0)"
  },
  "outputs": [ { "name": "result", "type": "value" } ],
  "edges": [
    { "id": "6E0B4C1A-2F3D-4E5A-8B7C-9D0E1F2A3B02", "value": "true", "description": "Yes", "steps": [] },
    { "id": "6E0B4C1A-2F3D-4E5A-8B7C-9D0E1F2A3B03", "value": "false", "description": "No", "steps": [] }
  ]
}
```

(`GetBalance` and `GetLimit` stand for upstream steps. Use the slugs and output names that exist in your flow.)

## Gotchas

- The expression is evaluated **after** substitution. If a substituted value contains operator or bracket characters (`= < > ~ & | ! ( ) ^ $`), the result can be wrong.
- `a = 1 & b = 2` without parentheses is read as one comparison and gives the wrong answer. Always parenthesise both sides of `&` and `|`.
- `!abc`, where the operand is not a boolean, evaluates to **true**. Only negate parenthesised expressions: `!( ... )`.
- When control leaves the Decision's branch, the outputs of the steps inside that branch are deleted. Steps after the Decision cannot reference outputs produced inside a branch.
