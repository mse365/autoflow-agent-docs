# HTTP Request

[← All actions](README.md)

Calls any HTTP endpoint and exposes the response status, headers and body to later steps.

| | |
|---|---|
| Enum name | `HttpRequest` |
| Ordinal | `"action": 5564402` |
| Category | Web |
| Terminating | `false` |
| Group / edges | no |
| Availability | GA |

## What it does

The step sends one HTTP request from the Business Central server, with SmartFields in the URL, header values and body already resolved. It can use an **AutoFlow Credential** (by code), which adds authentication, a base URL and default headers. The step waits for the response and publishes its status, headers and body. A 4xx or 5xx response does **not** fail the step; branch on `responseStatus` instead. Only transport failures raise an error: invalid URL, connection or DNS failure, a timeout, or HTTP calls being blocked in the environment. Binary responses (PDF, images, octet-stream and so on) are kept as raw bytes.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `url` | string | yes | `""` | Request URL. SmartText. With a credential that has base URLs, a relative URL (one not starting with `http://` or `https://`) is prefixed with the credential's first base URL. |
| `method` | string | yes | `"GET"` | `GET`, `POST`, `PUT`, `PATCH` or `DELETE` (upper case). It is sent as written. |
| `headers` | object | no | `{}` | Flat object `{ "Header-Name": "value" }`. Values are SmartText. Names are truncated to 50 characters and values to 4096. The key `Content-Type` (exact spelling) sets the content type of the body. |
| `body` | string | no | `""` | Request body, SmartText. The editor shows it only for POST, PUT and PATCH. If the unresolved body is exactly one `{{field}}` with no format suffix and that field holds binary data (a BLOB or Media field, or a binary output such as another HTTP response body), the raw bytes are sent. With a credential, the reserved tokens `{{credential.username}}` and `{{credential.password}}` are replaced at send time (XML-escaped). |
| `credentialCode` | string (max 20) | no | `""` | Code of an AutoFlow Credential in the target company. Empty means no credential; authenticate through `headers` instead. |

### Credentials: what goes in the flow JSON

A credential is a per-company Business Central record that holds the following:

- an authentication type: none, API key (header or query), Basic, Bearer, username and password in the request body, OAuth 2.0 client credentials, or Azure Storage SAS token
- optional **base URLs**, which also act as an allow-list
- optional **default headers**
- **secrets**, stored encrypted in Business Central's isolated storage for that company

**Only the code** (`credentialCode`) is stored in the flow definition. Secrets, base URLs, default headers and the auth type are never exported and cannot be supplied in the JSON. This has the following consequences for an agent writing a flow:

- Set `credentialCode` to the code of a credential that already exists in every company where the flow is imported. Credentials are environment-specific; an administrator creates them in the AutoFlow Credentials list.
- Never put secrets into `headers`, `url` or `body` when a credential can be used. Values written in the flow are visible in the definition, and request headers are written to the execution log (only authentication headers added by a credential are removed from the log).
- If the code does not exist at run time, the request is sent **without** the credential. There is no error, so the call usually comes back 401 or 403.
- For SOAP or XML APIs that expect the login in the body, use a credential of type "Username + password (request body)" and put `{{credential.username}}` and `{{credential.password}}` in `body`. Those two tokens are the only way to reach a credential's secrets from the flow, and only for the credential selected on that step.

When a credential is used, headers are merged in this order, with later sources winning: credential default headers, then step `headers`, then authentication headers. If the credential has base URLs, the final URL must start with one of them. The match is case-insensitive, respects path boundaries and ignores the query string. Otherwise the request is refused.

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `responseStatus` | `value` | – | Numeric status code as text, for example `"200"`. |
| `responseHeaders` | `value` | – | JSON object text holding the first value of each response header. |
| `responseBody` | `value` | – | Body as text. For a binary Content-Type, the raw bytes; use the whole `{{slug_responseBody}}` to write them to a BLOB or Media field. |

To reference them, use `{{<slug>_responseStatus}}`, `{{<slug>_responseHeaders}}` and `{{<slug>_responseBody}}`. The `outputs` array always contains all three.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `url` is required | Please fill in the highlighted fields. |
| editor | warning | `method` is one of GET/POST/PUT/PATCH/DELETE (other text is sent as-is but is reset to GET when the step is next edited) | – |
| editor | error | `headers` is an object of name → string | – |
| editor (live status) | warning | with a credential that has base URLs, the URL is allowed | ⚠ The URL "%1" is not allowed by credential "%2". Allowed prefixes: %3. |

There is no step-specific publish check. The step's validity check always passes. Only the generic dangling-reference warning applies.

## Runtime errors

- `The URL "%1" is not allowed by credential "%2". Allowed prefixes: %3.`: the credential's allow-list rejected the URL, and nothing was sent.
- `Failed to obtain OAuth token for credential %1: HTTP %2. Response: %3`: the OAuth 2.0 client-credentials token request failed.
- `OAuth token endpoint for credential %1 returned an unexpected response.`: the token response could not be read.
- The platform's HTTP errors: invalid URI, connection or timeout failures, or outgoing HTTP calls not allowed for the extension in this environment.

## Example

```json
{
  "id": "7E6D5C4B-3A29-4180-9F7E-6D5C4B3A2918",
  "type": "action",
  "action": 5564402,
  "description": "Post order to shop",
  "slug": "PostOrder",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/world-www.svg",
  "terminating": false,
  "configuration": {
    "url": "/api/orders/{{trigger_Rec.no}}",
    "method": "POST",
    "headers": {
      "Content-Type": "application/json",
      "Accept": "application/json"
    },
    "body": "{\"orderNo\":\"{{trigger_Rec.no}}\",\"customer\":\"{{trigger_Rec.selltocustomerno}}\"}",
    "credentialCode": "SHOP-API"
  },
  "outputs": [
    { "name": "responseStatus", "type": "value" },
    { "name": "responseHeaders", "type": "value" },
    { "name": "responseBody", "type": "value" }
  ]
}
```

In this example, `SHOP-API` must exist as a credential with a base URL such as `https://shop.example.com` in the target company. The trigger placeholders are illustrative; use your trigger's real outputs.

## Gotchas

- Feed `{{<slug>_responseBody}}` into a [Parser](Parser.md) step to extract values.
- The editor's "Send test request" button sends a real, authenticated request. It stores nothing in the configuration.
- Business Central sandboxes block outgoing HTTP until "Allow HttpClient Requests" is enabled for the extension.
- `Content-Type` is matched with that exact capitalisation. A header written as `content-type` is added as a normal request header instead of the body's content type.
