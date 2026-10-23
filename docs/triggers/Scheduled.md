# On a schedule

[← All triggers](README.md)

Runs the flow periodically from a Job Queue entry that is created when the flow is published.

| | |
|---|---|
| Enum name | `Scheduled` (enum caption "When scheduled to run") |
| Ordinal | `"trigger": 101` |
| Category | Base |
| Terminating | n/a (trigger) |
| Group / edges | no |
| Availability | GA |

## What it does

Publishing creates one recurring Job Queue entry for the flow. It runs every **60 minutes** on every weekday, all day. The first run comes one interval after publishing, not right away. Each Job Queue run starts one execution and queues it as its own Job Queue entry, so every tick is one background run that commits after every step. To change the interval or the time window, edit the Job Queue entry in Business Central. The schedule is not stored in the flow definition.

## Configuration

None. `configuration` must be `{}`. The configure dialog only says "There is nothing to configure for this trigger."

## Outputs

None. The flow runs without a record. Fetch data with steps such as Find Records.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | info | `configuration` must be empty | (no message) |

No publish-time trigger checks. The general flow checks still apply, for example that the flow has at least one action step.

## Runtime errors

None specific to this trigger. If the license check fails when the Job Queue entry runs, that run fails with "AutoFlow license validation failed for flow %1 – open Subscription Management to resolve."

## Example

```json
{
  "id": "1A2B3C4D-5E6F-4A7B-8C9D-0E1F2A3B4C5D",
  "type": "trigger",
  "trigger": 101,
  "description": "On a schedule",
  "slug": "trigger",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/calendar-time.svg",
  "configuration": {},
  "outputs": [],
  "level": 0
}
```

## Gotchas

- The interval (60 minutes) and the weekdays live on the Job Queue entry, not in the JSON. Re-importing a flow does not carry a custom schedule.
- The first run is one interval after publishing. To test now, use **Run this flow** on the flow card.
- Trigger-response steps (Respond to Webhook, Return SubFlow Output, Return PDF, Set report file name, Set document field values, Prevent page close) are hidden in scheduled flows.
