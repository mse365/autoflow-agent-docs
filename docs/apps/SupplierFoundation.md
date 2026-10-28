# AutoFlow Supplier Foundation

**AutoFlow Supplier Foundation** is a separate Business Central app on top of AutoFlow. It adds page actions for supplier work (search supplier items, update items and prices, send purchase orders, track order status, accept supplier documents) and fires a trigger for each of them. **The flows do the supplier-specific work**: Supplier Foundation knows no supplier, API or file format. It brings the actions, the triggers, two steps, the fields and tables the flows write to, and setup tables that tell the flows which vendor a supplier is and how the supplier's categories map to item templates and item categories.

Use this page to understand how the pieces fit together. Each trigger and step has its own reference page.

## Requirements

- The **AutoFlow Supplier Foundation** app installed, together with AutoFlow and AutoFlow Core. It is newer than the AutoFlow 27.0.40 these docs are verified against and needs the AutoFlow release that ships with it.
- The flows below are ordinary flows: import them with *Create from file* and publish them like any other. They count towards the flow license like any other flow.
- Status: **preview**. The steps documented here may still change before the app is released.

## What fires what

| Page action | Pages | Trigger | `"trigger"` | Runs |
|---|---|---|---|---|
| **Search supplier items** | Sales Quote, Sales Order, Sales Invoice and their lines; Item List | [When an item search is performed](../triggers/ItemSearch.md) | `5564012` | for each search text the user enters |
| (OK in the search dialog) | – | [When a search result is selected](../triggers/SearchSelected.md) | `5564013` | once, for the picked result |
| **Update from supplier** | Item Card, Item List | [When an item is updated](../triggers/ItemUpdate.md) | `5564014` | per item |
| **Update price and availability** | Sales and purchase quotes, orders and invoices (all item lines) and their line subforms (selected lines); Item Card, Item List | [When a price update is requested](../triggers/PriceUpdate.md) | `5564015` | per item line or item |
| **Send to supplier** | Purchase Order, Purchase Order List | [When a purchase order is sent](../triggers/POSent.md) | `5564016` | per order |
| **Update order status** | Purchase Order, Purchase Order List | [When an order status is updated](../triggers/OrderStatus.md) | `5564017` | per order |
| **Accept** | Supplier Documents, Supplier Document | [When a supplier document is accepted](../triggers/DocAccepted.md) | `5564018` | per document |
| **Reject** | Supplier Documents, Supplier Document | [When a supplier document is rejected](../triggers/DocRejected.md) | `5564019` | per document |

A page action is shown only while at least one flow is published on its trigger. Accept and Reject are always shown: accepting is the user's decision, and the flows only add what should happen because of it.

The two action steps:

- [Add search result](../actions/AddSearchResult.md) (`"action": 5564012`). The step picker offers it only in flows on When an item search is performed.
- [Get supplier item category](../actions/GetSuppItemCat.md) (`"action": 5564013`) maps a supplier's category to an item template and an item category. Offered for every trigger.

## How the flows run

All eight triggers share these rules.

- **Inline, while the user waits.** The page action fires the trigger for one record at a time. Every flow published on the trigger runs in the user's session, one after the other, with the same outputs. There is no Job Queue entry and no background run.
- **One transaction per record.** Nothing is committed while the flows run. The flows for one record, and what Supplier Foundation writes afterwards (the status of a supplier document), are committed together before the next record.
- **An error stops at that record.** Its changes are rolled back, the records before it keep theirs, and the user sees the flow's message. Use an **Error** step to tell the user why something did not work.
- **`timeoutSec`** is the only trigger setting: 30 seconds for the item search, 60 for the others. It is checked between steps. When it has passed, the run fails with "The flow %1 did not finish within %2 seconds and was stopped. Nothing it did has been kept."
- **No Sleep.** A step that defers the run fails it, as in every synchronous flow.
- **Outputs that don't apply are not set.** For example `SalesHeader` when the search was started from the Item List, or `ItemVendor` when the item has no Item Vendor entry. A `{{trigger_…}}` token for such an output stays in the text verbatim, so branch on an output that is always set (`Context`, `Source`, `DocumentType`, `ExistingItemNo`).
- **No recursion.** A flow that fires its own trigger again (through another page action) is skipped.
- **Enum outputs are value names**, never translated captions: `SalesDocument`, `PurchaseLine`, `OrderConfirmation`, `InStock`. Compare against those, and a flow works in every language.
- **Publish** has no trigger-specific checks.

