# When a document is released (interactive)

[← All triggers](README.md)

Runs synchronously in the user's session when a Sales or Purchase document is released manually. The flow can block the release, adjust the header, or take the release over.

| | |
|---|---|
| Enum name | `OnDocumentRelease` |
| Ordinal | `"trigger": 5564543` |
| Category | Interactive |
| Terminating | n/a (trigger) |
| Group / edges | no |
| Availability | GA. Sales Header and Purchase Header. Extensions can register more tables. |

## What it does

Hooks the manual-release events of Sales and Purchase documents, which run before any release work. Release previews never fire the flow. The flow runs **inline in the user's transaction, without commits**:

- An error in the flow, such as an **Error** step that enforces extra required fields, prevents the release and shows the flow's message.
- **Set document field values** writes values onto the header before it is released.
- With **Skip standard processing** on that step, the header is saved with the flow's values and Business Central's own release is skipped. Use this, for example, to set a custom "Pending Approval" status.

Because the flow runs outside a table event, a **Confirm dialog** can ask the user, and the release waits for the answer.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `tableNo` | integer | yes | `0` | `36` (Sales Header) or `38` (Purchase Header). |
| `guiOnly` | boolean | no | `true` | Run only in interactive sessions. |
| `timeoutSec` | integer | no | `30` | Maximum run time. |
| `filters` | array | no | `[]` | `[{ "fieldNo": int, "filter": "text" }]`. These are filters on the header, applied literally, max. 250 characters. |

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `Rec` | reference | `tableNo` | The document header being released. |

Reference it as `{{trigger_Rec}}`.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| publish | error (hard stop) | `tableNo` set | Pick the document table the flow should watch. |
| publish | error (hard stop) | `tableNo` supported | Table %1 is not one of the supported releasable document tables. |
| editor | error | live status for an unsupported table | Table %1 is not supported by this trigger, so the flow would never run. |

## Runtime errors

| condition | effect |
|---|---|
| any error in the flow | The release is prevented and the user sees the flow's message. |

## Example

```json
{
  "id": "0E1F2A3B-4C5D-4E6F-9A7B-8C9D0E1F2A3B",
  "type": "trigger",
  "trigger": 5564543,
  "description": "When a Sales Header is released (interactive)",
  "slug": "trigger",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/pointer-bold.svg",
  "configuration": {
    "tableNo": 36,
    "guiOnly": true,
    "timeoutSec": 30,
    "filters": [
      { "fieldNo": 1, "filter": "Order" }
    ]
  },
  "outputs": [
    { "name": "Rec", "type": "reference", "tableNo": 36 }
  ],
  "level": 0
}
```

## Gotchas

- Only the **manual** release (the Release action) fires it. Releases from posting or other code paths do not.
- **Set document field values** is offered here. The other trigger-response steps are hidden.
