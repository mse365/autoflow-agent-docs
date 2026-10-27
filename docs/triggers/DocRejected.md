# When a supplier document is rejected

[← All triggers](README.md) · [Supplier Foundation overview](../apps/SupplierFoundation.md)

Runs when the user rejects a supplier document. Use it to react per `DocumentType`, for example by telling the supplier or by notifying the buyer.

| | |
|---|---|
| Enum name | `DocRejected` (AL: `mse365 AF-SF DocRejected`) |
| Ordinal | `"trigger": 5564019` |
| Category | AutoFlow Supplier Foundation |
| Terminating | n/a (trigger) |
| Group / edges | no |
| Availability | Requires the **AutoFlow Supplier Foundation** app. |

## Where it fires

- **Reject** on the *Supplier Documents* list (every selected document) and on the *Supplier Document* card.

## What it does

Only documents with status New can be rejected; any other status raises "Supplier document %1 is already %2. Only new supplier documents can be accepted or rejected."

Every flow on this trigger runs inline. When they succeed, the document is set to Rejected, with *Status Changed At* and *Status Changed By*, in the same transaction, committed per document. If a flow fails, the document stays New.

Reject also works when no flow is published.

See [how Supplier Foundation flows run](../apps/SupplierFoundation.md#how-the-flows-run) for the transaction and timeout rules all eight triggers share.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `timeoutSec` | integer | yes | `60` | How long the user waits at most. Checked between steps; when it has passed, the run fails and is rolled back. Missing or `0` or less means 60. Keep it between 1 and 600. |

There is nothing else to configure: no table, no filters. The record comes from the page action.

## Outputs

| name | type | tableNo | set | notes |
|---|---|---|---|---|
| `SupplierDocument` | reference | 5564013 | always | The supplier document header. |
| `PurchaseHeader` | reference | 38 | only when the document's Purchase Order No. names an existing order | The purchase order. |
| `DocumentType` | value | – | always | `OrderConfirmation` or `DeliveryNote`. |
| `VendorNo` | value | – | always (may be empty) | The document's Vendor No. |

Reference them as `{{trigger_SupplierDocument}}`, `{{trigger_VendorNo}}` and so on. Declare **all** of them in `outputs`, as listed; the editor does the same.

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
| the document is not New | Supplier document %1 is already %2. Only new supplier documents can be accepted or rejected. |

`%1` in the timeout message is the flow number, `%2` the timeout.

## Example

```json
{
  "id": "5A1F0C2E-7B3D-4E8A-9C1F-2D3E4F5A6B08",
  "type": "trigger",
  "trigger": 5564019,
  "description": "When a supplier document is rejected",
  "slug": "trigger",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/af-sf-doc-reject.svg",
  "configuration": {
    "timeoutSec": 60
  },
  "outputs": [
    { "name": "SupplierDocument", "type": "reference", "tableNo": 5564013 },
    { "name": "PurchaseHeader", "type": "reference", "tableNo": 38 },
    { "name": "DocumentType", "type": "value" },
    { "name": "VendorNo", "type": "value" }
  ],
  "level": 0
}
```

## Gotchas

- The document's *Comment* (field `14`, Text[250]) is a good place for a reason; read it as `{{trigger_SupplierDocument.comment}}`.
- Do not set the document's Status yourself.
- The flow runs while the user waits. A Sleep step fails it, and a slow HTTP call counts against `timeoutSec`.
- Add search result is not offered for this trigger, and does nothing here.
