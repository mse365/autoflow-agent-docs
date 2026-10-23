# Create PDF

[← All actions](README.md)

Renders a Business Central report to PDF and stores the result as an AutoFlow Document that later steps can attach, upload or return.

| | |
|---|---|
| Enum name | `PdfPrint` |
| Ordinal | `"action": 5564410` |
| Category | Documents |
| Terminating | `false` |
| Group / edges | no |
| Availability | GA (layout lookup in the editor needs Business Central 26 or later; see Gotchas) |

## What it does

Runs the configured report with `Report.SaveAs(..., Pdf, ...)`. If a record selector is set, the report runs filtered to exactly that record; without one the report runs on its own request-page parameters only (useful for financial reports). An optional layout is applied for this one render and cleared afterwards, even when the render fails. The PDF is inserted into the AutoFlow Document table (content type `application/pdf`) and a reference to that row is published as the `Document` output.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `selector` | string | no | `""` | Record selector in `{{name}}` notation pointing to a record **reference** (e.g. `{{trigger_Rec}}`). Empty = report without a data-source record. Bare names are rejected. |
| `report` | string | yes | `""` | Report object ID as a decimal string, e.g. `"1306"`. |
| `parameters` | string | no | `""` | Request-page parameters as XML. SmartFields (`{{...}}`) inside the XML are resolved at run time. Values that do not start with `<` are treated as legacy base64 and decoded. |
| `layout` | string | no | `""` | Layout name for the selected report. Empty = report default layout. |
| `layoutAppId` | string (GUID) | no | `""` | GUID (no braces) of the app owning the layout; disambiguates same-named layouts. The editor recomputes it on every save. |
| `filenamePattern` | string | no | `""` | SmartText file name. Tokens `{ReportName}`, `{RecordNo}`, `{ReportId}` are replaced. Include `.pdf` yourself. Empty = `Report_<id>.pdf`. |

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `Document` | reference | 5564415 | The AutoFlow Document record (fields: ID, Name, Content Type, Length, Data). |

Reference it as `{{<slug>_Document}}`, e.g. `{{CreateInvoicePdf_Document}}`.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | Report is a required field in the dialog | Please fill in the highlighted fields. |

There is no publish-time check for this step. Everything else, including the selector format, is only checked at run time.

## Runtime errors

| condition | message |
|---|---|
| `report` empty | A report must be selected. |
| `report` not an integer | Invalid Report ID: %1. Report ID must be a valid integer. |
| report does not exist | Report ID %1 does not exist. |
| layout name (and app) not found for the report | The layout '%1' no longer exists for report %2. Open the PDF Print step and pick a layout again, or clear it to use the report default. |
| selector without braces | The selector '%1' must use the SmartField placeholder notation (e.g. '{{name}}'). Bare selector names are no longer accepted – open the SmartField picker on the PDF Print step config to insert a valid placeholder. |
| selector not in context | Record selector '%1' could not be resolved. The selector was not found in the context buffer. |
| selector is a value, not a reference | Record selector '%1' could not be resolved to a record reference. The field is not a reference type. |
| referenced record deleted | The record referenced by selector '%1' could not be found. |
| render failed | the platform's error text, or: The report %1 could not be rendered. |
| empty PDF | The report %1 produced an empty PDF document. |

## Example

```json
{
  "id": "6B0F3A52-1C7E-4E8D-9A41-2F5C7D9E0B13",
  "type": "action",
  "action": 5564410,
  "description": "Create Sales Invoice PDF",
  "slug": "CreateInvoicePdf",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/file-type-pdf.svg",
  "terminating": false,
  "configuration": {
    "selector": "{{trigger_Rec}}",
    "report": "1306",
    "parameters": "",
    "layout": "",
    "layoutAppId": "",
    "filenamePattern": "Invoice_{RecordNo}.pdf"
  },
  "outputs": [
    { "name": "Document", "type": "reference", "tableNo": 5564415 }
  ]
}
```

## Gotchas

- `report` is a **string** holding the number (`"1306"`), as the editor writes it.
- `{RecordNo}` is the record's primary-key values joined with `_`; it is empty when no selector is set.
- The selector must resolve to a record reference (e.g. a trigger's `Rec` output or a Find Records result), not a text value.
- If you edit `layout` by hand, clear or update `layoutAppId` as well; a stale app id makes the layout lookup fail at run time. The editor re-derives `layoutAppId` from the report and layout name on every save.
- On Business Central 24 the editor's layout picker has no lookup, so the layout can only be set by editing the JSON.
- The generated document stays in the AutoFlow Document table; it is the hand-off format for Send Email attachments and Azure Blob uploads.
