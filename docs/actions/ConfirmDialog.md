# Confirm dialog

[← All actions](README.md)

Asks the user a yes/no question and continues along the matching branch.

| | |
|---|---|
| Enum name | `ConfirmDialog` |
| Ordinal | `"action": 5564418` |
| Category | Control |
| Terminating | `false` |
| Group / edges | Yes: two fixed edges, `"true"` (Yes) and `"false"` (No) |
| Availability | GA. Offered in every flow, foreground or background. |

## What it does

The step resolves `message` and gets a Yes/No answer, then writes `"true"` or `"false"` to `result`, and the engine runs the matching edge. Where the answer comes from depends on the session:

- **Interactive session**: a standard confirm dialog. `defaultYes` preselects Yes.
- **Job queue (background) run with `waitMinutes` > 0**: the question is parked and checked every 2 seconds until the deadline. A user who follows the run, or anyone who opens the execution, is asked, and the first answer wins. The job queue session stays busy while it waits. If nobody answers in time, `noGuiAnswer` applies.
- **Any other session without a user interface** (e.g. a web service call): `noGuiAnswer` applies immediately.

The answer, and who gave it, is written to the execution log. Business Central cannot open a dialog after the flow has written to the database, or inside the record change that started the flow. Place the step before any writing step.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `message` | string | yes | – | The question. Supports SmartFields `{{..}}`, SmartFormulas `[[..]]` and SmartControls `{#..#}`. The copy used for background answering is cut at 2048 characters. |
| `defaultYes` | boolean | no | `false` | Preselects Yes in the dialog. Legacy behaviour: if `noGuiAnswer` is absent, `defaultYes` also acts as the no-UI answer (true = Yes, false = No). |
| `noGuiAnswer` | integer | no | `0` | When nobody can answer: `0` = raise an error, `1` = answer Yes, `2` = answer No. Always write it explicitly. |
| `waitMinutes` | integer | no | `5` | Job queue runs only: minutes to wait for an answer. `0` = do not wait. Range 0–15. |

The branch labels are stored as `edges[0].description` (Yes) and `edges[1].description` (No), not in `configuration`.

## Edges

| value | default description | taken when |
|---|---|---|
| `true` | `Yes` | the answer is Yes |
| `false` | `No` | the answer is No |

Keep the order `true` then `false`.

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `result` | value | – | `"true"` / `"false"`. Referenced as `{{<slug>_result}}`. |

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `message` is empty | `Enter the question to ask the user.` |
| editor | error | `waitMinutes` outside 0–15 | `The waiting time must be between 0 and %1 minutes.` (%1 = 15) |
| publish | warning | The trigger runs inside the record change (Document modified 5564529, Global insert 5564402, Global modify 5564450, Global delete 5564451) | `The confirm dialog '%1' runs inside the record change that started the flow. Business Central does not open dialogs there, so when a user triggers the flow it fails at this step. It only works when the flow runs in the background, where the answer under 'Without a user interface' applies.` |
| publish | warning | A writing step (insert/modify/delete/rename record, set document field values, add item tracking, set dimension values, draw number from number series) appears earlier in document order | `The confirm dialog '%1' may run after a step that writes ('%2'). Business Central cannot open a dialog once a flow has written, so the flow would fail there. Move the confirm dialog ahead of the writing steps.` |

`%1` and `%2` are step **ids**. The "writes before" check walks the JSON in document order: each step, then the steps nested in its edges, depth-first. It can therefore flag a writing step on a branch that would not actually run before the dialog.

## Runtime errors

| condition | message |
|---|---|
| No user interface, no answer in time, `noGuiAnswer` = 0 | `The flow runs without a user interface, so nobody can answer the confirm dialog "%1". To let the flow continue, choose Answer Yes or Answer No under "Without a user interface" in the step.` |
| Dialog requested after the flow has written, or inside the triggering record change, in an interactive session | Business Central platform error (the dialog cannot be opened) |

## Example

```json
{
  "id": "8C9D0E1F-2A3B-4C4D-9E5F-6A7B8C9D0E01",
  "type": "action",
  "action": 5564418,
  "description": "Confirm dialog",
  "slug": "ConfirmDialog",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/help-circle.svg",
  "terminating": false,
  "configuration": {
    "message": "Send the order confirmation to {{trigger_Rec.email}}?",
    "defaultYes": true,
    "noGuiAnswer": 2,
    "waitMinutes": 5
  },
  "outputs": [ { "name": "result", "type": "value" } ],
  "edges": [
    { "id": "8C9D0E1F-2A3B-4C4D-9E5F-6A7B8C9D0E02", "value": "true", "description": "Yes", "steps": [] },
    { "id": "8C9D0E1F-2A3B-4C4D-9E5F-6A7B8C9D0E03", "value": "false", "description": "No", "steps": [] }
  ]
}
```

(The `trigger_…` placeholder is illustrative.)

## Gotchas

- Without `noGuiAnswer` (and without `defaultYes`), any run without a user interface fails at this step. Set `noGuiAnswer` explicitly.
- `defaultYes` without `noGuiAnswer` silently becomes the background answer (legacy behaviour). This is probably not what you want.
- A waiting question holds a job queue session for up to `waitMinutes`. Keep the value small.
- Inside a loop, every pass asks again.
