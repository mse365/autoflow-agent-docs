# When a purchase order is sent

[← All triggers](README.md) · [Supplier Foundation overview](../apps/SupplierFoundation.md)

Runs for each purchase order the user sends to the supplier. Use it to transmit the order (the supplier's API, e-mail, EDI) and record how it went on the order. Like the price update, its runs are **queued** in the background.

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
- The step [Start sending purchase order](../actions/StartPOSend.md) in any other flow, for one order.

## What it does

**Queued, not inline.** For every order, each flow published on this trigger gets its own execution with a Job Queue entry. The action commits, then shows a progress window, "Sending purchase orders to the supplier": "*n* of *m* done" and the latest execution-log message. When all runs have finished, failed ones are reported with the offer to open them. After five minutes the window closes and the runs go on in the background. If AutoFlow is set to start flows manually, the runs wait until their Job Queue entries are started.

Each run is an ordinary background run: it commits after every step, has no timeout, may use Sleep, and a failed run **keeps the work of the steps before the error**. Runs for different orders are independent.

Supplier Foundation itself writes nothing to the order. Record the result in the flow: *Sent Via* (field `5564012`, Text[50]), *Supplier Order Status* (`5564013`, e.g. `Sent`) and *Order Status Updated At* (`5564014`).

The other rules in [how Supplier Foundation flows run](../apps/SupplierFoundation.md#how-the-flows-run) (outputs, enum value names) apply here too.

## Configuration

None: write `"configuration": {}`. No table, no filters, no timeout; the record comes from the page action.

**Before** this trigger was queued, it had a `timeoutSec`. A flow that still carries it is not rejected; the key is ignored.

## Outputs

| name | type | tableNo | set | notes |
|---|---|---|---|---|
| `PurchaseHeader` | reference | 38 | always | The purchase order. |
| `VendorNo` | value | – | always | The order's Buy-from Vendor No. |

Reference them as `{{trigger_PurchaseHeader}}`, `{{trigger_VendorNo}}` and so on. Declare **all** of them in `outputs`, as listed; the editor does the same.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| publish | – | no trigger-specific checks | – |

## Runtime errors

| condition | message |
|---|---|
| any error in the flow | The flow's own message, on the failed execution. The steps before it keep their work; the other orders' runs go on. At the end the user is asked "%1 of %2 executions ended with an error. Do you want to open them?" (one run: "The flow ended with an error. Do you want to open the execution?"). |

## Example

```json
{
  "id": "5A1F0C2E-7B3D-4E8A-9C1F-2D3E4F5A6B05",
  "type": "trigger",
  "trigger": 5564016,
  "description": "When a purchase order is sent",
  "slug": "trigger",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/af-sf-po-send.svg",
  "configuration": {},
  "outputs": [
    { "name": "PurchaseHeader", "type": "reference", "tableNo": 38 },
    { "name": "VendorNo", "type": "value" }
  ],
  "level": 0
}
```

## Gotchas

- The order's lines are not an output. Find them with **Find Records** on table 39 filtered on Document Type = Order and Document No. = `{{trigger_PurchaseHeader.no}}`, or with a `smartFieldDefs` relation.
- If the transmission fails, end with an **Error** step: the progress window reports it with the reason. What the flow wrote **before** the error is kept, so set *Sent Via* and *Supplier Order Status* only after the order went through.
- The user can change the order while its run is queued. Read the order from `{{trigger_PurchaseHeader.…}}` in the run, not from when the action started.
- Add search result is not offered for this trigger, and does nothing here.
