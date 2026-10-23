# Azure Blob: Get file

[← All actions](README.md)

Downloads one file from Azure Blob Storage into the AutoFlow document library and outputs a document reference plus the file's properties.

| | |
|---|---|
| Enum name | `AzureBlobGet` |
| Ordinal | `"action": 5564421` |
| Category | Documents |
| Terminating | `false` |
| Group / edges | No |
| Availability | GA |

## What it does

The step downloads the blob at `path` and stores its bytes as a new **AutoFlow Document** (table 5564415). You can use that document as an e-mail attachment or as the content of an Azure Blob: Upload file step.

It then reads the file's properties (content type, last-modified time, ETag, tags and metadata) through a one-entry listing of the exact path:

- If `includeTags` is **off** and that listing fails (for example with a read-only SAS token), the step still succeeds. The content type then comes from the file extension.
- If the file is missing and `errorIfMissing` is off, the step succeeds with `found = false`.

The connection settings (`credentialCode`, `storageAccount`, `container`), the credential rules and the cross-environment notes are the same as for [Azure Blob: List files](AzureBlobList.md#connection-shared-by-all-three-azure-blob-steps).

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `credentialCode` | string (≤ 20) | yes | `""` | AutoFlow Credential code. The credential must use OAuth 2.0 client credentials (scope `https://storage.azure.com/.default`) or an Azure Storage SAS token. |
| `storageAccount` | string | yes | `""` | Storage account name (3–24 characters, `a-z0-9`). Supports SmartText. |
| `container` | string | yes | `""` | Container name. Supports SmartText. |
| `path` | string | yes | `""` | File path inside the container, e.g. `invoices/2026/INV-1001.pdf`. The value is trimmed, `\` becomes `/`, and a leading `/` is removed. It must not end with `/`. Supports SmartText. |
| `includeTags` | boolean | no | `true` | Also reads the file's index tags. This needs Storage Blob Data Owner, or a SAS token with the Tags permission. When on, failing to read the properties is an error. |
| `errorIfMissing` | boolean | no | `true` | Fails the step when the file does not exist. When off, a missing file (Azure `BlobNotFound`) gives `found = false`; other Azure errors still fail. |

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `found` | value | – | `true` / `false`. This is the only value written when the file is missing and `errorIfMissing` is off; the other outputs then stay unresolved. |
| `Document` | reference | 5564415 | The new AutoFlow Document. |
| `name` | value | – | File name, the last path segment. |
| `path` | value | – | Normalized path. |
| `contentType` | value | – | The blob's content type, or one derived from the extension: `pdf`, `xml`, `json`, `txt`, `csv`, `htm`/`html`, `png`, `jpg`/`jpeg`, `gif`, `zip`, `docx`, `xlsx`, otherwise `application/octet-stream`. |
| `size` | value | – | Size in bytes. |
| `lastModified` | value | – | ISO-8601 date and time, or empty. |
| `etag` | value | – | The blob's ETag. |
| `tags` | value | – | Index tags as a JSON object string (`{}` when there are none). |
| `metadata` | value | – | Blob metadata as a JSON object string (`{}` when there is none). |

Reference the outputs downstream, e.g. `{{GetInvoice_Document}}` or `{{GetInvoice_found}}`.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `credentialCode`, `storageAccount`, `container` and `path` are required fields | Please fill in the highlighted fields. |
| editor status line | warning | Credential problems and the base-URL allow-list, as for List files. Advisory only. | See [Azure Blob: List files](AzureBlobList.md#validation) |
| runtime | error | Credential empty, missing or of a wrong type; invalid storage account or container (resolved values) | See [Azure Blob: List files](AzureBlobList.md#validation) |
| runtime | error | `path` empty after resolving and normalizing | Enter the path of the file, for example invoices/2026/INV-1001.pdf. |
| runtime | error | `path` ends with `/` | The path "%1" ends with a slash, so it names a folder. Enter the path of a file. |
| runtime | error | Endpoint is not covered by the credential's base URLs | The URL "%1" is not allowed by credential "%2". Allowed prefixes: %3. |

No publish-time check exists for this step.

## Runtime errors

- The file %1 was not found in container %2 of storage account %3. (Only with `errorIfMissing = true`.)
- Credential %1 has no SAS token stored.
- The other Azure error translations are the same as for List files. Unknown errors become `Downloading the file failed: <Azure error text>`.

## Example

```json
{
  "id": "A3F09C12-5B7D-4E21-8D44-7C6B5A493E20",
  "type": "action",
  "action": 5564421,
  "description": "Get invoice PDF",
  "slug": "GetInvoice",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/cloud-download.svg",
  "terminating": false,
  "configuration": {
    "credentialCode": "AZSTORAGE",
    "storageAccount": "contosodocs",
    "container": "invoices",
    "path": "inbox/INV-1001.pdf",
    "includeTags": false,
    "errorIfMissing": false
  },
  "outputs": [
    { "name": "found", "type": "value" },
    { "name": "Document", "type": "reference", "tableNo": 5564415 },
    { "name": "name", "type": "value" },
    { "name": "path", "type": "value" },
    { "name": "contentType", "type": "value" },
    { "name": "size", "type": "value" },
    { "name": "lastModified", "type": "value" },
    { "name": "etag", "type": "value" },
    { "name": "tags", "type": "value" },
    { "name": "metadata", "type": "value" }
  ]
}
```

## Gotchas

- Downloading needs Storage Blob Data Reader. `includeTags` (on by default) also needs Storage Blob Data Owner. With a read-only SAS token, turn `includeTags` off.
- Inside a For Each over List files results, bind `path` to the row's `Path` field.
- Every run creates a new AutoFlow Document record.
