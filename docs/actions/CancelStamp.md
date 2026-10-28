# Cancel Stamp

[← All actions](README.md)

Cancels a stamp by its entry no. The stamp stays on the record, crossed out, with the flow as the cancel source. Needs a paid AutoFlow licence.

| | |
|---|---|
| Enum name | `CancelStamp` |
| Ordinal | `"action": 5564429` |
| Category | Records |
| Terminating | `false` |
| Group / edges | No |
| Availability | GA (paid licence) |

## What it does

The step resolves `entryNo`, reads the stamp and marks it canceled, with the running flow execution as the cancel source. It logs `Canceled stamp %1.` A stamp is canceled at most once and cannot be un-canceled.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `entryNo` | string | yes | `""` | Entry no. of the stamp, usually `{{<add-stamp-slug>_entryNo}}` or a value from Find Records on *mse365 AF Stamp*. Must resolve to an integer. |

## Outputs

None.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `entryNo` is empty when saving the dialog | `Please fill in the highlighted fields.` |

## Runtime errors

| condition | message |
|---|---|
| No paid AutoFlow licence | `Stamps need a paid AutoFlow licence.` |
| `entryNo` is not an integer | `"%1" is not a stamp entry no.` |
| No stamp with this entry no. | `Stamp %1 does not exist.` |
| Stamp already canceled | `Stamp %1 is already canceled.` |

## Example

```json
{
  "id": "8C2A1D3F-6B4E-4F70-8B9C-2D3E4F5A6B7C",
  "type": "action",
  "action": 5564429,
  "description": "Cancel Stamp",
  "slug": "cancel-stamp",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/stamp-cancel.svg",
  "terminating": false,
  "configuration": {
    "entryNo": "{{add-stamp_entryNo}}"
  },
  "outputs": []
}
```

## Gotchas

- To return to an earlier state, put on a new stamp with [Add Stamp](AddStamp.md); a canceled stamp stays canceled.
- The step needs no permission set.
