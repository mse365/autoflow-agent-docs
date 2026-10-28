# When a purchase order is sent

[← All triggers](README.md) · [Supplier Foundation overview](../apps/SupplierFoundation.md)

Runs for each purchase order the user sends to the supplier. Use it to transmit the order (the supplier's API, e-mail, EDI) and record how it went on the order.

| | |
|---|---|
| Enum name | `POSent` (AL: `mse365 AF-SF POSent`) |
| Ordinal | `"trigger": 5564016` |
| Category | AutoFlow Supplier Foundation |
| Terminating | n/a (trigger) |
| Group / edges | no |
| Availability | Requires the **AutoFlow Supplier Foundation** app. |

## Where it fires

- **Send to supplier** on the Purchase Order and the Purchase Order List (every selected order; only document type Order).

## What it does

One run per order. Every flow on this trigger runs inline, in one transaction per order, committed before the next one. An error stops at that order: its changes are rolled back, earlier orders keep theirs.

Supplier Foundation itself writes nothing to the order. Record the result in the flow: *Sent Via* (field `5564012`, Text[50]), *Supplier Order Status* (`5564013`, e.g. `Sent`) and *Order Status Updated At* (`5564014`).

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
  "id": "5A1F0C2E-7B3D-4E8A-9C1F-2D3E4F5A6B05",
  "type": "trigger",
  "trigger": 5564016,
  "description": "When a purchase order is sent",
  "slug": "trigger",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/af-sf-po-send.svg",
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

- The order's lines are not an output. Find them with **Find Records** on table 39 filtered on Document Type = Order and Document No. = `{{trigger_PurchaseHeader.no}}`, or with a `smartFieldDefs` relation.
- If the transmission fails, end with an **Error** step. The order then stays unchanged and the user sees why.
- The flow runs while the user waits. A Sleep step fails it, and a slow HTTP call counts against `timeoutSec`.
- Add search result is not offered for this trigger, and does nothing here.
