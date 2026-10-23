# Set document field values

[← All actions](README.md)

A terminating response step for interactive document flows. It writes field values onto the document before Business Central saves, releases, reopens or posts it.

| | |
|---|---|
| Enum name | `SetDocumentField` |
| Ordinal | `"action": 5564530` |
| Category | Trigger Responses |
| Terminating | `true` |
| Group / edges | No |
| Availability | GA. Only offered in flows started by *When a record is created or modified / When a document is released / posted / reopened (interactive)* |

## What it does

The step does not write to the database itself. It resolves the configured `values` to literal text inside the flow and hands them back to the waiting interactive document trigger. The trigger then applies them to the live document record (Validate or direct assignment per row) right before Business Central continues with its own save, release, reopen or post.

`skipStandard` changes the behaviour in *released* and *reopened* flows only: Business Central does **not** release or reopen the document, and AutoFlow saves it with these values instead (e.g. Status = Pending Approval for a custom approval). In that case warehouse requests are not released or reopened either. To prevent the document action altogether, end the flow with an Error step instead.

The picker and the editor's default description show "Set Field Values".

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `tableNo` | integer | no | `0` | Table of the trigger's document. It only scopes the editor's field lookup, and the editor derives it from the trigger output. At runtime the values always go to the trigger's record. |
| `skipStandard` | boolean | no | `false` | Skip standard processing. It only has an effect in *released* and *reopened* flows. |
| `values` | array | yes | `[]` | At least one row `{lineNo, fieldNo, value, validate?, inputFormat?}`, the same shape as in [Insert Record](InsertRecord.md#values-row-shared-by-insert--modify--rename--set-document-field-values). **Non-key fields only.** |

## Outputs

None.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| runtime | warning | `values` is empty: nothing is written | (no message) |
| publish | warning | the step has a successor (terminating steps must end their path) | `Step "%1" is a terminating step but has a successor – terminating steps must end the path.` |

The step's own check for an empty `values` list (`Add at least one field to set on the record.`) is not run in 27.0.39, and the editor does not require a row. Always set at least one field.

## Runtime errors

These errors surface in the user's session when the trigger applies the values, and they cancel the document action:

| condition | message |
|---|---|
| Row targets a primary-key field | `Field "%1" is part of the primary key and cannot be modified. Use a Rename Record step instead.` |
| `fieldNo` not in the document table | `Field %1 does not exist in table %2.` |
| Invalid input format | `"%1" is not a valid input format. Leave it empty for the regional format, enter 9 or xml for the invariant XML notation, or enter a date/time pattern such as yyyyMMdd (tokens yyyy, yy, MM, dd, HH, mm, ss plus separators).` |
| Value not convertible | `Cannot convert value "%1" to %2 for field "%3".` / `… using input format "%4".` |
| Field validation fails | Business Central's own error |

## Example

```json
{
  "id": "2A4C6E8F-0B1D-4C3E-9F5A-7B9D1F3A5C68",
  "type": "action",
  "action": 5564530,
  "description": "Set Field Values",
  "slug": "SetFieldValues",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/file-pencil.svg",
  "terminating": true,
  "configuration": {
    "tableNo": 36,
    "skipStandard": true,
    "values": [
      { "lineNo": 10000, "fieldNo": 120, "value": "Pending Approval", "validate": false }
    ]
  },
  "outputs": []
}
```

(In a *When a document is released* flow, this sets the Sales Header status to *Pending Approval* instead of releasing.)

## Gotchas

- Always the **last** step of its path (`"terminating": true`). Use it at the end of each branch that should change the document.
- The picker offers it only in the four interactive document flows. Don't use it in other flows.
- The editor fills `tableNo` from the trigger output only for the supported document tables (18, 23, 27, 36, 37, 38, 39, 167, 1001, 1003, 5050, 8052, 8062). The runtime ignores `tableNo`.
- Use `validate: false` for fields such as *Status*, whose validation would block a direct change.
