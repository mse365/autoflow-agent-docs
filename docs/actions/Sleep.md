# Sleep

[← All actions](README.md)

Pauses the flow for a configured time.

| | |
|---|---|
| Enum name | `Sleep` |
| Ordinal | `"action": 103` |
| Category | Utilities |
| Terminating | `false` |
| Group / edges | No |
| Availability | GA |

## What it does

The step converts `duration` × `unit` into milliseconds and then does one of two things:

- **Short wait**: unit Milliseconds and less than 10,000 ms. The worker blocks in-process for that time, and the step then completes.
- **Deferred wait**: any other unit, or 10,000 ms and more. The run is parked with status *Sleeping*, and a one-time job queue entry resumes it at *now + duration*. On resume, the step completes immediately and the flow continues with the next step.

A deferred wait is only possible in an asynchronous (job queue) run. Inside a synchronous frame (webhook synchronous phase, SubFlow body, interactive document or page triggers), the step fails instead.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `duration` | string (integer text) | yes | – | Positive whole number in the chosen unit, e.g. `"30"`. Can be a SmartField such as `"{{RetryDelay_Seconds}}"`, which is resolved at runtime. Decimals are not accepted. |
| `unit` | integer | no | `1` | `0` = Milliseconds, `1` = Seconds, `2` = Minutes, `3` = Hours. A missing or unknown value is treated as Seconds. |

## Outputs

None.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| publish | warning | `duration` is empty or missing | `Sleep step '%1' has no duration configured.` |
| publish | warning | `duration` is not an integer > 0 and contains no `{{…}}` token | `Sleep step '%1' duration '%2' is not a positive integer or SmartField token.` |
| editor | error | same two conditions (configuration rejected) | – |

`%1` is the step **id**, not its description.

## Runtime errors

| condition | message |
|---|---|
| Resolved duration is not an integer > 0 | `Sleep duration '%1' is not a positive integer.` |
| Deferred wait requested while running synchronously | `Step %1 (%2) requested a deferred resume, but the flow is running synchronously. Use Sleep or other time-based deferral steps only outside of synchronous frames (Webhook sync phase or SubFlow body).` |

## Example

```json
{
  "id": "4D5E6F70-8192-4A3B-9C4D-5E6F708192A1",
  "type": "action",
  "action": 103,
  "description": "Sleep 5 Minutes",
  "slug": "Sleep5Minutes",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/hourglass.svg",
  "terminating": false,
  "configuration": {
    "duration": "5",
    "unit": 2
  },
  "outputs": []
}
```

## Gotchas

- `unit` is stored as an **integer ordinal**, not as a name such as `"Minutes"`.
- The default unit is Seconds, not Milliseconds. With `{"duration": "500"}` and no `unit`, the step waits 500 **seconds** and therefore defers.
- To pause briefly in a synchronous or interactive flow, use unit `0` with less than 10,000.
- A SmartField duration is only checked at runtime. If it resolves to empty, zero or a non-integer, the step fails.