## Typical flow set for one supplier

| Flow | Trigger | Steps, roughly |
|---|---|---|
| Search | ItemSearch | Find Records (supplier code → vendor) → HTTP Request (supplier search with `{{trigger_Query}}`) → Parser (list of products) → For Each → Parser (one product) → Add search result |
| Import | SearchSelected | Decision on `{{trigger_ExistingItemNo}} = ''` → Parser on `{{trigger_Payload}}` → Get supplier item category → Insert Record Item + Insert Record Item Vendor, or Modify Record `{{trigger_Item}}` → Decision on `{{trigger_Context}} = SalesDocument` → Insert Record Sales Line |
| Item master data | ItemUpdate | HTTP Request → Parser → Modify Record `{{trigger_Item}}` and `{{trigger_ItemVendor}}` |
| Price and stock | PriceUpdate | HTTP Request → Parser → Modify Record `{{trigger_ItemVendor}}` → Case on `{{trigger_Source}}` → Modify Record on the line |
| Send order | POSent | Find Records (order lines) → HTTP Request or Send Email → Modify Record `{{trigger_PurchaseHeader}}` (Sent Via, Order Status = `Sent`) |
| Order status | OrderStatus | HTTP Request → Parser → Modify Record `{{trigger_PurchaseHeader}}` → For Each new confirmation: Insert Record supplier document header + lines |
| Accept | DocAccepted | Case on `{{trigger_DocumentType}}` → Find Records (document lines) → For Each → Modify Record on the purchase line |

With several suppliers, write one search flow per supplier (their results are combined) and branch on `{{trigger_VendorNo}}` in the other flows, or give each its own flow with a Decision on the vendor at the start.

