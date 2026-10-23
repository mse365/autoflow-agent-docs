# When a page is opened (interactive)

[← All triggers](README.md)

Runs synchronously when a user opens one of the supported card pages, before the page is shown. Use it to show a hint, or to keep the user out with an error.

| | |
|---|---|
| Enum name | `OnPageOpen` |
| Ordinal | `"trigger": 5564407` |
| Category | Interactive |
| Terminating | n/a (trigger) |
| Group / edges | no |
| Availability | GA. Supported card pages only. Extensions can register more. |

## What it does

Hooks the open event of the configured page. In a session with a UI, and when the page shows a saved record that matches `filters`, the flow runs in the user's session before the page appears. An error from the flow, such as an **Error** step, stops the page from opening and shows the flow's message. Otherwise the page opens normally. The run commits its own execution entries. A page that the running flow opens itself does not re-trigger it.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `pageNo` | integer | yes | `0` | Sales Quote `41`, Sales Order `42`, Sales Invoice `43`, Sales Credit Memo `44`, Sales Return Order `6630`, Blanket Sales Order `507`, Purchase Quote `49`, Purchase Order `50`, Purchase Invoice `51`, Purchase Credit Memo `52`, Purchase Return Order `6640`, Blanket Purchase Order `509`, Customer Card `21`, Vendor Card `26`, Contact Card `5050`, Item Card `30`. |
| `timeoutSec` | integer | no | `10` | Maximum run time. The page waits for it. |
| `filters` | array | no | `[]` | `[{ "fieldNo": int, "filter": "text" }]`. These are filters on the page's record (its source table), applied literally, max. 250 characters. |

The table is not configured. It is always the page's source table.

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `Rec` | reference | page's source table | The record the page shows. |
| `PageNo` | value | – | The page number as text. |

Reference them as `{{trigger_Rec}}` and `{{trigger_PageNo}}`.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| publish | error (hard stop) | `pageNo` set | Pick the page the flow should watch. |
| publish | error (hard stop) | `pageNo` supported | Page %1 is not supported by this trigger, so the flow would never run. |

## Runtime errors

| condition | effect |
|---|---|
| any error in the flow | The page does not open and the user sees the flow's message. |

## Example

```json
{
  "id": "3B4C5D6E-7F8A-4B9C-8D0E-1F2A3B4C5D6E",
  "type": "trigger",
  "trigger": 5564407,
  "description": "When Customer Card is opened (interactive)",
  "slug": "trigger",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/window.svg",
  "configuration": {
    "pageNo": 21,
    "timeoutSec": 10,
    "filters": [
      { "fieldNo": 39, "filter": "<>' '" }
    ]
  },
  "outputs": [
    { "name": "Rec", "type": "reference", "tableNo": 18 },
    { "name": "PageNo", "type": "value" }
  ],
  "level": 0
}
```

## Gotchas

- New, unsaved records, such as a new sales order that is still empty, do not fire the flow.
- Keep it short. The default timeout is 10 seconds.
- A flow on Sales Order (42) does not fire for Sales Quote (41), even though both show table 36.
- Trigger-response steps are hidden here.
