# Azure Blob: List files

[← All actions](README.md)

Lists the files in an Azure Blob Storage container. You can limit the list to one folder level and filter it by index tags.

| | |
|---|---|
| Enum name | `AzureBlobList` |
| Ordinal | `"action": 5564420` |
| Category | Documents |
| Terminating | `false` |
| Group / edges | No |
| Availability | GA |

## What it does

The step signs in to Azure with an AutoFlow Credential and lists the blobs under `path`. It follows Azure's continuation markers until it has all results or reaches `maxResults`. Each file is stored as an **Azure Blob Entry** row (table 5564412), and the step outputs the count plus a reference collection over those rows, which you can loop with For Each. If `tagFilters` is set, the step runs Azure's *find blobs by tags* query instead. That query spans the whole **storage account**. The step then keeps only the hits in the configured container and under `path` (and directly inside it when `folderLevelOnly` is on).

The rows belong to the top-level execution, also when the step runs inside a SubFlow. They are deleted when that execution succeeds or is deleted. A failed execution keeps them, so a restart can reuse them.

### Connection (shared by all three Azure Blob steps)

- `credentialCode` names an **AutoFlow Credential**. It must use one of these authentication types:
  - **OAuth 2.0 client credentials**: an Entra app with the scope `https://storage.azure.com/.default`. The step gets a bearer token for the request.
  - **Azure Storage SAS token**: the token is stored as a secret on the credential. You can paste the bare token, the token with a leading `?`, or a full Blob SAS URL.
- The endpoint is always `https://<storageAccount>.blob.core.windows.net/<container>`. If the credential has **base URLs** (an allow-list), that endpoint must start with one of them.
- Credentials are company data. They are **not** part of the flow definition and are not exported or imported with it. When you move a flow to another company or environment, a credential with the same code (and a SAS token or client secret) must already exist there.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `credentialCode` | string (≤ 20) | yes | `""` | Code of the AutoFlow Credential (see above). No SmartFields. |
| `storageAccount` | string | yes | `""` | Storage account name: 3–24 characters, `a-z0-9`. Supports SmartText. |
| `container` | string | yes | `""` | Container name: 3–63 characters, `a-z0-9` and single `-`, starting and ending with a letter or digit. `$root` and `$web` are also allowed. Supports SmartText. |
| `path` | string | no | `""` | Path prefix, e.g. `invoices/2026/`. Empty lists the whole container. The value is trimmed, `\` becomes `/`, and a leading `/` is removed. Supports SmartText. |
| `folderLevelOnly` | boolean | no | `false` | Lists only the files directly inside the folder named by `path`, not the ones in sub-folders. A `/` is appended to a non-empty path. |
| `tagFilters` | array | no | `[]` | Index-tag conditions, combined with AND: `[{"tag": "...", "op": "=", "value": "..."}]`. `op` is one of `=`, `>`, `>=`, `<`, `<=` (empty means `=`). `value` supports SmartText. Rows with an empty `tag` are ignored. |
| `maxResults` | integer | no | `500` | Maximum number of files. A value of `<= 0` means 500. Values above 5000 are capped at 5000. |
| `includeTags` | boolean | no | `true` | Also returns each file's index tags. This needs Storage Blob Data Owner, or a SAS token with the Tags permission. |
| `errorOnEmpty` | boolean | no | `false` | Fails the step when no file is found. |

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `count` | value | – | Number of files returned, as text. |
| `results` | reference | 5564412 | Azure Blob Entry rows. `results` points at the first row, and `results[0]`, `results[1]`, … address the individual rows. |

To use them downstream:

- `{{<slug>_count}}` gives the number of files.
- For Each over `{{<slug>_results}}` loops the rows.
- Row fields include `Name`, `Path`, `Parent Directory`, `Size`, `Content Type`, `Created At`, `Last Modified`, `ETag`, `Tags` (JSON), `Metadata` (JSON), `Storage Account` and `Container`.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `credentialCode` empty | Select a credential for the Azure Blob Storage connection. |
| editor + runtime | error | Credential does not exist | Credential %1 does not exist. |
| editor + runtime | error | Credential type is not OAuth 2.0 client credentials or Azure Storage SAS token | Credential %1 uses the authentication type "%2". Azure Blob Storage steps accept "%3" (an Entra app) or "%4". |
| editor | error | OAuth credential scope does not contain `storage.azure.com` | Credential %1 requests the scope "%2". Azure Blob Storage needs a token for the scope https://storage.azure.com/.default. |
| editor (literal values) + runtime (resolved value) | error | Invalid storage account | The storage account name "%1" is not valid. It must be 3 to 24 characters long and contain only lowercase letters and digits. |
| editor (literal values) + runtime (resolved value) | error | Invalid container | The container name "%1" is not valid. It must be 3 to 63 characters long and contain only lowercase letters, digits and single hyphens, starting and ending with a letter or digit. |
| editor status line + runtime | error | Endpoint is not covered by the credential's base URLs | The URL "%1" is not allowed by credential "%2". Allowed prefixes: %3. |

Values that contain `{{` are only checked at run time, after the SmartFields are resolved. No publish-time check exists for this step.

## Runtime errors

- Credential %1 has no SAS token stored.
- No files were found in container %1 under "%2". (Only with `errorOnEmpty = true`.)
- Azure errors are translated:
  - The container %1 was not found in storage account %2.
  - Azure denied access to container %1 (%2). The Entra app needs the role Storage Blob Data Reader to list and download, Storage Blob Data Contributor to upload, and Storage Blob Data Owner to read or write index tags; a SAS token needs the matching permissions. Azure answered: %3
  - Azure could not authenticate the request (%1). For an Entra app, check that the credential uses the scope https://storage.azure.com/.default; for a SAS token, check that it has not expired. Azure answered: %2
  - Any other error: `Listing files failed: <Azure error text>`

## Example

```json
{
  "id": "6D1C2A40-8E3B-4F7A-9C55-0B1E2F3A4D51",
  "type": "action",
  "action": 5564420,
  "description": "List incoming invoices",
  "slug": "ListInvoices",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/cloud-search.svg",
  "terminating": false,
  "configuration": {
    "credentialCode": "AZSTORAGE",
    "storageAccount": "contosodocs",
    "container": "invoices",
    "path": "inbox/",
    "folderLevelOnly": true,
    "tagFilters": [
      { "tag": "status", "op": "=", "value": "new" }
    ],
    "maxResults": 100,
    "includeTags": true,
    "errorOnEmpty": false
  },
  "outputs": [
    { "name": "count", "type": "value" },
    { "name": "results", "type": "reference", "tableNo": 5564412 }
  ]
}
```

## Gotchas

- Tag filters search the **whole storage account** first. The container and path filters are applied afterwards, in AutoFlow. On a large account, `maxResults` can be reached before the matches in your container come in.
- With `tagFilters`, `includeTags` is not used. Azure's find-by-tags response carries the blob name (and the matching tags), so properties such as size, content type and dates may be empty on those rows. Use Azure Blob: Get file when you need them.
- `maxResults` caps the total; there is no paging output.
- Listing needs Storage Blob Data Reader. Reading tags (`includeTags`) needs Storage Blob Data Owner.
