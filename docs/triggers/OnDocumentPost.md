# When a document is posted (interactive)

[← All triggers](README.md)

Runs synchronously in the user's session when a Sales or Purchase document is posted. The flow can block the posting or adjust the header first.

| | |
|---|---|
| Enum name | `OnDocumentPost` |
| Ordinal | `"trigger": 5564549` |
| Category | Interactive |
| Terminating | n/a (trigger) |
| Group / edges | no |
| Availability | GA. Sales Header and Purchase Header. Extensions can register more tables. |

## What it does

Hooks the "before post" events of Sales and Purchase posting, which run before any posting work. Posting previews never fire the flow. The flow runs **inline in the user's transaction, without commits**:

- An error in the flow, such as an **Error** step, prevents the posting and shows the flow's message.
- **Set document field values** writes values onto the header before it is posted. Its "Skip standard processing" option has no effect here.

Because the flow runs outside a table event, a **Confirm dialog** can ask the user, and the posting waits for the answer.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `tableNo` | integer | yes | `0` | `36` (Sales Header) or `38` (Purchase Header). |
| `guiOnly` | boolean | no | `true` | Run only in interactive sessions. Batch posting in the background is then skipped. |
| `timeoutSec` | integer | no | `30` | Maximum run time. |
| `filters` | array | no | `[]` | `[{ "fieldNo": int, "filter": "text" }]`. These are filters on the header, applied literally, max. 250 characters. |

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `Rec` | reference | `tableNo` | The document header about to be posted. |

Reference it as `{{trigger_Rec}}`.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| publish | error (hard stop) | `tableNo` set | Pick the document table the flow should watch. |
| publish | error (hard stop) | `tableNo` supported | Table %1 is not one of the supported postable document tables. |
| editor | error | live status for an unsupported table | Table %1 is not supported by this trigger, so the flow would never run. |

## Runtime errors

| condition | effect |
|---|---|
| any error in the flow | The posting is prevented and the user sees the flow's message. |

## Example

```json
{
  "id": "1F2A3B4C-5D6E-4F7A-8B8C-9D0E1F2A3B4C",
  "type": "trigger",
  "trigger": 5564549,
  "description": "When a Purchase Header is posted (interactive)",
  "slug": "trigger",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/pointer-bold.svg",
  "configuration": {
    "tableNo": 38,
    "guiOnly": true,
    "timeoutSec": 30,
    "filters": [
      { "fieldNo": 1, "filter": "Invoice" }
    ]
  },
  "outputs": [
    { "name": "Rec", "type": "reference", "tableNo": 38 }
  ],
  "level": 0
}
```

## Gotchas

- It runs **before** posting. The posted documents do not exist yet, so react to them with a background trigger on the posted tables instead.
- **Set document field values** is offered here. The other trigger-response steps are hidden.
