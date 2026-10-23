# Azure Blob: Upload file

[← All actions](README.md)

Uploads a document, binary data or text to a path in Azure Blob Storage, with optional index tags.

| | |
|---|---|
| Enum name | `AzureBlobPut` |
| Ordinal | `"action": 5564422` |
| Category | Documents |
| Terminating | `false` |
| Group / edges | No |
| Availability | GA |

## What it does

The step resolves `content` and writes it as a block blob to `path`, with `contentType` and the optional index tags, in a single request. The data source depends on the **raw** `content` value:

- **Exactly one SmartField that names an AutoFlow Document** (e.g. the `Document` output of a PDF step): that document's bytes are uploaded, and its stored content type is used.
- **Exactly one SmartField that names another binary source** (a BLOB or Media field, a binary step output): those bytes are uploaded byte for byte.
- **Anything else**: the value is resolved as SmartText and uploaded as UTF-8 text.

When `overwrite` is off, the step first checks whether a blob with exactly this path exists, and fails if so.

The connection settings, credential rules and cross-environment notes are the same as for [Azure Blob: List files](AzureBlobList.md#connection-shared-by-all-three-azure-blob-steps).

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `credentialCode` | string (≤ 20) | yes | `""` | AutoFlow Credential code. The credential must use OAuth 2.0 client credentials (scope `https://storage.azure.com/.default`) or an Azure Storage SAS token. |
| `storageAccount` | string | yes | `""` | Storage account name (3–24 characters, `a-z0-9`). Supports SmartText. |
| `container` | string | yes | `""` | Container name. Supports SmartText. |
| `path` | string | yes | `""` | Target path, e.g. `invoices/2026/{{trigger_Rec.no}}.pdf`. Folders are implicit. The value is trimmed, `\` becomes `/`, and a leading `/` is removed. It must not end with `/`. Supports SmartText. |
| `content` | string | yes | `""` | What to upload (see above). Supports SmartText and binary SmartFields. |
| `contentType` | string | no | `""` | MIME type, e.g. `application/pdf`. When empty, the source document's type is used, otherwise a type derived from the extension of `path`. Supports SmartText. |
| `overwrite` | boolean | no | `true` | Replaces an existing blob. When `false`, an existing blob makes the step fail. |
| `tags` | array | no | `[]` | Index tags: `[{"name": "status", "value": "new"}]`. At most 10 tags. `value` supports SmartText. |

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `path` | value | – | Normalized path. |
| `name` | value | – | File name, the last path segment. |
| `url` | value | – | `https://<account>.blob.core.windows.net/<container>/<path>`, without a SAS token. |
| `size` | value | – | Number of bytes uploaded. |
| `contentType` | value | – | The content type actually stored. |

Reference the outputs downstream, e.g. `{{UploadInvoice_url}}`.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `credentialCode` empty | Select a credential for the Azure Blob Storage connection. |
| editor + runtime | error | Credential missing or of a wrong type, OAuth scope is not Azure Storage, invalid account or container | See [Azure Blob: List files](AzureBlobList.md#validation) |
| editor + runtime | error | `path` empty | Enter the path of the file, for example invoices/2026/INV-1001.pdf. |
| editor + runtime | error | `path` ends with `/` | The path "%1" ends with a slash, so it names a folder. Enter the path of a file. |
| editor + runtime | error | More than 10 tags | A file can have at most 10 index tags; %1 are configured. |
| editor + runtime | error | Duplicate tag name | The index tag "%1" is configured more than once. |
| editor + runtime | error | Tag name is not 1–128 characters | The index tag name "%1" is not valid. It must be 1 to 128 characters long. |
| editor (literal) / runtime (resolved) | error | Tag value is longer than 256 characters | The value of index tag "%1" is too long. Tag values can have at most 256 characters. |
| editor (literal) / runtime (resolved) | error | Tag name or value contains a character other than ASCII letters, digits, space and `+ - . / : = _` | The index tag "%1" contains the character "%2". Tag names and values may only contain letters, digits, spaces and the characters + - . / : = _ |
| editor status line + runtime | error | Endpoint is not covered by the credential's base URLs | The URL "%1" is not allowed by credential "%2". Allowed prefixes: %3. |

No publish-time check exists for this step.

## Runtime errors

- The content of the file is empty. Check the Content field – a SmartField there may not have resolved.
- The file %1 already exists in container %2. Turn on "Overwrite existing file" to replace it.
- Credential %1 has no SAS token stored.
- Azure errors are translated as for List files. Unknown errors become `Uploading the file failed: <Azure error text>`.

## Example

```json
{
  "id": "0E7B4D29-3C61-4A8F-B2D7-91F5C0A6E834",
  "type": "action",
  "action": 5564422,
  "description": "Upload invoice PDF",
  "slug": "UploadInvoice",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/cloud-upload.svg",
  "terminating": false,
  "configuration": {
    "credentialCode": "AZSTORAGE",
    "storageAccount": "contosodocs",
    "container": "invoices",
    "path": "archive/2026/{{trigger_Rec.no}}.pdf",
    "content": "{{CreatePdf_Document}}",
    "contentType": "",
    "overwrite": true,
    "tags": [
      { "name": "customer", "value": "{{trigger_Rec.selltocustomerno}}" },
      { "name": "status", "value": "archived" }
    ]
  },
  "outputs": [
    { "name": "path", "type": "value" },
    { "name": "name", "type": "value" },
    { "name": "url", "type": "value" },
    { "name": "size", "type": "value" },
    { "name": "contentType", "type": "value" }
  ]
}
```

(`trigger_*` and `CreatePdf_Document` stand for outputs of earlier steps in your flow.)

## Gotchas

- Put **only** the SmartField in `content` when you want binary data. `report: {{CreatePdf_Document}}` is treated as text.
- Uploading needs Storage Blob Data Contributor. Writing tags needs Storage Blob Data Owner (or a SAS token with the Tags permission). With `overwrite = false`, the step also needs list permission.
- Tag values resolved from SmartFields can contain characters that are not allowed (umlauts, `&`, `,`, …). The step then fails at run time.
