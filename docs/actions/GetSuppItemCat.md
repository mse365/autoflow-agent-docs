# Get supplier item category

[← All actions](README.md) · [Supplier Foundation overview](../apps/SupplierFoundation.md)

Finds the item template and the item category for one of a supplier's categories, from the supplier item categories of a supplier code.

| | |
|---|---|
| Enum name | `GetSuppItemCat` (AL: `mse365 AF-SF GetSuppItemCat`) |
| Ordinal | `"action": 5564013` |
| Category | AutoFlow Supplier Foundation |
| Terminating | `false` |
| Group / edges | No |
| Availability | Requires the **AutoFlow Supplier Foundation** app. Offered for every trigger. |

## What it does

Typically used when a flow imports a supplier item: the supplier says the item is in "Gaming laptops", and the step says which item template to create the item from and which item category to put it in. The mapping is set up per [supplier code](../apps/SupplierFoundation.md#supplier-codes) as a tree of [supplier item categories](../apps/SupplierFoundation.md#supplier-item-categories-table-5564017).

1. The supplier code is looked up (trimmed, upper-cased). If it is not set up, the step fails.
2. The category is looked up among that supplier code's categories: first as a **code** (upper-cased), then as a **name** (exact text). With several categories of the same name, the one with the lowest code wins.
3. From that category, the step takes its Item Template Code and Item Category Code. Each value that is still empty is taken from the parent, then the parent's parent, and so on, until both are filled or the top is reached. Each value comes from the **nearest** category that has one.
4. What is still empty after that comes from the supplier code's **Default Item Template Code** and **Default Item Category Code**.

When `category` is empty or not found, both values come from the defaults. A category that is not found also writes an Info entry to the execution log.

The step only reads; it writes nothing.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `supplierCode` | string | yes | `""` | The supplier code, as set up on the *Supplier Codes* page, e.g. `ACME`. SmartText. |
| `category` | string | no | `""` | The supplier's category of the item: its code or its name. SmartText, usually from the supplier's data. |

## Outputs

| name | type | tableNo | set | notes |
|---|---|---|---|---|
| `ItemTemplateCode` | value | – | always (may be empty) | Code of an Item Templ. |
| `ItemCategoryCode` | value | – | always (may be empty) | Code of an Item Category. |
| `ItemTemplate` | reference | 1382 | only when `ItemTemplateCode` is set and exists | The Item Templ. record. |
| `ItemCategory` | reference | 5722 | only when `ItemCategoryCode` is set and exists | The Item Category record. |
| `CategoryFound` | value | – | always | `true` when the supplier's category was found, `false` when the defaults were used because it was empty or not found. |

Declare all five in `outputs`, in this order.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `supplierCode` empty | Please fill in the highlighted fields. |

There are no publish-time checks.

## Runtime errors

| condition | message |
|---|---|
| `supplierCode` empty, longer than 20 characters, or not set up | The supplier code %1 is not set up. Add it on the Supplier Codes page. |
| `category` given but not found (Info log entry, no error) | Supplier category %1 of %2 was not found - the supplier code's defaults are used. |

## Example

With a Parser step `Hit` that read the supplier's category:

```json
{
  "id": "0C8E2B57-3F1D-4A6E-9B2C-7D4E5F6A1B02",
  "type": "action",
  "action": 5564013,
  "description": "Get supplier item category",
  "slug": "Category",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/af-sf-category.svg",
  "terminating": false,
  "configuration": {
    "supplierCode": "ACME",
    "category": "{{Hit_category}}"
  },
  "outputs": [
    { "name": "ItemTemplateCode", "type": "value" },
    { "name": "ItemCategoryCode", "type": "value" },
    { "name": "ItemTemplate", "type": "reference", "tableNo": 1382 },
    { "name": "ItemCategory", "type": "reference", "tableNo": 5722 },
    { "name": "CategoryFound", "type": "value" }
  ]
}
```

Then set the new item's *Item Category Code* (Item field `5702`) to `{{Category_ItemCategoryCode}}` in Insert Record. A complete import flow is in [examples/supplier-import-selected.json](../../examples/supplier-import-selected.json).

## Gotchas

- `ItemTemplateCode` is an **Item Templ.** (table 1382). [Insert Record](InsertRecord.md) on Item accepts an Item Templ. code in `templateCode`, but only a **fixed** code: the editor treats the key as a plain `Code[20]`, not SmartText, so saving the step cuts `{{Category_ItemTemplateCode}}` to 20 characters and upper-cases it (the validator warns). To use the template this step found, copy its fields into `values` rows. Item Templ. uses the same field numbers as Item: `{{Category_ItemTemplate.genprodpostinggroup}}` into field `91`, `vatprodpostinggroup` into `99`, `inventorypostinggroup` into `11`.
- `ItemTemplate` and `ItemCategory` are not set when their code is empty, and a `{{Category_ItemTemplate.…}}` token then stays in the text verbatim, which makes a validated field fail. Set the supplier code's defaults, or branch on `{{Category_ItemTemplateCode}} != ''` first.
- An unknown supplier code stops the flow. An unknown category does not: it falls back to the defaults. Check `{{Category_CategoryFound}}` if the flow must notice that.
- Pass the category the way the tree was filled: if the tree holds the supplier's ids, pass the id; names are compared exactly.
