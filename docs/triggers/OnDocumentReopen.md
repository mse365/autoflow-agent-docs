# When a document is reopened (interactive)

[← All triggers](README.md)

Runs synchronously in the user's session when a Sales or Purchase document is reopened manually, including documents that are Pending Approval. The flow can block the reopen, ask the user, adjust the header, or reopen the document its own way.

| | |
|---|---|
| Enum name | `OnDocumentReopen` |
| Ordinal | `"trigger": 5564409` |
| Category | Interactive |
| Terminating | n/a (trigger) |
| Group / edges | no |
| Availability | GA. Sales Header and Purchase Header. For Purchase documents on BC24–BC27, see Gotchas. |

## What it does

Hooks the manual reopen (the Reopen action) of Sales and Purchase documents. The flow runs **inline in the user's transaction, without commits**:

- An error in the flow prevents the reopen and shows the flow's message.
- **Set document field values** adjusts the header before it is reopened.
- With **Skip standard processing**, the header is saved with the flow's values and Business Central's own reopen (Status := Open) is skipped.
- **Pending Approval:** Business Central normally refuses to reopen such a document. If a reopen flow ran for it, that block is lifted, unless Business Central's own approval workflow still has open approval entries.

A **Confirm dialog** can ask the user, and the reopen waits for the answer. `Rec` shows the status from before the reopen.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `tableNo` | integer | yes | `0` | `36` (Sales Header) or `38` (Purchase Header). |
| `guiOnly` | boolean | no | `true` | Run only in interactive sessions. |
| `timeoutSec` | integer | no | `30` | Seconds the flow may run, checked between steps. When it has passed, the remaining steps are skipped and the reopen goes ahead. `0` or less means no limit. |
| `filters` | array | no | `[]` | `[{ "fieldNo": int, "filter": "text" }]`. These are filters on the header, applied literally, max. 250 characters. A filter that Business Central can't parse means the flow never runs. |

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `Rec` | reference | `tableNo` | The document header, with its status from before the reopen. |

Reference it as `{{trigger_Rec}}`.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| publish | error (hard stop) | `tableNo` set | Pick the document table the flow should watch. |
| publish | error (hard stop) | `tableNo` supported | Table %1 is not one of the supported reopenable document tables. |
| editor | error | no table picked | Please fill in the highlighted fields. |
| editor | info | status line (does not block saving) | Table %1 does not exist in this environment. / Table %1 is not supported by this trigger, so the flow would never run. |

## Runtime errors

| condition | effect |
|---|---|
| any error in the flow | The reopen is prevented and the user sees the flow's message. |
| a Sleep step runs | The flow fails with "Step %1 (%2) requested a deferred resume, but the flow is running synchronously. …" and the reopen is prevented. |

## Example

```json
{
  "id": "2A3B4C5D-6E7F-4A8B-9C9D-0E1F2A3B4C5D",
  "type": "trigger",
  "trigger": 5564409,
  "description": "When a Sales Header is reopened (interactive)",
  "slug": "trigger",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/pointer-bold.svg",
  "configuration": {
    "tableNo": 36,
    "guiOnly": true,
    "timeoutSec": 30,
    "filters": []
  },
  "outputs": [
    { "name": "Rec", "type": "reference", "tableNo": 36 }
  ],
  "level": 0
}
```

## Gotchas

- **BC24–BC27, Purchase documents:** the flow runs one step later, after Business Central's Pending Approval check. On those versions a Pending Approval purchase document cannot be reopened through the flow. The flow still prevents, adjusts or handles every other reopen.
- A typical use is a custom approval: on reopen of a Pending Approval document, notify or reject the approval request, then let the reopen proceed.
- **Set document field values** is offered here.
