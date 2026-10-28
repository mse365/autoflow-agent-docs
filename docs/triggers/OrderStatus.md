# When an order status is updated

[← All triggers](README.md) · [Supplier Foundation overview](../apps/SupplierFoundation.md)

Runs for each purchase order whose status the user updates from the supplier. Use it to ask the supplier where the order stands, set the Supplier Order Status, and create a supplier document for every new order confirmation or delivery note.

| | |
|---|---|
| Enum name | `OrderStatus` (AL: `mse365 AF-SF OrderStatus`) |
| Ordinal | `"trigger": 5564017` |
| Category | AutoFlow Supplier Foundation |
| Terminating | n/a (trigger) |
| Group / edges | no |
| Availability | Requires the **AutoFlow Supplier Foundation** app. |

## Where it fires

- **Update order status** on the Purchase Order and the Purchase Order List (every selected order; only document type Order).

## What it does

One run per order, inline, one transaction per order, committed before the next one. An error stops at that order.

Supplier Foundation writes nothing by itself. The flow sets *Supplier Order Status* (field `5564013`) and *Order Status Updated At* (`5564014`) and inserts supplier documents (tables `5564013` header, `5564014` lines). A user then accepts or rejects each document, which fires [When a supplier document is accepted](DocAccepted.md) or [rejected](DocRejected.md).

See [how Supplier Foundation flows run](../apps/SupplierFoundation.md#how-the-flows-run) for the transaction and timeout rules the inline Supplier Foundation triggers share.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `timeoutSec` | integer | yes | `60` | How long the user waits at most. Checked between steps; when it has passed, the run fails and is rolled back. Missing or `0` or less means 60. Keep it between 1 and 600. |

There is nothing else to configure: no table, no filters. The record comes from the page action.

## Outputs

| name | type | tableNo | set | notes |
|---|---|---|---|---|
| `PurchaseHeader` | reference | 38 | always | The purchase order. |
| `VendorNo` | value | – | always | The order's Buy-from Vendor No. |

Reference them as `{{trigger_PurchaseHeader}}`, `{{trigger_VendorNo}}` and so on. Declare **all** of them in `outputs`, as listed; the editor does the same.

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
  "id": "5A1F0C2E-7B3D-4E8A-9C1F-2D3E4F5A6B06",
  "type": "trigger",
  "trigger": 5564017,
  "description": "When an order status is updated",
  "slug": "trigger",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/af-sf-order-status.svg",
  "configuration": {
    "timeoutSec": 60
  },
  "outputs": [
    { "name": "PurchaseHeader", "type": "reference", "tableNo": 38 },
    { "name": "VendorNo", "type": "value" }
  ],
  "level": 0
}
```

## Gotchas

- Avoid duplicate supplier documents: before inserting, **Find Records** on table `5564013` with Vendor No. and Vendor Document No. (field `6`) and skip when one exists.
- Supplier document header: leave *Entry No.* (field 1) out, it is an AutoIncrement. Insert Record's `rec` output then holds the new number: `{{InsertDoc_rec.entryno}}` for the lines' *Document Entry No.* (field 1). *Status* is set to New automatically; do not write it.
- Link each document line to the order line it answers with *Purchase Order Line No.* (field `3`); the accept flow needs it.
- The flow runs while the user waits. A Sleep step fails it, and a slow HTTP call counts against `timeoutSec`.
- Add search result is not offered for this trigger, and does nothing here.
