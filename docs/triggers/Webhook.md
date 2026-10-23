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
| Availability | GA, **Business Central online only**. Needs the environment connected to the AutoFlow portal and an AutoFlow Premium (or higher) package. Next release (not in 27.0.39): any paid AutoFlow license. |

## What it does

On first publish the AutoFlow portal mints a per-flow endpoint URL, which is shown on the flow card and not stored in the JSON. Callers send requests to that URL. The proxy enforces `allowedMethods`, authenticates to Business Central and forwards the method, headers, query and body.

- **InstantReturn**: the call is recorded as an execution and queued as a background run. The caller gets `responseStatusCode` / `responseContentType` with an empty body right away. The background run commits after every step.
- **WaitForResponse**: the flow runs synchronously inside the call. The first **Respond to Webhook** step becomes the HTTP response and ends the synchronous phase; steps after it continue in the background. If the flow ends without one, or `timeoutSec` is exceeded first (checked between steps), the caller gets the default response, and a timed-out flow continues in the background. The synchronous phase is committed once, at the end of the call. A failure in it returns HTTP 500 (`text/plain`, body = error text), rolls back its database changes and marks the execution as failed.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `allowedMethods` | array of string | no | `["POST"]` | Any of `GET`, `POST`, `PUT`, `PATCH`, `DELETE`. Upper-cased. A missing or empty array means `["POST"]`. Enforced by the proxy. |
| `responseMode` | string | no | `"InstantReturn"` | `"InstantReturn"` or `"WaitForResponse"`. It must be the string; any other value acts as InstantReturn. |
| `timeoutSec` | integer | no | `30` | WaitForResponse only: the limit for the synchronous phase, checked between steps. `0` or less means no limit. |
| `responseStatusCode` | integer | no | `200` | Status of the default response (InstantReturn always; WaitForResponse when no Respond to Webhook step ran in time). The default response body is empty. |
| `responseContentType` | string | no | `"application/json"` | Content-Type of the default response (max. 100 characters). |

None of these keys supports SmartText.

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `Payload` | value | – | The request body as JSON object text. An empty body, a JSON array or a non-JSON body becomes `{}`. |
| `Method` | value | – | For example `POST`. |
| `Headers` | value | – | Request headers as forwarded by the proxy. |
| `Query` | value | – | The query string as forwarded by the proxy. |

Reference them as `{{trigger_Payload}}`, `{{trigger_Method}}` and so on. Parse `Payload` with a JSON or Parser step to read single values.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | info | the configure dialog only opens on Business Central online | The webhook trigger is only available on Business Central online (SaaS). It cannot be configured on-premises. |
| publish | info (flow card note) | no portal API key | No AutoFlow portal API key on this environment. Connect it to the AutoFlow portal (AutoFlow Setup) before publishing a webhook flow. |
| publish | info (flow card note) | portal registration failed | Registration failed (HTTP %1): %2 |
| publish | info (flow card status) | package below Premium | The webhook trigger requires at least AutoFlow Premium. Upgrade your package in the AutoFlow portal, then republish this flow. |
| publish | info (flow card status) | admin consent missing | Administrator consent required - click to grant. |
| publish | info (flow card note) | proxy app could not be enabled (needs admin) | The webhook is registered, but an administrator must enable the AutoFlow webhook proxy in this environment – use the "Enable webhook proxy" action. |

There are no configuration checks, in the editor or at publish. None of the publish-stage items blocks or warns during the publish: the flow is published, but the webhook is not live until they are resolved.

## Runtime errors

| condition | message / response |
|---|---|
| unknown endpoint id | No webhook flow is registered for unique id '%1'. |
| WaitForResponse flow fails | HTTP 500, `text/plain`, body = error text |
| WaitForResponse: a Sleep step runs before Respond to Webhook | Step %1 (%2) requested a deferred resume, but the flow is running synchronously. Use Sleep or other time-based deferral steps only outside of synchronous frames (Webhook sync phase or SubFlow body). |

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
- In WaitForResponse mode, put Sleep steps after Respond to Webhook.
- The proxy's application user needs the permissions that the flow's steps use. The flow card links to that user.
- No recurring Job Queue entry is created. Each call is its own execution.
