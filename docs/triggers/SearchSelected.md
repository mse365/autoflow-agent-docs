# When a search result is selected

[← All triggers](README.md) · [Supplier Foundation overview](../apps/SupplierFoundation.md)

Runs when the user picks one of the item search results and confirms with OK. Use it to import the item: create or update the Item and its Item Vendor entry and, when the search was started from a sales document, add a sales line.

| | |
|---|---|
| Enum name | `SearchSelected` (AL: `mse365 AF-SF SearchSelected`) |
| Ordinal | `"trigger": 5564013` |
| Category | AutoFlow Supplier Foundation |
| Terminating | n/a (trigger) |
| Group / edges | no |
| Availability | Requires the **AutoFlow Supplier Foundation** app. |

## Where it fires

- OK in the *Search Supplier Items* dialog with a result selected. The search was started by **Search supplier items** on a sales document, its lines, or the Item List.

## What it does

Fires once, for the selected row, after the dialog has closed. Every field of the result that the search flow set with [Add search result](../actions/AddSearchResult.md) is an output, plus the search context.

Before the result was shown, Supplier Foundation looked for an Item Vendor entry with the result's Vendor No. and Vendor Item No. If one exists, `ExistingItemNo` holds its Item No. and `Item` points to that item. That is how an item imported earlier is recognised, so make the import flow create that Item Vendor entry.

All flows on this trigger run in one transaction, which is committed at the end. An error rolls back everything they did and shows the flow's message.

See [how Supplier Foundation flows run](../apps/SupplierFoundation.md#how-the-flows-run) for the transaction and timeout rules the inline Supplier Foundation triggers share.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `timeoutSec` | integer | yes | `60` | How long the user waits at most. Checked between steps; when it has passed, the run fails and is rolled back. Missing or `0` or less means 60. Keep it between 1 and 600. |

There is nothing else to configure: no table, no filters. The record comes from the page action.

## Outputs

| name | type | tableNo | set | notes |
|---|---|---|---|---|
| `Query` | value | – | always | The search text the result was found for. |
| `Context` | value | – | always | `SalesDocument` or `ItemList`. |
| `SalesHeader` | reference | 36 | only when started from a sales document | The Sales Header the search was started from. |
| `VendorNo` | value | – | always (may be empty) | As set on the result. |
| `VendorItemNo` | value | – | always (may be empty) |  |
| `Manufacturer` | value | – | always (may be empty) |  |
| `ManufacturerItemNo` | value | – | always (may be empty) |  |
| `GTIN` | value | – | always (may be empty) |  |
| `Description` | value | – | always |  |
| `Description2` | value | – | always (may be empty) |  |
| `UnitOfMeasure` | value | – | always (may be empty) |  |
| `UnitCost` | value | – | always | Invariant decimal, e.g. `12.5`; `0` when not set. |
| `UnitPrice` | value | – | always | Invariant decimal; `0` when not set. |
| `StockAmount` | value | – | always | Invariant decimal; `0` when not set. |
| `StockStatus` | value | – | always (may be empty) | Value name: `InStock`, `LowStock`, `OutOfStock`, `OnOrder`, `Unknown`, or empty. |
| `ImageUrl` | value | – | always (may be empty) |  |
| `Payload` | value | – | always (may be empty) | Exactly the text the search flow put into `payload`. |
| `ExistingItemNo` | value | – | always (may be empty) | Item No. of the item already imported for VendorNo + VendorItemNo, or empty. |
| `Item` | reference | 27 | only when ExistingItemNo is set | The existing item. |

Reference them as `{{trigger_Query}}`, `{{trigger_Item}}` and so on. Declare **all** of them in `outputs`, as listed; the editor does the same.

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
  "id": "5A1F0C2E-7B3D-4E8A-9C1F-2D3E4F5A6B02",
  "type": "trigger",
  "trigger": 5564013,
  "description": "When a search result is selected",
  "slug": "trigger",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/af-sf-search-select.svg",
  "configuration": {
    "timeoutSec": 60
  },
  "outputs": [
    { "name": "Query", "type": "value" },
    { "name": "Context", "type": "value" },
    { "name": "SalesHeader", "type": "reference", "tableNo": 36 },
    { "name": "VendorNo", "type": "value" },
    { "name": "VendorItemNo", "type": "value" },
    { "name": "Manufacturer", "type": "value" },
    { "name": "ManufacturerItemNo", "type": "value" },
    { "name": "GTIN", "type": "value" },
    { "name": "Description", "type": "value" },
    { "name": "Description2", "type": "value" },
    { "name": "UnitOfMeasure", "type": "value" },
    { "name": "UnitCost", "type": "value" },
    { "name": "UnitPrice", "type": "value" },
    { "name": "StockAmount", "type": "value" },
    { "name": "StockStatus", "type": "value" },
    { "name": "ImageUrl", "type": "value" },
    { "name": "Payload", "type": "value" },
    { "name": "ExistingItemNo", "type": "value" },
    { "name": "Item", "type": "reference", "tableNo": 27 }
  ],
  "level": 0
}
```

## Gotchas

- `UnitCost`, `UnitPrice` and `StockAmount` are invariant numbers (`1234.5`). When you write them to a field, set `"inputFormat": "9"` on the values row, or a German session reads `12.5` as 125.
- Branch on `{{trigger_ExistingItemNo}} = ''` (new item) rather than on `{{trigger_Item}}`, which is not set for a new item and then stays verbatim.
- Create the Item Vendor entry (table 99: Vendor No., Item No., Vendor Item No.) when you create the item. Without it the next search does not recognise the item and the flow would create a duplicate.
- On a sales line created from here, set *Supplier No.* (field `5564012` of Sales Line) to `{{trigger_VendorNo}}`, so a later price update asks the same supplier.
- `Payload` arrives as text. To read fields from a JSON payload, run a **Parser** step on `{{trigger_Payload}}`.
- The flow runs while the user waits. A Sleep step fails it, and a slow HTTP call counts against `timeoutSec`.
- Add search result is not offered for this trigger, and does nothing here.
