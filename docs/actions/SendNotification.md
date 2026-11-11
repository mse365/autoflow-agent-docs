# Send Notification

[← All actions](README.md)

Shows a message to the user running the flow, either as a page notification with up to three action buttons or as a modal dialog message.

| | |
|---|---|
| Enum name | `SendNotification` |
| Ordinal | `"action": 5564557` |
| Category | Utilities |
| Terminating | `false` |
| Group / edges | no |
| Availability | GA (offered for every trigger) |

## What it does

Resolves `Message` and shows it in the current client session, either as a notification in the bar at the top of the page or as a dialog message. A dialog message only appears once the flow has finished and control returns to the client. A notification can carry up to three actions: start a manual flow, open a card page on a record, or open a filtered list page. Everything an action needs is resolved while the step runs, and the click happens later, outside the flow. The run offers the first three rows that have a label, a type and a target. Without a user interface, a Job Queue run keeps the message for the user following the run in the wait dialog. Any other headless session skips it. The flow always continues with the next step.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `Message` | string | yes | `""` | SmartText (SmartFields, SmartFormulas, SmartControls). **Capital M.** Truncated to 2048 characters. Empty means nothing is shown. |
| `display` | integer | no | `0` | `0` = Notification, `1` = Dialog message. Any other number shows a notification without actions. |
| `actions` | array | no | `[]` | Up to 3 rows. Used only when `display` = 0. A non-array value is ignored. |

Action rows (`actions[]`):

| key | type | description |
|---|---|---|
| `label` | string | SmartText button caption (max 100 characters). Required. |
| `type` | string | `"1"` Start flow, `"2"` Open card, `"3"` Open list. These are **string** ordinals. |
| `target` | string | Start flow: the **Code** of a published manual flow. Open card / Open list: page ID as a string, e.g. `"21"`. |
| `record` | string | `{{selector}}` to a record reference. Required for Open card and for Start flow when the manual flow runs on a record. Use `""` otherwise. |
| `recordTableNo` | integer | The table of `record`, written by the editor. `0` means unknown and skips the table check. |
| `filters` | array | Open list only: `[{ "fieldNo": 2, "filter": "<SmartText filter>" }]` on the page's source table. |
| `filterTableNo` | integer | Open list only: the table the filters belong to. Must equal the page's source table (`0` = unchecked). |
| `filterDisplay` | string | Display text only. |

**Translatable** ([translations](../flow-definition.md#translations)): `Message`, `actions[].label`.

## Outputs

None.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `Message` is a required field | Please fill in the highlighted fields. |
| editor | – | at most 3 action rows (the editor does not let you add more) | – |
| editor status line, publish | warning | more than 3 actions | A notification can carry at most %1 actions. Remove the others. |
| editor status line, publish | warning | row without label | Enter a label. |
| editor status line, publish | warning | row type not 1/2/3 | Choose what the action does. |
| editor status line, publish | warning | Start flow without target | Choose the flow to start. |
| editor status line, publish | warning | target is not a published manual flow | The flow %1 is not an active manual flow on this system. |
| editor status line, publish | warning | record-based manual flow without `record` | The flow %1 runs on a record. Select the record to start it for. |
| editor status line, publish | warning | Open card/list without page | Choose the page to open. |
| editor status line, publish | warning | page does not exist | The page %1 does not exist. |
| editor status line, publish | warning | Open card on a non-card page (Card/Document/ListPlus allowed) | The page %1 is not a card page. Choose a card or document page. |
| editor status line, publish | warning | Open list on a non-list page (List/Worksheet allowed) | The page %1 is not a list page. Choose a list or worksheet page. |
| editor status line, publish | warning | page without (non-temporary) source table | The page %1 shows no table, so it cannot be opened on a record. |
| editor status line, publish | warning | Open card without `record` | Select the record to open the card page on. |
| editor status line, publish | warning | record table ≠ expected table | The record belongs to table %1, but table %2 is expected. |
| editor status line, publish | warning | `filterTableNo` ≠ page source table | The filters were set for table %1, but the page %2 shows table %3. Set the filters again. |

The action checks only apply when `display` = 0. In the editor the first problem is shown on the status line; it does not block saving. Row problems are prefixed `Action <n>: `. At publish each problem becomes a warning prefixed `Send notification '<stepId>': `, for example `Send notification '<stepId>': Action 2: Enter a label.` Interactive publish asks for confirmation; a headless publish fails while any warning exists. An empty `Message` is not checked at publish; the step then shows nothing.

## Runtime errors

None. An action row that cannot be resolved at run time is left out, and the notification is still sent. Reasons include an unknown flow or page, an unresolvable or deleted record, a wrong table, a filter that does not apply, or a filter view longer than 2000 characters. The log line is `Notification action "%1" left out: %2`. Sessions without a UI log either `No user interface – notification skipped.` or `No user interface – the message is shown to the user following the run once it has finished.`

## Example

```json
{
  "id": "F3B6D0A8-2C41-4E9F-8D57-6A1E0C3B9F72",
  "type": "action",
  "action": 5564557,
  "description": "Send Notification",
  "slug": "NotifyUser",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/bell.svg",
  "terminating": false,
  "configuration": {
    "Message": "A new customer was created and needs review.",
    "display": 0,
    "actions": [
      {
        "label": "Open customer",
        "type": "2",
        "target": "21",
        "record": "{{trigger_Rec}}",
        "recordTableNo": 18,
        "filters": [],
        "filterTableNo": 0,
        "filterDisplay": ""
      },
      {
        "label": "Blocked customers",
        "type": "3",
        "target": "22",
        "record": "",
        "recordTableNo": 0,
        "filters": [ { "fieldNo": 39, "filter": "Invoice|All" } ],
        "filterTableNo": 18,
        "filterDisplay": ""
      }
    ]
  },
  "outputs": []
}
```

## Gotchas

- The message key is `Message` with a capital M. A lowercase `message` is ignored.
- `actions[].type` is a **string** (`"2"`), not a number.
- A Start flow `target` is the flow **Code**, not its number.
- Dialog messages (`display: 1`) are only shown after the flow finishes, and actions are ignored for them.
- In a background flow that is not a Job Queue run started by a user, nothing is shown.
- Leave `recordTableNo` / `filterTableNo` at `0` if you don't know the table. A wrong non-zero value causes a publish warning.
