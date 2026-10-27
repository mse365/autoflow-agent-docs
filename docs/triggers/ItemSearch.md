# When an item search is performed

[← All triggers](README.md) · [Supplier Foundation overview](../apps/SupplierFoundation.md)

Runs while the user searches for supplier items. The flow asks the supplier for items that match `Query` and adds every hit with [Add search result](../actions/AddSearchResult.md). The user sees the hits in a list under the search field.

| | |
|---|---|
| Enum name | `ItemSearch` (AL: `mse365 AF-SF ItemSearch`) |
| Ordinal | `"trigger": 5564012` |
| Category | AutoFlow Supplier Foundation |
| Terminating | n/a (trigger) |
| Group / edges | no |
| Availability | Requires the **AutoFlow Supplier Foundation** app. |

## Where it fires

- **Search supplier items** on Sales Quote, Sales Order and Sales Invoice, and on their lines: `Context` = `SalesDocument`, `SalesHeader` = the document.
- **Search supplier items** on the Item List: `Context` = `ItemList`, no `SalesHeader`.

## What it does

The action opens the *Search Supplier Items* dialog. Each time the user enters a search text (Enter), every flow published on this trigger runs once, inline, while the dialog waits. An empty search text runs nothing.

The results of all flows are combined into one list. Columns that no result fills are hidden; Description is always shown. After the flows have finished, the search is committed, so the execution entries are kept.

When the user picks a row and confirms with OK, the dialog closes and [When a search result is selected](SearchSelected.md) fires for that row.

If a flow raises an error (for example an **Error** step after a failed HTTP call), the user sees the flow's message and the search shows nothing.

See [how Supplier Foundation flows run](../apps/SupplierFoundation.md#how-the-flows-run) for the transaction and timeout rules all eight triggers share.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `timeoutSec` | integer | yes | `30` | How long the user waits at most. Checked between steps; when it has passed, the run fails and is rolled back. Missing or `0` or less means 30. Keep it between 1 and 600. |

There is nothing else to configure: no table, no filters. The record comes from the page action.

## Outputs

| name | type | tableNo | set | notes |
|---|---|---|---|---|
| `Query` | value | – | always | The search text, trimmed. |
| `Context` | value | – | always | `SalesDocument` or `ItemList` (value name, not translated). |
| `SalesHeader` | reference | 36 | only when started from a sales document | The Sales Header the search was started from. |

Reference them as `{{trigger_Query}}`, `{{trigger_SalesHeader}}` and so on. Declare **all** of them in `outputs`, as listed; the editor does the same.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | timeout empty | Please fill in the highlighted fields. |
| publish | – | no trigger-specific checks | – |

## Runtime errors

| condition | message |
|---|---|
| the flows run longer than `timeoutSec` | The flow %1 did not finish within %2 seconds and was stopped. Nothing it did has been kept. |
| a Sleep step runs | Step %1 (%2) requested a deferred resume, but the flow is running synchronously. Use Sleep or other time-based deferral steps only outside of synchronous frames (Webhook sync phase or SubFlow body). |
| any error in the flow | The flow's own message. This record's run is rolled back and the action stops here. |

`%1` in the timeout message is the flow number, `%2` the timeout.

## Example

```json
{
  "id": "5A1F0C2E-7B3D-4E8A-9C1F-2D3E4F5A6B01",
  "type": "trigger",
  "trigger": 5564012,
  "description": "When an item search is performed",
  "slug": "trigger",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/af-sf-search.svg",
  "configuration": {
    "timeoutSec": 30
  },
  "outputs": [
    { "name": "Query", "type": "value" },
    { "name": "Context", "type": "value" },
    { "name": "SalesHeader", "type": "reference", "tableNo": 36 }
  ],
  "level": 0
}
```

Default `timeoutSec` is 30 for this trigger.

## Gotchas

- The user waits for this flow. Fetch only what is needed to **show** a result; leave the rest to the selection flow and pass what it needs in the step's `payload`.
- Do not write to the database here. Everything the flow writes is committed after the search, even though the user may never pick a result.
- Several suppliers: one search flow per supplier works well. Their results are combined; `vendorNo` on each result tells them apart.
- When the search was started from the Item List, `{{trigger_SalesHeader}}` is not set and stays in text verbatim. Branch on `{{trigger_Context}}` instead.
- The flow runs while the user waits. A Sleep step fails it, and a slow HTTP call counts against `timeoutSec`.
