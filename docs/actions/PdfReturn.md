# Return PDF

[← All actions](README.md)

Ends a "When a PDF is printed" flow and hands a base64-encoded PDF back to Business Central to replace the original document.

| | |
|---|---|
| Enum name | `PdfReturn` |
| Ordinal | `"action": 5564414` |
| Category | Trigger Responses |
| Terminating | `true` |
| Group / edges | no |
| Availability | GA. Offered in the step picker only for flows whose trigger is **When a PDF is printed** (`"trigger": 5564405`). |

## What it does

Reads `documentBase64` (SmartFields resolved), and signals the engine to stop the flow and return that text to the caller. The PDF-print trigger receives it, decodes the base64 and writes it as the document Business Central prints, previews, saves or sends. The flow runs synchronously inside the user's print request, so everything happens in one transaction that is committed when the trigger returns. If the flow finishes without reaching this step, or the value is empty, Business Central uses the original PDF.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `documentBase64` | string | yes | `""` | SmartText. The replacement PDF as base64, e.g. `{{trigger_DocumentStream}}` or the base64 output of an earlier step. |

## Outputs

None. This step ends the flow.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | info | Only shown in the step picker under the "When a PDF is printed" trigger | (picker filter, not enforced) |
| publish | warning | No step may follow it and it must not have edges | Step "%1" is a terminating step but has a successor – terminating steps must end the path. |

Nothing checks that `documentBase64` is filled in. If it is empty, or resolves to an empty string, Business Central silently keeps the original PDF.

**Trigger pairing is not enforced at publish.** The trigger restriction is only a step-picker filter. A hand-written or imported definition that uses this step under another trigger publishes without any warning.

## Runtime errors

| condition | message |
|---|---|
| used inside a SubFlow | Step %1 (%2) requested an HTTP yield, but it is running inside a SubFlow. Yield is only valid in the synchronous phase of a Webhook flow. |
| `documentBase64` is not valid base64 | the platform's base64 decode error, raised inside the print request |

## Example

```json
{
  "id": "0D9C4B7E-5A23-4F61-8E0B-7C1A2D3E4F50",
  "type": "action",
  "action": 5564414,
  "description": "Return PDF",
  "slug": "ReturnPdf",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/arrow-back-up.svg",
  "terminating": true,
  "configuration": {
    "documentBase64": "{{trigger_DocumentStream}}"
  },
  "outputs": []
}
```

In a real flow `documentBase64` would usually reference a modified PDF that an earlier step produced, for example a stamped or merged document from an HTTP call.

## Gotchas

- Put it **last** on its path. Steps after it never run, and publish shows a warning.
- Under other triggers: in a Webhook flow's synchronous phase it acts like a response (status 200, `application/pdf`, body = the base64 text); in a SubFlow it fails; in background flows nothing consumes the hand-back, so it only ends the path.
- Only one published flow can use the "When a PDF is printed" trigger, so put all PDF replacement logic into that one flow and branch on `{{trigger_ReportId}}`.
- If the trigger's timeout expires first, the original PDF is used.
