# Run Codeunit / Report

[← All actions](README.md)

Runs any AL codeunit or processing-only report by ID, optionally on a record from the flow.

| | |
|---|---|
| Enum name | `RunCodeunit` |
| Ordinal | `"action": 5564415` |
| Category | Utilities |
| Terminating | `false` |
| Group / edges | No |
| Availability | GA |

## What it does

The step runs the codeunit or report in a **separate background session** and waits for it to finish. It polls every 200 ms, for up to 10 minutes.

1. Before it starts the session, the step **commits** the flow's open transaction. It does this in every kind of flow, including SubFlows and interactive or synchronous flows.
2. The object runs in its own transaction, so its changes are committed independently of the flow. A later failure of the flow does not roll them back.
3. How the object is called:
   - **Codeunit**: `OnRun` runs with the record when `sourceRecordSelector` is set, otherwise without one.
   - **Report**: the report runs with the saved request-page parameters, never shows a request page, and discards its rendered output. Only the side effects count.
4. If the object raises an error, the step fails with that error message.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `objectType` | string | no | `"Codeunit"` | `"Codeunit"` or `"Report"` (exact case). Empty means Codeunit. |
| `objectId` | integer | yes | `0` | ID of the codeunit or report. Must be a JSON number. |
| `objectCaption` | string | no | `""` | Caption of the object, written by the editor. Display only; not read at run time. |
| `sourceRecordSelector` | string | no | `""` | Optional record to pass: a wrapped, flat Reference SmartField such as `{{trigger_Rec}}`. For a codeunit, its `TableNo` must match the record's table. For a report, the record is the report's data record. |
| `reportParameters` | string | no | `""` | Request-page parameters as XML, in the format BC saves for report requests. SmartFields inside the XML are resolved first. Used only for reports. When empty, an empty `<ReportParameters />` envelope is used. |

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `success` | value | – | Always `true` when the step completes. Failures raise an error instead. |

Reference it downstream as `{{<slug>_success}}`.

## Validation

The editor runs these checks when you confirm the dialog and refuses to save an invalid configuration. Core does **not** repeat them at publish, so an imported definition is not checked until the step is opened.

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `objectId` is 0 or missing | Codeunit is required. / Report is required. |
| editor | error | `objectType` is not `Codeunit` or `Report` | Unknown objectType: %1. Expected Codeunit or Report. |
| editor + runtime | error | Codeunit is on the block-list: 1, 2, 40, 357, 358 (extensions may add more) | Codeunit %1: %2 (at run time: This codeunit is blocked for AutoFlow. %1) |
| editor | error | Codeunit does not exist | Codeunit %1 does not exist. |
| editor | error | Codeunit subtype is not Normal | Codeunit %1 (%2) has subtype %3; only Normal codeunits are allowed. |
| editor | error | Report does not exist | Report %1 does not exist. |
| editor + runtime | error | Selector is not a wrapped `{{...}}` placeholder | Source record reference must be a wrapped SmartField placeholder, e.g. {{customer}}. Got: %1 |
| editor | error | Selector cannot be resolved | Source record reference %1 cannot be resolved to a known field. |
| editor | error | Selector points at a Value, not a Reference | Source record reference %1 must point at a Reference-typed field, not a Value. |
| editor (status line) | error | No object picked | Select a codeunit to run. / Select a report to run. |

The block-list reasons are:

- **Codeunit 1**: legacy system bootstrap.
- **Codeunit 2**: Company-Initialize.
- **Codeunit 40**: LogInManagement.
- **Codeunits 357 and 358**: date compression.

## Runtime errors

| condition | message |
|---|---|
| The selector is not a Reference at run time | Source record reference '%1' could not be resolved at runtime. |
| The record was deleted before the session started | Source record %1 in table %2 could not be found. (Reported inside the codeunit or report failure message.) |
| The codeunit failed | Codeunit %1 failed: %2 |
| The codeunit failed without a message | Codeunit %1 failed without a usable error message. Try invoking the same operation manually from the BC UI to see the underlying validation error. |
| The report failed | Report %1 failed: %2 |
| The report failed without a message | Report %1 failed without a usable error message. Try invoking the same report manually from the BC UI to see the underlying validation error. |
| The 10-minute limit was exceeded | Codeunit/report did not complete within %1 seconds. Job %2 is still Pending. |

Error texts are truncated to 1024 characters.

## Example

```json
{
  "id": "C81E728D-9D4C-4F3B-A2E1-5D7E6B0F1A42",
  "type": "action",
  "action": 5564415,
  "description": "Run Sales-Post",
  "slug": "RunSalesPost",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/run-codeunit.svg",
  "terminating": false,
  "configuration": {
    "objectType": "Codeunit",
    "objectId": 80,
    "objectCaption": "Sales-Post",
    "sourceRecordSelector": "{{trigger_Rec}}",
    "reportParameters": ""
  },
  "outputs": [
    { "name": "success", "type": "value" }
  ]
}
```

## Gotchas

- The commit before the run breaks "all or nothing" behaviour. Work done by earlier steps stays committed even if a later step fails.
- The codeunit runs in a background session. It cannot show UI, and `Confirm` or `Page.Run` in it fail.
- Object IDs differ between extensions and environments. Make sure the object exists in the target environment.
- The subtype and existence checks only run in the editor. A test codeunit imported via JSON is not stopped at run time.
