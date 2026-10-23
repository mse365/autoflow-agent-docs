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

Hooks both file-name paths of Business Central. The first is the platform path: Send to…, and Save or Download from a request page. The second is the legacy custom-layout path: Word-layout email and SaveAs. Any file type triggers the flow (PDF, Word, Excel, …), but only for reports listed in `reports`. The flow runs **inside the user's request** until Set report file name yields, the flow ends, it fails or `timeoutSec` passes. Its step state is committed once at the end. Without a yield Business Central keeps its own name. If the flow itself renders a report, that nested event does not start the flow again.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `reports` | array | yes | `[]` | `[{ "reportId": 1306, "tableNo": 112 }, ...]`. `tableNo` (optional, `0` = none) is the report's source table. With it, the printed records become available as `Rec_<reportId>`. |
| `timeoutSec` | integer | no | `30` | Maximum run time before the generated name is kept. Must be ≥ 1. |

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `ProposedFileName` | value | – | The name Business Central generated. |
| `ReportId` | value | – | For example `1306`. |
| `Extension` | value | – | As passed by Business Central. |
| `RecordCount` | value | – | Number of records the output covers (true total), `0` without a source record. |
| `Rec_<reportId>` | reference | `reports[].tableNo` | Only for lines with `tableNo` > 0. Points at the first matched record. `Rec_<reportId>[0]`, `[1]`, … (up to 1000) hold every matched record at run time and can be walked with For Each. They are not listed in `outputs`. |

Reference them as `{{trigger_ProposedFileName}}`, `{{trigger_Rec_1306}}` and so on.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| publish | error | at least one report line | The "When a report file name is generated" trigger requires at least one report line. |
| publish | error | no other published flow uses this trigger | Only one published flow can use the "When a report file name is generated" trigger. It is already used by flow '%1'. |
| editor | error | at least one line | Configure at least one report line. |
| editor | error | `timeoutSec` ≥ 1 | The timeout must be at least 1 second. |
| editor | error | report exists | Report %1 does not exist. |
| editor | error | table exists (when set) | Table %1 (line for report %2) does not exist. |
| editor | error | report listed once | Report %1 is configured on more than one line. |

## Runtime errors

| condition | effect / message |
|---|---|
| flow fails | The execution is marked Error with the log "Report file-name flow failed before any body step could complete: %1". Business Central keeps its name and the download does not fail. |

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
