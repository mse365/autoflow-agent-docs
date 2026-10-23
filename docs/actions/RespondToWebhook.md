# Respond to Webhook

[← All actions](README.md)

Sends the HTTP response to a caller that is waiting on the flow's Webhook trigger. The rest of the flow continues in the background.

| | |
|---|---|
| Enum name | `RespondToWebhook` |
| Ordinal | `"action": 5564404` |
| Category | Trigger Responses |
| Terminating | `false` |
| Group / edges | no |
| Availability | GA. Offered only in flows whose trigger is Webhook (`"trigger": 5564403`). |

## What it does

When the step runs, the status code, content type and resolved body are handed back as the response to the HTTP call that started the flow. The flow then stops running synchronously. If more steps follow, they continue asynchronously in the background, and the caller does not wait for them. If this is the last step, the execution completes. The step only matters when the Webhook trigger is configured with `"responseMode": "WaitForResponse"`. In `"InstantReturn"` mode, the trigger has already answered the caller with its own fixed response.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `statusCode` | string (or number) | yes | `"200"` | HTTP status to return, from 200 to 599. Stored as text so it can be a SmartField or SmartFormula. If the resolved value is not an integer, 200 is used. |
| `contentType` | string | yes | `"application/json"` | Response Content-Type. If the key is missing, `application/json` is used. |
| `body` | string | no | `""` | Response body. SmartText (SmartFields `{{..}}`, SmartFormulas `[[..]]`, SmartControls `{#..#}`). |

## Outputs

None.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `statusCode` is required (an empty value is saved as `"200"`) | Please fill in the highlighted fields. |
| editor | error | a numeric `statusCode` must be between 200 and 599 | – |
| editor | error | `contentType` must be non-empty | Please fill in the highlighted fields. |

These checks are not re-run at publish or at run time.

## Runtime errors

None specific to this step. The status code is not range-checked at run time.

## Example

```json
{
  "id": "0A1B2C3D-4E5F-4061-8273-8495A6B7C8D9",
  "type": "action",
  "action": 5564404,
  "description": "Respond to Webhook",
  "slug": "Reply",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/arrow-back-up.svg",
  "terminating": false,
  "configuration": {
    "statusCode": "201",
    "contentType": "application/json",
    "body": "{\"orderId\":\"{{ParseOrder_orderId}}\",\"status\":\"accepted\"}"
  },
  "outputs": []
}
```

## Gotchas

- Set the Webhook trigger's `responseMode` to `"WaitForResponse"`, or this step has no effect on what the caller receives.
- An explicitly empty `"contentType": ""` is sent as an empty Content-Type. Only a missing key falls back to `application/json`.
- Work after the response (for example slow HTTP calls) does not delay the caller. Errors in that work are not reported to the caller either.
