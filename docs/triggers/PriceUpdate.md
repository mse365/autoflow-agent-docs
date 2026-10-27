# When a price update is requested

[← All triggers](README.md) · [Supplier Foundation overview](../apps/SupplierFoundation.md)

Runs once for each sales line, purchase line or item whose price and availability the user updates. Use it to ask the supplier for price and stock and write them to the line or item and to the Item Vendor entry.

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

Every flow on this trigger runs inline, in one transaction per line or item, committed before the next one. An error stops at that line: its changes are rolled back, the lines before it keep theirs.

Which vendor: a sales line uses its *Supplier No.* (field `5564012`), and when that is empty the item's *Vendor No.*; a purchase line uses its *Buy-from Vendor No.*; an item uses its *Vendor No.* The Item Vendor entry is the one for that vendor and the line's variant, or, if there is none, the one without a variant.

See [how Supplier Foundation flows run](../apps/SupplierFoundation.md#how-the-flows-run) for the transaction and timeout rules all eight triggers share.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `timeoutSec` | integer | yes | `60` | How long the user waits at most. Checked between steps; when it has passed, the run fails and is rolled back. Missing or `0` or less means 60. Keep it between 1 and 600. |

There is nothing else to configure: no table, no filters. The record comes from the page action.

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
  "id": "5A1F0C2E-7B3D-4E8A-9C1F-2D3E4F5A6B04",
  "type": "trigger",
  "trigger": 5564015,
  "description": "When a price update is requested",
  "slug": "trigger",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/af-sf-price.svg",
  "configuration": {
    "timeoutSec": 60
  },
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

## Gotchas

- Branch on `{{trigger_Source}}` (a Decision or a Case) before you touch `SalesLine` or `PurchaseLine`; the other one is not set and stays verbatim.
- Where to write: Item Vendor fields `5564012` *Supplier Unit Price*, `5564013` *Supplier Stock*, `5564014` *Supplier Stock Status*, `5564015` *Availability Updated At*. Sales Line `5564013`–`5564015` and Purchase Line `5564012`–`5564014` hold stock, stock status and the update time. See the [overview](../apps/SupplierFoundation.md#fields-flows-write).
- A Sales Quote action updates every item line, so a quote with 30 lines runs the flow 30 times. Keep the flow fast; users who need only some lines can select them on the line subform instead.
- The flow runs while the user waits. A Sleep step fails it, and a slow HTTP call counts against `timeoutSec`.
- Add search result is not offered for this trigger, and does nothing here.
