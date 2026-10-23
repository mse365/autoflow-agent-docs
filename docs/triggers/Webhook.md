# When a webhook is received

[← All triggers](README.md)

Starts the flow when the AutoFlow webhook proxy forwards an HTTP call to this flow's endpoint URL. The flow can answer the caller synchronously.

| | |
|---|---|
| Enum name | `Webhook` |
| Ordinal | `"trigger": 5564403` |
| Category | Web |
| Terminating | n/a (trigger) |
| Group / edges | no |
| Availability | GA, **Business Central online only**. Needs the environment connected to the AutoFlow portal and a paid AutoFlow license. |

## What it does

On first publish the AutoFlow portal mints a per-flow endpoint URL, which is shown on the flow card and not stored in the JSON. Callers send requests to that URL. The proxy enforces `allowedMethods`, authenticates to Business Central and forwards the method, headers, query and body.

- **InstantReturn**: the call is recorded as an execution and queued as a background run. The caller gets `responseStatusCode` / `responseContentType` with an empty body right away. The background run commits after every step.
- **WaitForResponse**: the flow runs synchronously inside the call. The first **Respond to Webhook** step becomes the HTTP response. If the flow ends without one, or `timeoutSec` passes first, the caller gets the default response, and a timed-out flow continues in the background. A failure in the synchronous phase returns HTTP 500 (`text/plain`, body = error text) and marks the execution as failed.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `allowedMethods` | array of string | no | `["POST"]` | Any of `GET`, `POST`, `PUT`, `PATCH`, `DELETE`. Upper-cased. An empty array means `["POST"]`. |
| `responseMode` | string | no | `"InstantReturn"` | `"InstantReturn"` or `"WaitForResponse"`. It must be the string; any other value acts as InstantReturn. |
| `timeoutSec` | integer | no | `30` | WaitForResponse only: the limit for the synchronous phase. Must be > 0. |
| `responseStatusCode` | integer | no | `200` | Status of the default response. |
| `responseContentType` | string | no | `"application/json"` | Content-Type of the default response (max. 100 characters). |

None of these keys supports SmartText.

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `Payload` | value | – | The request body as JSON object text. A body that is not a JSON object becomes `{}`. |
| `Method` | value | – | For example `POST`. |
| `Headers` | value | – | Request headers as forwarded by the proxy. |
| `Query` | value | – | The query string as forwarded by the proxy. |

Reference them as `{{trigger_Payload}}`, `{{trigger_Method}}` and so on. Parse `Payload` with a JSON or Parser step to read single values.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | only configurable on Business Central online | The webhook trigger is only available on Business Central online (SaaS). It cannot be configured on-premises. |
| editor | error | `timeoutSec` > 0, at least one method | (no message) |
| publish | warning (flow card note, publish succeeds) | no portal API key | No AutoFlow portal API key on this environment. Connect it to the AutoFlow portal (AutoFlow Setup) before publishing a webhook flow. |
| publish | warning (flow card note) | portal registration failed | Registration failed (HTTP %1): %2 |
| publish | warning (flow card status) | no paid license | The webhook trigger requires a paid AutoFlow license; the free tier does not include it. License AutoFlow in the AutoFlow portal, then republish this flow. |
| publish | warning (flow card note) | proxy app could not be enabled (needs admin) | The webhook is registered, but an administrator must enable the AutoFlow webhook proxy in this environment – use the "Enable webhook proxy" action. |

None of the publish-stage items blocks the publish. The webhook simply is not live until they are resolved.

## Runtime errors

| condition | message / response |
|---|---|
| unknown endpoint id | No webhook flow is registered for unique id '%1'. |
| WaitForResponse flow fails | HTTP 500, `text/plain`, body = error text |

## Example

```json
{
  "id": "5F6A7B8C-9D0E-4F1A-8B2C-3D4E5F6A7B8C",
  "type": "trigger",
  "trigger": 5564403,
  "description": "When a webhook is received",
  "slug": "trigger",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/webhook.svg",
  "configuration": {
    "allowedMethods": ["POST"],
    "responseMode": "WaitForResponse",
    "timeoutSec": 20,
    "responseStatusCode": 202,
    "responseContentType": "application/json"
  },
  "outputs": [
    { "name": "Payload", "type": "value" },
    { "name": "Method", "type": "value" },
    { "name": "Headers", "type": "value" },
    { "name": "Query", "type": "value" }
  ],
  "level": 0
}
```

## Gotchas

- `responseMode` is stored as a **string**. Writing `1` (the canvas option index) silently means InstantReturn.
- The URL is environment-specific and not part of the definition. An imported or copied flow gets a new URL on publish.
- **Respond to Webhook** is only offered in Webhook flows. In InstantReturn mode it has no caller left to answer.
- The proxy's application user needs the permissions that the flow's steps use. The flow card links to that user.
- No recurring Job Queue entry is created. Each call is its own execution.