Where a flow needs "its" vendor and no trigger output gives it (the search flow, for `vendorNo` in Add search result), look it up by [supplier code](#supplier-codes) instead of writing a Vendor No. into the flow.

Two complete examples: [examples/supplier-item-search.json](../../examples/supplier-item-search.json) and [examples/supplier-import-selected.json](../../examples/supplier-import-selected.json).

## Supplier codes

A supplier code is a fixed name for a supplier (`ACME`) that a user maps to one of their vendors on the *Supplier Codes* page (also under *Related* on the Vendor Card). Vendor numbers differ from company to company; the supplier code does not, so a flow that looks its vendor up by supplier code works in every company once the code is set up.

### Supplier Code, table `5564016`

| fieldNo | field | type | path name | notes |
|---|---|---|---|---|
| `1` | Supplier Code | Code[20] | `suppliercode` | primary key, not blank |
| `2` | Vendor No. | Code[20] | `vendorno` | relation to Vendor; required |
| `3` | Vendor Name | Text[100] | `vendorname` | FlowField, not calculated by Find Records |
| `4` | Default Item Template Code | Code[20] | `defaultitemtemplatecode` | relation to Item Templ. (1382); used by [Get supplier item category](../actions/GetSuppItemCat.md) when the category tree has none |
| `5` | Default Item Category Code | Code[20] | `defaultitemcategorycode` | relation to Item Category (5722); likewise |

Several codes may point to the same vendor. Deleting a vendor deletes its supplier codes and their item categories; renaming it updates them. Deleting a supplier code with its triggers deletes its item categories.

Read it with **Find Records** on table `5564016`, filtered on field `1`, and use `{{<slug>_results.vendorno}}`:

```json
"configuration": {
  "tableNo": 5564016,
  "filters": [ { "fieldNo": 1, "filter": "ACME" } ],
  "smartFilter": "",
  "limit": 1,
  "errorOnEmpty": false,
  "keyFields": "",
  "ascending": true
}
```

When the code is not set up, `results` is not set and `{{<slug>_results.vendorno}}` stays in the text verbatim. Check `{{<slug>_count}} = 0` with a Decision and stop with an **Error** that tells the user to set the code up, as in [examples/supplier-item-search.json](../../examples/supplier-item-search.json). (`errorOnEmpty: true` also stops the flow, but its message names only the table number.)

Flows normally only read this table. If one writes it, Insert Record and Modify Record with `"triggers": true` fail when Vendor No. is empty.

### Supplier item categories, table `5564017`

The supplier's own category tree, one per supplier code, mapped to item templates and item categories. Users maintain it on the *Supplier Item Categories* page (also *Item Categories* on the Supplier Codes page); a flow can fill it from the supplier's category list. [Get supplier item category](../actions/GetSuppItemCat.md) reads it.

| fieldNo | field | type | path name | notes |
|---|---|---|---|---|
| `1` | Supplier Code | Code[20] | `suppliercode` | key; relation to Supplier Code |
| `2` | Code | Code[50] | `code` | key; the supplier's own id of the category |
| `3` | Name | Text[100] | `name` | the supplier's name of the category |
| `4` | Parent Code | Code[50] | `parentcode` | Code of the parent category of the same supplier code; empty at the top |
| `5` | Level | Integer | `level` | calculated, do not write |
| `6` | Item Template Code | Code[20] | `itemtemplatecode` | relation to Item Templ. (1382); empty = use the nearest parent's |
| `7` | Item Category Code | Code[20] | `itemcategorycode` | relation to Item Category (5722); empty = use the nearest parent's |
| `8` | Sort Path | Text[250] | `sortpath` | calculated, only orders the list as a tree; do not write |

Filling it from a flow with Insert Record:

- Use `"triggers": true`. The insert then calculates Level and Sort Path for the category and for any subcategories already there, so the categories may come in any order: a subcategory before its parent is fine. Without triggers, Level stays 0 and the list does not show the tree.
- Parent Code is not checked against existing categories. With `"validate": true` on its row, a parent that would make the category its own ancestor fails with "Category %1 cannot be a subcategory of itself - %2 is one of its subcategories."
- Validated Item Template Code and Item Category Code must exist.
- A category cannot be renamed, and a category that still has subcategories cannot be deleted ("Category %1 has subcategories. Delete or move them first.").
- To refresh an existing tree, Find Records on table `5564017` with field `1` = the supplier code and field `2` = the id, then Insert or Modify Record. Modify Record with triggers recalculates the tree as well.

## Fields flows write

Supplier Foundation adds these fields to standard tables. It never fills them itself; the flows do. In `values` rows use the **field number**; in `{{…}}` paths use the punctuation-free lower-case name shown.

### Purchase Header (38) and Purchase Header Archive (5109)

| fieldNo | field | type | path name |
|---|---|---|---|
| `5564012` | Sent Via | Text[50] | `mse365afsfsentvia` |
| `5564013` | Supplier Order Status | enum, see below | `mse365afsforderstatus` |
| `5564014` | Order Status Updated At | DateTime | `mse365afsfstatusupdatedat` |

The archive carries the same field numbers, so archiving an order keeps them.

### Item Vendor (99)

| fieldNo | field | type | path name |
|---|---|---|---|
| `5564012` | Supplier Unit Price | Decimal | `mse365afsfunitprice` |
| `5564013` | Supplier Stock | Decimal | `mse365afsfstockamount` |
| `5564014` | Supplier Stock Status | enum Stock Status | `mse365afsfstockstatus` |
| `5564015` | Availability Updated At | DateTime | `mse365afsfavailupdatedat` |

Item Vendor's own key fields are Vendor No. (`2`), Item No. (`1`) and Variant Code (`5700`); Vendor Item No. is `7`. **Vendor No. + Vendor Item No. is how Supplier Foundation recognises an item that was imported before**, so the import flow must create this entry.

### Sales Line (37)

| fieldNo | field | type | path name |
|---|---|---|---|
| `5564012` | Supplier No. | Code[20], relation to Vendor | `mse365afsfvendorno` |
| `5564013` | Supplier Stock | Decimal | `mse365afsfstockamount` |
| `5564014` | Supplier Stock Status | enum Stock Status | `mse365afsfstockstatus` |
| `5564015` | Availability Updated At | DateTime | `mse365afsfavailupdatedat` |

Supplier No. decides which vendor the price update asks for this line; when it is empty, the item's Vendor No. is used.

### Purchase Line (39)

| fieldNo | field | type | path name |
|---|---|---|---|
| `5564012` | Supplier Stock | Decimal | `mse365afsfstockamount` |
| `5564013` | Supplier Stock Status | enum Stock Status | `mse365afsfstockstatus` |
| `5564014` | Availability Updated At | DateTime | `mse365afsfavailupdatedat` |

Note that the field numbers differ between Sales Line and Purchase Line.

## Supplier documents

An order confirmation or delivery note the supplier sent back for a purchase order. The order-status flow inserts them; a user reviews them on the *Supplier Documents* page and accepts or rejects them.

### Supplier Document, table `5564013`

| fieldNo | field | type | notes |
|---|---|---|---|
| `1` | Entry No. | Integer | AutoIncrement. Leave it out of Insert Record; read it back as `{{<slug>_rec.entryno}}`. |
| `2` | Document Type | enum | `OrderConfirmation`, `DeliveryNote` |
| `3` | Status | enum | `New`, `Accepted`, `Rejected`. New on insert; set by Accept/Reject only. Do not write it. |
| `4` | Vendor No. | Code[20] | relation to Vendor |
| `6` | Vendor Document No. | Code[35] | the supplier's number for the document |
| `7` | Document Date | Date | |
| `8` | Purchase Order No. | Code[20] | the purchase order (document type Order) it answers |
| `9` | Expected Receipt Date | Date | |
| `10` | Currency Code | Code[10] | |
| `11` | Received At | DateTime | set to the insert time when left empty (Insert Record with `"triggers": true`) |
| `12` | Status Changed At | DateTime | set by Accept/Reject |
| `13` | Status Changed By | Code[50] | set by Accept/Reject |
| `14` | Comment | Text[250] | |

Field 5 (Vendor Name) is a FlowField. Deleting a document with its triggers deletes its lines.

### Supplier Document Line, table `5564014`

| fieldNo | field | type | notes |
|---|---|---|---|
| `1` | Document Entry No. | Integer | the header's Entry No. |
| `2` | Line No. | Integer | key with field 1; write `10000`, `20000`, … |
| `3` | Purchase Order Line No. | Integer | Line No. of the purchase line it answers |
| `4` | Vendor Item No. | Text[50] | |
| `5` | Item No. | Code[20] | |
| `6` | Description | Text[100] | |
| `7` | Quantity | Decimal | |
| `8` | Unit of Measure Code | Code[10] | |
| `9` | Direct Unit Cost | Decimal | |
| `10` | Expected Receipt Date | Date | |

Path names follow the usual rule: `entryno`, `documenttype`, `purchaseorderno`, `purchaseorderlineno`, `directunitcost`, and so on.

## Enum values

Write enum fields by **value name** in Insert/Modify Record `values` rows (`"value": "Sent"`); the name must match exactly, including case. Triggers emit the same names.

| enum | values (name, ordinal) | extensible |
|---|---|---|
| Supplier Order Status | blank `0`, `Sent` 1, `Confirmed` 2, `PartiallyConfirmed` 3, `PartiallyDelivered` 4, `Delivered` 5, `Rejected` 6, `Cancelled` 7 | yes |
| Stock Status | blank `0`, `InStock` 1, `LowStock` 2, `OutOfStock` 3, `OnOrder` 4, `Unknown` 5 | yes |
| Supplier Document Type | `OrderConfirmation` 0, `DeliveryNote` 1 | yes |
| Supplier Document Status | `New` 0, `Accepted` 1, `Rejected` 2 | no |
| Search Context (output only) | `SalesDocument`, `ItemList` | no |

Extensible enums may have more values in an environment where a supplier-specific app adds them.

## What to tell the user

When you hand over Supplier Foundation flows, list what the environment needs:

- the Supplier Foundation app (and the AutoFlow release it requires),
- the supplier code the flows use (`ACME`), to be mapped to the supplier's vendor on the *Supplier Codes* page, or the Vendor No. if a flow uses one directly,
- the AutoFlow credential (by code) for the supplier's API,
- for flows that use Get supplier item category: the supplier item categories (or a flow that fills them) and the supplier code's Default Item Template Code and Default Item Category Code,
- which flows to publish, and that the page actions appear only once they are published.
