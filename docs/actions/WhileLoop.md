# While Loop

[← All actions](README.md)

Repeats the steps in its body as long as a condition stays true, either checking before each pass (While) or after the first pass (Do-While).

| | |
|---|---|
| Enum name | `WhileLoop` |
| Ordinal | `"action": 106` |
| Category | Control |
| Terminating | `false` |
| Group / edges | Yes: one fixed edge, `"loop"` (the loop body) |
| Availability | GA |

## What it does

Each time the While step is dispatched, it re-substitutes and evaluates `condition` (SmartFilter, same grammar as [Decision](Decision.md)). If the condition is true, the body (`loop` edge) runs, and afterwards the While step is dispatched again. If it is false, the flow continues after the loop. In Do-While mode, the first dispatch skips the check, so the body always runs at least once. A runaway guard, `maxIterations`, fails the step if the condition is still true after that many passes.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `condition` | string | yes (not checked) | – | SmartFilter expression with `{{..}}` placeholders, e.g. `{{trigger_Rec.status}} != Released`. Re-evaluated on every pass. An empty or unparseable condition evaluates to false. |
| `mode` | integer | no | `0` | `0` = While (check first), `1` = Do-While (run the body first). Unknown values are treated as `0`. |
| `maxIterations` | integer | no | `1000` | Maximum number of body passes. A missing value or a value ≤ 0 means 1000. |

## Edges

| value | default description | meaning |
|---|---|---|
| `loop` | `while` | Loop body. Runs once per pass while the condition is true. |

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `iteration` | value | – | 1-based pass number. Inside the body, pass N sees `{{<slug>_iteration}}` = N. |

The step also writes a runtime-only `result` (`loop` or empty) for routing. It is not declared in `outputs`.

## Validation

No editor or publish checks exist for this step. An empty `condition` is accepted and evaluates to false.

## Runtime errors

| condition | message |
|---|---|
| The condition is still true on the dispatch after `maxIterations` body passes | `The While loop did not terminate within its configured maximum of %1 iterations. Review the condition or raise the limit on the step.` |

The limit is exact: with `maxIterations: 3`, the body runs at most 3 times. If the 4th check is false, the loop ends normally. If it is true, the step fails.

## Example

```json
{
  "id": "5F6A7B8C-9D0E-4F1A-8B2C-3D4E5F6A7B01",
  "type": "action",
  "action": 106,
  "description": "Until header is released",
  "slug": "UntilReleased",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/refresh.svg",
  "terminating": false,
  "configuration": {
    "condition": "{{trigger_Rec.status}} != Released",
    "mode": 1,
    "maxIterations": 50
  },
  "outputs": [ { "name": "iteration", "type": "value" } ],
  "edges": [
    { "id": "5F6A7B8C-9D0E-4F1A-8B2C-3D4E5F6A7B02", "value": "loop", "description": "while", "steps": [] }
  ]
}
```

(`trigger_Rec` is a record reference. Record references are stored as record ids, and their fields are read from the database each time the condition is substituted, so the condition sees changes the body made to that record. See the gotchas.)

## Gotchas

- **The condition cannot read outputs of steps inside the body.** Those outputs are deleted every time control returns to the While step, before the condition is evaluated. Base the condition on data that persists across passes, typically a field of a record reference produced before the loop, which is read fresh from the database on each pass. Otherwise the loop either never ends (and hits `maxIterations`) or never starts.
- In mode `0`, a condition that is false at the start skips the body completely. Use mode `1` if the body must run at least once.
- Every pass re-runs the body's steps. In asynchronous runs, each step commits, so a failure halfway leaves the earlier passes committed.
