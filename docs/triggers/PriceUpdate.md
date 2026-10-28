# When a price update is requested

[← All triggers](README.md) · [Supplier Foundation overview](../apps/SupplierFoundation.md)

Runs once for each sales line, purchase line or item whose price and availability the user updates. Use it to ask the supplier for price and stock: write the price with [Set supplier price](../actions/SetSupplierPrice.md), and the stock to the line or item and to the Item Vendor entry. Unlike the other Supplier Foundation triggers, its runs are **queued** in the background.

| | |
|---|---|
| Enum name | `PriceUpdate` (AL: `mse365 AF-SF PriceUpdate`) |
| Ordinal | `"trigger": 5564015` |
| Category | AutoFlow Supplier Foundation |
| Terminating | n/a (trigger) |
| Group / edges | no |
| Availability | Requires the **AutoFlow Supplier Foundation** app. |

## Where it fires

- **Update price and availability** on Sales Quote, Sales Order and Sales Invoice: every item line of the document. On their line subforms: the selected lines. `Source` = `SalesLine`.
- The same action on Purchase Quote, Purchase Order and Purchase Invoice and their line subforms. `Source` = `PurchaseLine`.
- The same action on the Item Card and the Item List (selected items). `Source` = `Item`.

## What it does

One run per line or item. Lines that are not of type Item, or have no No., are skipped. If nothing is left, the user sees "There is nothing to update - none of the selected lines is an item."

**Queued, not inline.** For every line or item, each flow published on this trigger gets its own execution with a Job Queue entry, like a manually started flow. The action commits, then shows a progress window: "*n* of *m* done" and the latest execution-log message, which is the step that is running. When all runs have finished, failed ones are reported with the offer to open them. After five minutes the window closes with "The flow is taking longer than expected and keeps running in the background. You can follow it in the AutoFlow executions." If AutoFlow is set to start flows manually, the runs wait until their Job Queue entries are started.

So, unlike the other Supplier Foundation triggers:

- Each run is an ordinary background run: it commits after every step, and a failed run keeps the work of the steps before the error. Runs for different lines are independent; one failing does not stop the others.
- There is no timeout, and **Sleep** works.
- Runs may finish in any order, and may run in parallel.

Which vendor: a sales line uses its *Supplier No.* (field `5564012`), and when that is empty the item's *Vendor No.*; a purchase line uses its *Buy-from Vendor No.*; an item uses its *Vendor No.* The Item Vendor entry is the one for that vendor and the line's variant, or, if there is none, the one without a variant.

The other rules in [how Supplier Foundation flows run](../apps/SupplierFoundation.md#how-the-flows-run) (outputs that don't apply are not set, enum value names) apply here too.

## Configuration

None: write `"configuration": {}`. No table, no filters, no timeout; the record comes from the page action.

**Before** this trigger was queued, it had a `timeoutSec` like the other Supplier Foundation triggers. A flow that still carries it is not rejected; the key is ignored.

## Outputs

| name | type | tableNo | set | notes |
|---|---|---|---|---|
| `Source` | value | – | always | `SalesLine`, `PurchaseLine` or `Item`. |
| `SalesLine` | reference | 37 | only when Source = SalesLine | The sales line. |
| `PurchaseLine` | reference | 39 | only when Source = PurchaseLine | The purchase line. |
| `Item` | reference | 27 | when the item exists | The line's item, or the item itself. |
| `ItemVendor` | reference | 99 | only when an Item Vendor entry exists for the vendor | See *Which vendor* above. |
| `VendorNo` | value | – | only when a vendor was found | The vendor that should be asked. |

Reference them as `{{trigger_Source}}`, `{{trigger_VendorNo}}` and so on. Declare **all** of them in `outputs`, as listed; the editor does the same.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| publish | – | no trigger-specific checks | – |

## Runtime errors

| condition | message |
|---|---|
| any error in the flow | The flow's own message, on the failed execution. The steps before it keep their work; the other lines' runs go on. At the end the user is asked "%1 of %2 executions ended with an error. Do you want to open them?" (one run: "The flow ended with an error. Do you want to open the execution?"). |

## Example

```json
{
  "id": "5A1F0C2E-7B3D-4E8A-9C1F-2D3E4F5A6B04",
  "type": "trigger",
  "trigger": 5564015,
  "description": "When a price update is requested",
  "slug": "trigger",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/af-sf-price.svg",
  "configuration": {},
  "outputs": [
    { "name": "Source", "type": "value" },
    { "name": "SalesLine", "type": "reference", "tableNo": 37 },
    { "name": "PurchaseLine", "type": "reference", "tableNo": 39 },
    { "name": "Item", "type": "reference", "tableNo": 27 },
    { "name": "ItemVendor", "type": "reference", "tableNo": 99 },
    { "name": "VendorNo", "type": "value" }
  ],
  "level": 0
}
```

A complete flow (ask the supplier, Set supplier price, stock on the line) is in [examples/supplier-price-update.json](../../examples/supplier-price-update.json).

## Gotchas

- Branch on `{{trigger_Source}}` (a Decision or a Case) before you touch `SalesLine` or `PurchaseLine`; the other one is not set and stays verbatim.
- Where to write: the **price** with [Set supplier price](../actions/SetSupplierPrice.md) (`supplierCode`, `itemNo` `{{trigger_Item.no}}`, `variantCode`, `unitOfMeasureCode`, `directUnitCost`), into Business Central's purchase prices. The sales and purchase lines show it as *Supplier Price*, calculated by Business Central's price calculation. The **stock** with Modify Record: Item Vendor `5564013` *Supplier Stock*, `5564014` *Supplier Stock Status*, `5564015` *Availability Updated At*; Sales Line `5564013`–`5564015`; Purchase Line `5564012`–`5564014`. There is no supplier price field to write any more. See the [overview](../apps/SupplierFoundation.md#fields-flows-write).
- A Sales Quote action updates every item line, so a quote with 30 lines queues 30 runs per flow. Users who need only some lines can select them on the line subform instead.
- The page does not lock the lines while the runs are queued: the user can change a line before its run gets to it. Read the line's values from `{{trigger_SalesLine.…}}` when the run needs them, not from the time the action started.
- Set supplier price uses a supplier code, not the vendor. With several suppliers, look the supplier code up from `{{trigger_VendorNo}}` with Find Records on table `5564016` (field `2` = Vendor No.).
- Add search result is not offered for this trigger, and does nothing here.
