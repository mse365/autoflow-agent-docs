# When an item is updated

[← All triggers](README.md) · [Supplier Foundation overview](../apps/SupplierFoundation.md)

Runs for each item the user updates from the supplier. Use it to fetch the item's current master data from the supplier and write it to the Item and its Item Vendor entry.

| | |
|---|---|
| Enum name | `ItemUpdate` (AL: `mse365 AF-SF ItemUpdate`) |
| Ordinal | `"trigger": 5564014` |
| Category | AutoFlow Supplier Foundation |
| Terminating | n/a (trigger) |
| Group / edges | no |
| Availability | Requires the **AutoFlow Supplier Foundation** app. |

## Where it fires

- **Update from supplier** on the Item Card (that item) and the Item List (every selected item).
- The step [Start item update](../actions/StartItemUpdate.md) in any other flow, for one item (queued, see below).

## What it does

One run per item. For each item, every flow on this trigger runs inline, in the user's session, in one transaction that is committed before the next item. An error stops at that item: its changes are rolled back, the items before it keep theirs, and the user sees the flow's message.

**Started by a step, the run is queued instead.** [Start item update](../actions/StartItemUpdate.md) in another flow queues this trigger's flows for one item in the background, like the price update: commit per step, no timeout, Sleep allowed, and a failed run keeps the work of the steps before the error. Nobody waits for it and no message reaches a user; check the executions. A flow on this trigger can therefore run either way. Write it so that both are fine: no Sleep, and the writes that mark success last.

The vendor is the item's *Vendor No.* The Item Vendor entry is the one for that vendor without a variant code.

See [how Supplier Foundation flows run](../apps/SupplierFoundation.md#how-the-flows-run) for the transaction and timeout rules the inline Supplier Foundation triggers share.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `timeoutSec` | integer | yes | `60` | How long the user waits at most. Checked between steps; when it has passed, the run fails and is rolled back. Missing or `0` or less means 60. Keep it between 1 and 600. |

There is nothing else to configure: no table, no filters. The record comes from the page action.

## Outputs

| name | type | tableNo | set | notes |
|---|---|---|---|---|
| `Item` | reference | 27 | always | The item. |
| `ItemVendor` | reference | 99 | only when the item's vendor has an Item Vendor entry | Item Vendor entry of the item's Vendor No. (blank variant). |
| `VendorNo` | value | – | only when the item has a Vendor No. | The item's Vendor No. |

Reference them as `{{trigger_Item}}`, `{{trigger_VendorNo}}` and so on. Declare **all** of them in `outputs`, as listed; the editor does the same.

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
  "id": "5A1F0C2E-7B3D-4E8A-9C1F-2D3E4F5A6B03",
  "type": "trigger",
  "trigger": 5564014,
  "description": "When an item is updated",
  "slug": "trigger",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/af-sf-item-update.svg",
  "configuration": {
    "timeoutSec": 60
  },
  "outputs": [
    { "name": "Item", "type": "reference", "tableNo": 27 },
    { "name": "ItemVendor", "type": "reference", "tableNo": 99 },
    { "name": "VendorNo", "type": "value" }
  ],
  "level": 0
}
```

## Gotchas

- Items without a *Vendor No.* still fire the flow, without `VendorNo` and `ItemVendor`. Check `{{trigger_Item.vendorno}} != ''` first.
- The supplier's item number is on the Item Vendor entry: `{{trigger_ItemVendor.vendoritemno}}`, or `{{trigger_Item.vendoritemno}}` on the item itself.
- The flow runs while the user waits. A Sleep step fails it, and a slow HTTP call counts against `timeoutSec`.
- Add search result is not offered for this trigger, and does nothing here.
