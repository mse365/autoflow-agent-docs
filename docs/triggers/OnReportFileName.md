# When a report file name is generated

[← All triggers](README.md)

Runs synchronously whenever Business Central assigns a file name to an output of one of the configured reports. The flow can replace the name with a **Set report file name** step.

| | |
|---|---|
| Enum name | `OnReportFileName` |
| Ordinal | `"trigger": 5564406` |
| Category | Reports |
| Terminating | n/a (trigger) |
| Group / edges | no |
| Availability | GA. **Only one published flow per environment** may use this trigger. |

## What it does

Hooks both file-name paths of Business Central. The first is the platform path: Send to…, and Save or Download from a request page. The second is the legacy custom-layout path: Word-layout email and SaveAs. Any file type triggers the flow (PDF, Word, Excel, …), but only for reports listed in `reports`. The flow runs **inside the user's request** until a Set report file name step answers, the flow ends or fails, or `timeoutSec` has passed. Without an answer Business Central keeps its own name. If the flow itself renders a report, that nested event does not start the flow again.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `reports` | array | yes | `[]` | `[{ "reportId": 1306, "tableNo": 112 }, ...]`. `tableNo` (optional, `0` = none) is the report's source table. With it, the printed records become available as `Rec_<reportId>`. List each report once. |
| `timeoutSec` | integer | no | `30` | Seconds the flow may run. Checked between steps: once it has passed, the remaining steps don't run and Business Central keeps its name. `0` or less means no limit. |

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `ProposedFileName` | value | – | The name Business Central generated. |
| `ReportId` | value | – | For example `1306`. |
| `Extension` | value | – | As passed by Business Central. |
| `RecordCount` | value | – | Number of records the output covers (true total), `0` without a source record. |
| `Rec_<reportId>` | reference | `reports[].tableNo` | One per line with `tableNo` > 0, in line order. Points at the first matched record. `Rec_<reportId>[0]`, `[1]`, … (up to 1000) hold every matched record at run time and can be walked with For Each. They are not listed in `outputs`. |

Reference them as `{{trigger_ProposedFileName}}`, `{{trigger_Rec_1306}}` and so on.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| publish | error | at least one report line | The "When a report file name is generated" trigger requires at least one report line. |
| publish | error | no other published flow uses this trigger | Only one published flow can use the "When a report file name is generated" trigger. It is already used by flow '%1'. |

Both are raised while the trigger is registered, after the licensing call, and undo the whole publish. The trigger also has checks for the timeout, unknown reports or tables and duplicate lines, but 27.0.40 runs none of them. Use existing report and table numbers anyway: a line for a report that doesn't exist never fires.

## Runtime errors

| condition | effect / message |
|---|---|
| flow fails | The execution is marked Error with the log "Report file-name flow failed before any body step could complete: %1". Business Central keeps its name and the download does not fail. |
| a Sleep step runs | The flow fails as above: "Step %1 (%2) requested a deferred resume, but the flow is running synchronously. …" |
| the flow's published version can't be loaded | "Failed to resolve trigger context for Report ID %1 (flow %2)." The report output fails. |

## Example

```json
{
  "id": "8C9D0E1F-2A3B-4C4D-9E5F-6A7B8C9D0E1F",
  "type": "trigger",
  "trigger": 5564406,
  "description": "When a report file name is generated",
  "slug": "trigger",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/file-text.svg",
  "configuration": {
    "reports": [
      { "reportId": 1306, "tableNo": 112 }
    ],
    "timeoutSec": 30
  },
  "outputs": [
    { "name": "ProposedFileName", "type": "value" },
    { "name": "ReportId", "type": "value" },
    { "name": "Extension", "type": "value" },
    { "name": "RecordCount", "type": "value" },
    { "name": "Rec_1306", "type": "reference", "tableNo": 112 }
  ],
  "level": 0
}
```

## Gotchas

- One flow handles every configured report. Branch on `{{trigger_ReportId}}`.
- **Set report file name** is only offered here.
- Business Central removes characters that are not allowed in file names after the flow returns.
- In a batch run, `RecordCount` can be larger than 1000 while only 1000 references are emitted.
- Matched records come from the report's request-page filter on the platform path. On the legacy custom-layout path only the single record Business Central passes is used.
