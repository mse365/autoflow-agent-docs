# When manually started

[← All triggers](README.md)

Starts the flow on demand: from the flow itself, from another flow (Start flow step), from a "Start Flow" action on standard pages, or from an extension, optionally on one record of a table.

| | |
|---|---|
| Enum name | `Manual` |
| Ordinal | `"trigger": 100` |
| Category | Base |
| Terminating | n/a (trigger) |
| Group / edges | no |
| Availability | GA. Publishing requires a **Code** on the flow card. |

## What it does

Every start creates one pending execution and its own Job Queue entry in the caller's transaction (one execution per record when the flow runs on a table). Interactive starts (flow card, Flow Workspace, page action) then commit and follow the run in a wait dialog. Extensions starting the flow choose a mode: wait with dialog, wait silently, fire and forget (nothing committed, runs once the caller commits), or inline (commits, then runs the whole flow in the caller's session with no Job Queue). Queued runs commit after every step. No recurring Job Queue entry is created on publish.

When `tableNo` is set, starting from the flow card shows a filter page for that table and starts one execution per matching record. With more than one record you are asked to confirm.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `tableNo` | integer | no | `0` | Table the flow runs on. `0` means standalone, with no record. When set, every start must pass exactly one record of this table. |
| `openExecution` | integer | no | `0` | When to open the execution card after a run that a user waited for: `0` Never (you are offered to open a failed run), `1` On error, `2` Always. Unknown values act as `0`. |
| `pages` | array of integer | no | `[]` | Page numbers that offer this flow through their **Start Flow** action. Only supported pages are allowed (see Gotchas). For a record-based flow, each page must show records of `tableNo`. |

None of these keys supports SmartText. They are literal values.

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `Rec` | reference | `tableNo` | Only when `tableNo` ≠ 0. The record the run was started for. |

Reference it as `{{trigger_Rec}}`. Fields of the record are read like any other reference output, see [references-and-smart-fields.md](../references-and-smart-fields.md).

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| publish | error (hard stop) | `tableNo`, if set, must be an existing table (not checked in the editor) | The table %1 the flow runs on does not exist. |
| publish | error (hard stop) | each page in `pages` must carry the Start Flow action | The page %1 cannot show the "Start Flow" action. |
| publish | error (hard stop) | for a record-based flow, each page must show `tableNo` records | The page %1 shows records of the table %2, but the flow runs on the table %3. |
| publish | error | the flow header needs a Code (not part of the JSON) | Enter a Code on the flow card before publishing this flow. Manual flows are started from other flows and from extensions by their Code. |
| editor | error | the two page rules, shown live in the config status line | (same texts) |

Trigger errors are reported as `This flow's trigger cannot be published:` followed by the list.

## Runtime errors

| condition | message |
|---|---|
| flow not published | The flow %1 is not active. Publish it before starting it. |
| flow's trigger is not Manual | The flow %1 cannot be started this way, because it is not started by the trigger "When manually started". |
| record-based flow started without record | The flow %1 runs on a record of the table %2. Pass a record to start it. |
| standalone flow started with record | The flow %1 does not run on a record. Start it without one. |
| record of the wrong table | The flow %1 runs on records of the table %2, not of the table %3. |
| started from an unsaved card | Save the record before starting a flow on it. |
| inline mode, flow deferred itself (e.g. Sleep) | The flow stopped before its end and cannot continue when it runs in this session. |

## Example

```json
{
  "id": "6B1E2F3A-4C5D-4E6F-8A9B-0C1D2E3F4A5B",
  "type": "trigger",
  "trigger": 100,
  "description": "When manually started on a Customer",
  "slug": "trigger",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/hand-click.svg",
  "configuration": {
    "tableNo": 18,
    "openExecution": 1,
    "pages": [21, 22]
  },
  "outputs": [
    { "name": "Rec", "type": "reference", "tableNo": 18 }
  ],
  "level": 0
}
```

## Gotchas

- Set a **Code** on the flow before publishing. Other flows and extensions start Manual flows by their Code.
- Pages that carry **Start Flow**, as card and list pairs: Sales Quote 41/9300, Sales Order 42/9305, Sales Invoice 43/9301, Sales Credit Memo 44/9302, Sales Return Order 6630/9304, Blanket Sales Order 507/9303, Posted Sales Invoice 132/143, Posted Sales Credit Memo 134/144, Posted Sales Shipment 130/142, Purchase Quote 49/9306, Purchase Order 50/9307, Purchase Invoice 51/9308, Purchase Credit Memo 52/9309, Purchase Return Order 6640/9311, Blanket Purchase Order 509/9310, Posted Purchase Invoice 138/146, Posted Purchase Credit Memo 140/147, Posted Purchase Receipt 136/145, Reminder 434/436, Issued Reminder 438/440, Customer 21/22, Vendor 26/27, Item 30/31, Contact 5050/5052. Extensions can register more pages.
- On a list page the flow starts once per selected record.
- In the Step Selector, published Manual flows appear as their own tiles. The generic **Start flow** step is not offered directly.
- Trigger-response steps (Respond to Webhook, Return SubFlow Output, Return PDF, Set report file name, Set document field values, Prevent page close) are hidden in Manual flows.
- A Scheduled flow can also be run once by hand from the flow card. That is a different trigger, though, and is not started by Code.
