# Add Stamp

[← All actions](README.md)

Puts a stamp – a free text such as `Checked` or `G/L Account: 6300` – on a record. Users see it in the **Stamps** factbox of the document. Needs a paid AutoFlow licence.

| | |
|---|---|
| Enum name | `AddStamp` |
| Ordinal | `"action": 5564428` |
| Category | Records |
| Terminating | `false` |
| Group / edges | No |
| Availability | GA (paid licence) |

## What it does

The step resolves `reference` to a record and `text` through SmartFields, then writes a new stamp for that record with the running flow execution as its source. The stamp gets the next entry no., which is emitted as the value output `entryNo` and logged as `Stamped %1 with "%2" (stamp %3).`

Stamps are append-only: they can never be changed or deleted, only canceled once with [Cancel Stamp](CancelStamp.md). The step needs no permission set – it works in the session of whoever triggered the flow.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `reference` | string | yes | `""` | One SmartField placeholder that resolves to a record reference, e.g. `"{{trigger_Rec}}"`. A new step in the editor is prefilled with the first record reference the flow offers (normally the trigger's record). |
| `text` | string | yes | `""` | The stamp text. SmartFields are resolved; the result is trimmed and must be 1–250 characters. Longer text fails the step, it is not cut. |

**Translatable** ([translations](../flow-definition.md#translations)): `text`.

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `entryNo` | value | – | Entry no. of the new stamp, as text. Reference it as `{{<slug>_entryNo}}`. |

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `reference` or `text` is empty when saving the dialog | `Please fill in the highlighted fields.` |

## Runtime errors

| condition | message |
|---|---|
| No paid AutoFlow licence (the editor shows it as a red status line) | `Stamps need a paid AutoFlow licence.` |
| `reference` does not resolve | `The record "%1" cannot be resolved.` |
| The record was deleted | `The record %1 no longer exists.` |
| Resolved text is empty | `A stamp needs a text.` |
| Resolved text longer than 250 characters | `The stamp text has %1 characters; a stamp holds at most %2.` |

## Example

```json
{
  "id": "7B1F0C2E-5A3D-4E6F-9A8B-1C2D3E4F5A6B",
  "type": "action",
  "action": 5564428,
  "description": "Add Stamp",
  "slug": "add-stamp",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/stamp.svg",
  "terminating": false,
  "configuration": {
    "reference": "{{trigger_Rec}}",
    "text": "Checked – total {{trigger_Rec.Amount}}"
  },
  "outputs": [
    { "name": "entryNo", "type": "value" }
  ]
}
```

A later [Cancel Stamp](CancelStamp.md) can use `{ "entryNo": "{{add-stamp_entryNo}}" }`.

## Gotchas

- To read stamps in a flow (e.g. "is there a stamp `Checked` that is not canceled?"), use [Find Records](FindRecords.md) on table `5564416` *mse365 AF Stamp*: field 2 *Table No.*, 3 *Record SystemId*, 5 *Text*, 11 *Canceled*.
- Posting a sales or purchase document copies its stamps to the posted documents as new entries with the original time and source.
- Manual stamping in the UI needs the permission sets *mse365 AF STAMP* (stamp) or *mse365 AF STAMP CNCL* (stamp and cancel); flows need neither.
