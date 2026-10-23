# Set File Name

[← All actions](README.md)

Ends a "When a report file name is generated" flow and hands the resolved text back to Business Central as the report's output file name.

| | |
|---|---|
| Enum name | `SetReportFileName` |
| Ordinal | `"action": 5564416` |
| Category | Trigger Responses |
| Terminating | `true` |
| Group / edges | no |
| Availability | GA. Offered in the step picker only for flows whose trigger is **When a report file name is generated** (`"trigger": 5564406`). |

## What it does

Resolves `fileName` (SmartFields, SmartFormulas, SmartControls) and signals the engine to stop the flow and return the text to the caller. The file-name trigger then uses it as the file name for Send to… / Save / Download and for the Word-layout email path. The flow runs synchronously inside the user's request and is committed when the trigger returns. If the resolved name is empty, or the flow finishes without reaching this step, Business Central keeps its own name.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `fileName` | string | yes | `""` | SmartText. Full file name **including extension**, e.g. `Invoice_{{trigger_ProposedFileName}}` or `Order [[...]].pdf`. |

## Outputs

None. This step ends the flow.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `fileName` must not be empty | (no text; required field / step reported invalid) |
| editor | info | Only shown in the step picker under the "When a report file name is generated" trigger | (picker filter, not enforced) |
| publish | warning | No step may follow it and it must not have edges | Step "%1" is a terminating step but has a successor – terminating steps must end the path. |

**Trigger pairing is not enforced at publish.** The restriction is only a step-picker filter.

## Runtime errors

| condition | message |
|---|---|
| used inside a SubFlow | Step %1 (%2) requested an HTTP yield, but it is running inside a SubFlow. Yield is only valid in the synchronous phase of a Webhook flow. |

## Example

```json
{
  "id": "A47E2C19-3B5D-4F80-91C6-5E2F8A0B7D34",
  "type": "action",
  "action": 5564416,
  "description": "Set File Name",
  "slug": "SetFileName",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/file-pencil.svg",
  "terminating": true,
  "configuration": {
    "fileName": "Sales Invoice {{trigger_ProposedFileName}}"
  },
  "outputs": []
}
```

## Gotchas

- Add the extension yourself. `{{trigger_Extension}}` holds the original one, and `{{trigger_ProposedFileName}}` is the name Business Central proposed.
- Put it **last** on its path. Publish warns if anything follows it.
- Under other triggers: in a Webhook flow's synchronous phase it acts like a response (status 200, `text/plain`); in a SubFlow it fails; in background flows nothing consumes the hand-back.
- Business Central removes characters that are not allowed in file names after the hand-back, so you don't need to sanitise the name.
