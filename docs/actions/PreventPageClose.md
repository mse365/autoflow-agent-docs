# Prevent page close

[← All actions](README.md)

Keeps the page open instead of letting it close, and can tell the user why.

| | |
|---|---|
| Enum name | `PreventPageClose` |
| Ordinal | `"action": 5564419` |
| Category | Trigger Responses |
| Terminating | `false` (flag in JSON), but it ends the flow in practice, see below |
| Group / edges | No |
| Availability | GA. Only offered in flows whose trigger is **When a page is closed (interactive)** (`"trigger": 5564408`). |

## What it does

The "page is closed" trigger runs synchronously in the user's session before the page actually closes. When the flow reaches this step, the step hands a "keep the page open" answer back to the page, and the flow ends: steps after it do not run. If `showMessage` is true, the resolved `message` is shown either as a dialog the user must acknowledge (`asDialog: true`) or as a notification on the page that stayed open (`asDialog: false`). If `showMessage` is false, the page simply stays open.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `showMessage` | boolean | no | `true` | Tell the user why the page stays open. |
| `asDialog` | boolean | no | `true` | `true` = dialog, `false` = notification bar on the page. Only used when `showMessage` is true. |
| `message` | string | when `showMessage` is true | `""` | What the user is told. Say what to change, not just that something is wrong. Supports SmartFields `{{..}}`, SmartFormulas `[[..]]` and SmartControls `{#..#}`. Cut to 2048 characters. |

**Translatable** ([translations](../flow-definition.md#translations)): `message`.

## Outputs

None.

## Validation

No check is enforced. The step picker hides this step unless the flow's trigger is the page-close trigger, and no publish check enforces this either.

The step has a check for an empty message (`Enter the message to show, or turn off "Tell the user why".`), but 27.0.40 runs it neither in the editor nor at publish. An empty message with `showMessage` true keeps the page open without telling the user why, so always write one.

## Runtime errors

None from the step itself.

## Example

Typically placed in a Decision branch in a page-close flow:

```json
{
  "id": "3B4C5D6E-7F80-4192-A3B4-C5D6E7F80901",
  "type": "action",
  "action": 5564419,
  "description": "Prevent page close",
  "slug": "PreventPageClose",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/hand-stop.svg",
  "terminating": false,
  "configuration": {
    "showMessage": true,
    "asDialog": false,
    "message": "Please enter an External Document No. before closing the order."
  },
  "outputs": []
}
```

## Gotchas

- Treat it as the last step of its path. The JSON flag is `terminating: false`, so publishing does **not** warn about steps placed after it, but those steps never run.
- `showMessage` defaults to `true`. If you omit it, provide `message`, or the page stays open silently.
- Use it only in flows with trigger `5564408` ("When a page is closed (interactive)").
