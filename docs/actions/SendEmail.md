# Send Email

[← All actions](README.md)

Sends an HTML email through Business Central's standard email module, with optional attachments from AutoFlow Documents or inline base64 content.

| | |
|---|---|
| Enum name | `SendEmail` |
| Ordinal | `"action": 5564413` |
| Category | Web |
| Terminating | `false` |
| Group / edges | no |
| Availability | GA |

## What it does

Resolves recipients, subject, body and attachment fields, applies the AutoFlow test-mode redirect if it is active, checks every address, checks the sending account, builds the attachments, then sends with `Email.Send` from the configured account. The message GUID is returned as `sentEmailId`. The send runs in the flow's session. A failure from the email connector stops the step with the platform's error.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `accountId` | string (GUID) | yes | null GUID | Email account ID from the **Email Accounts** page, no braces. Environment-specific. |
| `accountConnector` | integer | yes | `0` | Ordinal of Business Central's `Email Connector` enum for that account. |
| `accountCaption` | string | no | `""` | Display text only (`Name (address)`), not read at run time. |
| `to` | string | yes | `""` | SmartText. Addresses separated by `;` or `,`. |
| `cc` | string | no | `""` | SmartText. Same format. |
| `bcc` | string | no | `""` | SmartText. Same format. |
| `subject` | string | yes (dialog) | `""` | SmartText. |
| `body` | string | no | `""` | HTML (rich text). SmartFields are resolved. Always sent as HTML. |
| `attachments` | array | no | `[]` | Rows `{ "type", "reference", "filename", "contentBase64" }`, described below. |

Attachment rows:

| key | used when | description |
|---|---|---|
| `type` | always | `"Reference"` (default; also used for empty or unknown values) or `"Inline"`. Case-insensitive at run time. |
| `reference` | Reference | `{{selector}}` to an AutoFlow Document reference (table 5564415). It can be a single reference, an array of references (each element is attached), an iterator over documents, or `{{name[N]}}` for one array element. Each document is attached with its `Name` (or `document_<ID>`) and `Content Type`. |
| `filename` | Inline | SmartText file name including extension. The content type is guessed from the extension (pdf, png, jpg/jpeg, gif, txt, html/htm, csv, xml, json, zip, xlsx, docx; otherwise `application/octet-stream`). |
| `contentBase64` | Inline | SmartText base64 content. |

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `sentEmailId` | value | – | Email message GUID (no braces). |

Reference it as `{{<slug>_sentEmailId}}`.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `to` and `subject` are required fields | (field marked required) |
| editor | error | Inline row without filename or content | Inline attachment is missing a filename or content. |
| editor | error | Reference row with empty selector | Attachment reference selector is empty. |
| editor | error | Selector not in `{{name}}` notation | Attachment reference selector '%1' must use the SmartField placeholder notation, e.g. '{{name}}'. |
| editor | error | Selector not among the outputs available at this step | Attachment reference selector "%1" was not found in the available outputs. |
| editor | error | Selector is a value, not a reference | Attachment reference selector "%1" must point at a record reference (or array of references). |
| editor | error | Selector points to a table other than AutoFlow Document | Attachment reference selector "%1" must point at a record from the AutoFlow Document table; got table %2. |

The attachment checks run when the dialog is saved and appear live in the dialog's status line. There is **no publish-time check** for this step, so a hand-written definition is only checked at run time.

## Runtime errors

| condition | message |
|---|---|
| to, cc and bcc all empty after resolution | At least one recipient (To, CC, or BCC) is required. |
| an address fails validation | Invalid email address: %1 |
| `accountId` empty, or account not registered for the connector | The configured email account is no longer registered or active. |
| referenced document deleted | Document record %1 referenced by selector "%2" no longer exists. |
| reference selector wrong type, table, notation or index | the corresponding editor message above |
| inline content not base64 | Inline attachment content is not valid base64-encoded data. |
| email connector fails | the platform's error |

## Example

```json
{
  "id": "C2E81F64-7D3A-4B95-A0E7-19F4B6C8D25A",
  "type": "action",
  "action": 5564413,
  "description": "Send Email",
  "slug": "SendInvoiceMail",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/mail.svg",
  "terminating": false,
  "configuration": {
    "accountId": "5D1A0B3C-8E2F-4A67-9B10-C4D5E6F70812",
    "accountConnector": 1,
    "accountCaption": "Billing (billing@example.com)",
    "to": "accounting@example.com",
    "cc": "",
    "bcc": "",
    "subject": "Your invoice",
    "body": "<p>Dear customer,</p><p>please find your invoice attached.</p>",
    "attachments": [
      { "type": "Reference", "reference": "{{CreateInvoicePdf_Document}}", "filename": "", "contentBase64": "" }
    ]
  },
  "outputs": [
    { "name": "sentEmailId", "type": "value" }
  ]
}
```

The account values above are placeholders. Use the ID and connector of a real account in the target environment.

## Gotchas

- `accountId` and `accountConnector` differ in every environment. After importing a flow, pick the account again or the step fails with "The configured email account is no longer registered or active."
- Reference attachments must point to **AutoFlow Document** records, such as Create PDF's `Document` output or Azure Blob: Get file's output. A reference to any other table (e.g. a Sales Invoice record) is rejected.
- Inline content is decoded to text before it is written, so binary files may not arrive byte-exact. Use a Reference row for PDFs and images.
- When AutoFlow test mode is active with test recipients, every email goes only to those test addresses, and CC/BCC are dropped.
- Subject and body are not checked at run time. An empty subject is sent as-is.
