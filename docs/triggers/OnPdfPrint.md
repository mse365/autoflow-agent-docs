# When a PDF is printed

[← All triggers](README.md)

Runs synchronously whenever Business Central produces a PDF for one of the configured reports. The flow can replace the document with a **Return PDF** step.

| | |
|---|---|
| Enum name | `OnPdfPrint` |
| Ordinal | `"trigger": 5564405` |
| Category | Reports |
| Terminating | n/a (trigger) |
| Group / edges | no |
| Availability | GA. **Only one published flow per environment** may use this trigger. |

## What it does

Hooks Business Central's "document ready" report event for every intent: Print, Preview, Save, Download and Schedule. Only `application/pdf` documents of reports listed in `reports` start the flow. If another extension has already supplied the document, the flow does not run. The flow runs **inside the user's report request** until it reaches Return PDF, ends, fails or exceeds `timeoutSec` (checked between steps). Its step state is committed once at the end. Nothing continues in the background afterwards. Without a Return PDF, or after a failure or a timeout, Business Central uses the original PDF. A failure rolls back the flow's database changes.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `reports` | array | yes | `[]` | `[{ "reportId": 1306 }, ...]`. At least one entry (checked at publish). List each report once. |
| `timeoutSec` | integer | no | `30` | Maximum run time before the original PDF is used, checked between steps. `0` or less means no limit, so keep it ≥ 1. |

The config canvas also shows a "Source Table" column, but this trigger does not store it.

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `ObjectPayload` | value | – | The full report payload JSON from Business Central, as text. |
| `DocumentStream` | value | – | The original PDF, base64. It is deleted from the execution after the run. |
| `ReportId` | value | – | For example `1306`. |
| `DocumentType` | value | – | Always `application/pdf`. |
| `LayoutName` | value | – | Layout used, `""` if unknown. |
| `Intent` | value | – | `Print`, `Preview`, `Save`, `Download`, `Schedule`, … |

Reference them as `{{trigger_ReportId}}`, `{{trigger_DocumentStream}}` and so on.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| publish | error | at least one report line | The "When a PDF is printed" trigger requires at least one report line. |
| publish | error | no other published flow uses this trigger | Only one published flow can use the "When a PDF is printed" trigger. It is already used by flow '%1'. |

Nothing else is checked. A line for a report that does not exist never matches, and a `timeoutSec` of 0 or less removes the time limit.

## Runtime errors

| condition | effect / message |
|---|---|
| flow fails | The execution is marked Error with the log "PDF Print flow failed before any body step could complete: %1". The user gets the original PDF and the print does not fail. |
| a Sleep step runs | Step %1 (%2) requested a deferred resume, but the flow is running synchronously. Use Sleep or other time-based deferral steps only outside of synchronous frames (Webhook sync phase or SubFlow body). |

## Example

```json
{
  "id": "7B8C9D0E-1F2A-4B3C-8D4E-5F6A7B8C9D0E",
  "type": "trigger",
  "trigger": 5564405,
  "description": "When a PDF is printed",
  "slug": "trigger",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/file-type-pdf-trigger.svg",
  "configuration": {
    "reports": [
      { "reportId": 1306 },
      { "reportId": 1322 }
    ],
    "timeoutSec": 30
  },
  "outputs": [
    { "name": "ObjectPayload", "type": "value" },
    { "name": "DocumentStream", "type": "value" },
    { "name": "ReportId", "type": "value" },
    { "name": "DocumentType", "type": "value" },
    { "name": "LayoutName", "type": "value" },
    { "name": "Intent", "type": "value" }
  ],
  "level": 0
}
```

## Gotchas

- One flow handles every configured report. Branch on `{{trigger_ReportId}}`.
- **Return PDF** is only offered here. Respond to Webhook, Return SubFlow Output, Set report file name, Set document field values and Prevent page close are hidden.
- Keep the flow fast. The user waits on the print.
- The older single `reportId` key is no longer read. Use `reports`.
