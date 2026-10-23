# When a page is closed (interactive)

[← All triggers](README.md)

Runs synchronously when a user closes one of the supported card pages, before the page actually closes. With a **Prevent page close** step the flow keeps the page open and tells the user why.

| | |
|---|---|
| Enum name | `OnPageClose` |
| Ordinal | `"trigger": 5564408` |
| Category | Interactive |
| Terminating | n/a (trigger) |
| Group / edges | no |
| Availability | GA. Supported card pages only. Extensions can register more. |

## What it does

Hooks the page's query-close event. In a session with a UI, and when the page shows a saved record that matches `filters`, the flow runs in the user's session. If it ends with **Prevent page close**, the page stays open and the step's message appears as a dialog or as a notification in the page bar. Otherwise the page closes. The run commits its own execution entries, so a prevented close stays visible in the execution list. The trigger never overrules another extension that already keeps the page open.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `pageNo` | integer | yes | `0` | Same 16 card pages as [When a page is opened](OnPageOpen.md): `41`, `42`, `43`, `44`, `6630`, `507`, `49`, `50`, `51`, `52`, `6640`, `509`, `21`, `26`, `5050`, `30`. |
| `timeoutSec` | integer | no | `10` | Maximum run time. The user is waiting to leave. |
| `filters` | array | no | `[]` | `[{ "fieldNo": int, "filter": "text" }]`. These are filters on the page's record, applied literally, max. 250 characters. |

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `Rec` | reference | page's source table | The record the page was showing. |
| `PageNo` | value | – | The page number as text. |

Reference them as `{{trigger_Rec}}` and `{{trigger_PageNo}}`.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| publish | error (hard stop) | `pageNo` set | Pick the page the flow should watch. |
| publish | error (hard stop) | `pageNo` supported | Page %1 is not supported by this trigger, so the flow would never run. |

## Runtime errors

None specific to this trigger. To keep the page open, use Prevent page close rather than an Error step.

## Example

```json
{
  "id": "4C5D6E7F-8A9B-4C0D-9E1F-2A3B4C5D6E7F",
  "type": "trigger",
  "trigger": 5564408,
  "description": "When Sales Order is closed (interactive)",
  "slug": "trigger",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/window-off.svg",
  "configuration": {
    "pageNo": 42,
    "timeoutSec": 10,
    "filters": [
      { "fieldNo": 120, "filter": "Open" }
    ]
  },
  "outputs": [
    { "name": "Rec", "type": "reference", "tableNo": 36 },
    { "name": "PageNo", "type": "value" }
  ],
  "level": 0
}
```

## Gotchas

- **Prevent page close** is only offered for this trigger. The other trigger-response steps are hidden.
- After a record is deleted, Business Central force-closes the card and the flow does not run. It also does not run for unsaved new records.
- Keep it short. The default timeout is 10 seconds.
