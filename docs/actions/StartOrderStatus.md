# Start order status update

[← All actions](README.md) · [Supplier Foundation overview](../apps/SupplierFoundation.md)

Starts [When an order status is updated](../triggers/OrderStatus.md) for one purchase order, from any other flow, as the page action *Update order status* does. The flows run in the background; this flow continues at once.

| | |
|---|---|
| Enum name | `StartOrderStatus` (AL: `mse365 AF-SF StartOrderStatus`) |
| Ordinal | `"action": 5564018` |
| Category | AutoFlow Supplier Foundation |
| Terminating | `false` |
| Group / edges | No |
| Availability | Requires the **AutoFlow Supplier Foundation** app. Offered for every trigger. |

One of four steps that start the Supplier Foundation actions from a flow; the others are [Start price and availability update](StartPriceUpdate.md), [Start item update](StartItemUpdate.md), [Start sending purchase order](StartPOSend.md).

## What it does

The step resolves `reference` to a record. It must be a Purchase Header of document type Order (a quote is not sent). Then every flow published on When an order status is updated (`"trigger": 5564017`) is **queued** for that record: each gets its own execution with a Job Queue entry and the same trigger outputs the page action would give it. The step does not wait for them, shows no progress window and does not see whether they succeed. Follow them in the AutoFlow executions.

- The flow that contains this step is never queued, so a flow on that trigger cannot start itself over and over. The other flows on the trigger are started.
- With no (other) flow published on the trigger, nothing happens: `FlowsQueued` is `0` and an Info entry "No flow is published for "%1" - nothing was started." is logged.
- Otherwise it logs "%1 flow(s) started for %2."

The queued runs are ordinary background runs: commit per step, no timeout, Sleep allowed, and a failed run keeps the work of the steps before the error.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `reference` | string | yes | `""` | The purchase order as one SmartField placeholder, e.g. `{{trigger_PurchaseHeader}}`, `{{FindOrders_results}}` or a For Each's current record. Resolved like [Modify Record](ModifyRecord.md)'s `reference`. |

## Outputs

| name | type | tableNo | set | notes |
|---|---|---|---|---|
| `FlowsQueued` | value | – | always | How many flows were queued, e.g. `2`. `0` when none is published (apart from this flow). |

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `reference` empty | Please fill in the highlighted fields. |

There are no publish-time checks.

## Runtime errors

| condition | message |
|---|---|
| `reference` is not a placeholder, or does not resolve to a record | Reference "%1" cannot be resolved to a record. |
| the record is not a purchase order | The record of "%1" must be a purchase order. (`%1` = the step's caption) |
| the record no longer exists | Business Central's own error |

## Example

```json
{
  "id": "4D2B4018-6E1F-4A3C-9B5D-7E8F9A0B1C18",
  "type": "action",
  "action": 5564018,
  "description": "Start order status update",
  "slug": "Start",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/af-sf-start-order-status.svg",
  "terminating": false,
  "configuration": {
    "reference": "{{trigger_PurchaseHeader}}"
  },
  "outputs": [
    { "name": "FlowsQueued", "type": "value" }
  ]
}
```

## Gotchas

- Flows on this trigger otherwise run inline; started by this step they run queued (commit per step, no timeout). Typical use: a scheduled flow that loops over open purchase orders.
- Business Central starts a Job Queue entry only after the transaction that created it commits. In a background flow that happens right after this step. In an inline flow (an interactive document trigger, or an inline Supplier Foundation trigger) it happens when the caller's transaction commits, and if that transaction is rolled back, nothing is started.
- Only the calling flow is excluded. Two flows that start each other's triggers (a flow on one trigger starting the other, and back) keep starting each other.
- To start it for many purchase orders, put the step in a **For Each** over a Find Records result. Each iteration queues its own runs.
