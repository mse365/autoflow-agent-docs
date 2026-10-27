# Add search result

[← All actions](README.md) · [Supplier Foundation overview](../apps/SupplierFoundation.md)

Adds one item to the results the user sees under the search field of the supplier item search.

| | |
|---|---|
| Enum name | `AddSearchResult` (AL: `mse365 AF-SF AddSearchResult`) |
| Ordinal | `"action": 5564012` |
| Category | AutoFlow Supplier Foundation |
| Terminating | `false` |
| Group / edges | No |
| Availability | Requires the **AutoFlow Supplier Foundation** app. Only useful in a flow on [When an item search is performed](../triggers/ItemSearch.md). |

## What it does

The step reads its configuration (SmartFields already resolved), builds one search result from it and appends it to the results of the search that is running. Call it once for every item the supplier returned, typically inside a **For Each** over the supplier's answer. It is not terminating: the flow continues, and further results can follow.

Before the result is shown, Supplier Foundation looks for an Item Vendor entry with the result's `vendorNo` and `vendorItemNo`. If there is one, the result carries that Item No.; the selection flow receives it as `ExistingItemNo`.

All results of all search flows are shown together. When the user picks one and confirms, [When a search result is selected](../triggers/SearchSelected.md) fires with every field below as an output, and `payload` unchanged.

Outside an item search, for example in a flow on another trigger, the step adds nothing. It writes an Info entry to the execution log and the flow continues.

## Configuration

Every key except `stockStatus` is a SmartText string. Values are trimmed. Text longer than the field is cut without an error.

| key | type | required | default | max | description |
|---|---|---|---|---|---|
| `description` | string | yes | `""` | 100 | What the user sees as the result. |
| `description2` | string | no | `""` | 50 | A second line of description. |
| `vendorNo` | string | no | `""` | 20 | The Business Central **Vendor No.** of the supplier (not the supplier's own id). Upper-cased. |
| `vendorItemNo` | string | no | `""` | 50 | The supplier's item number. With `vendorNo` it identifies an item imported before. |
| `manufacturer` | string | no | `""` | 100 | |
| `manufacturerItemNo` | string | no | `""` | 50 | Manufacturer part number. |
| `gtin` | string | no | `""` | 14 | GTIN (EAN). Upper-cased. |
| `imageUrl` | string | no | `""` | 2048 | A link to a picture of the item. |
| `unitOfMeasure` | string | no | `""` | 10 | The unit the prices refer to. Upper-cased. |
| `unitCost` | string | no | `""` | – | Purchase price the supplier offers. A number, see below. |
| `unitPrice` | string | no | `""` | – | Sales price, for example the recommended retail price. A number. |
| `stockAmount` | string | no | `""` | – | Quantity the supplier has in stock. A number. |
| `stockStatus` | object or string | no | – | – | Enum input, see below. |
| `payload` | string | no | `""` | – | Anything the import needs later: the supplier's product id, or the whole JSON of the hit. Not shown to the user; passed unchanged to the selection flow. |

**Numbers** (`unitCost`, `unitPrice`, `stockAmount`): empty means `0`. `1234.5` and `1234,5` are both read as 1234.5, and a thousands separator next to the decimal one is dropped (`1,234.50`, `1.234,50`). Any other text fails the step (see Runtime errors), so a price is never silently 0.

### `stockStatus`

The values are `InStock`, `LowStock`, `OutOfStock`, `OnOrder` and `Unknown`. An app built on Supplier Foundation can add more. Blank means "not reported".

The editor stores an object with one of three modes:

```json
{ "mode": "fixed", "value": "InStock" }
```

```json
{ "mode": "smarttext", "smartText": "{{Product_availability}}" }
```

```json
{
  "mode": "rules",
  "rules": [
    { "condition": "{{Product_stock}} > 10", "value": "InStock" },
    { "condition": "{{Product_stock}} > 0", "value": "LowStock" }
  ],
  "otherwise": "OutOfStock"
}
```

- **fixed**: `value` is a value name.
- **smarttext**: the resolved text may be the value name (`InStock`), its caption in the user's language (`In Stock`) or its number, case-insensitive. Any other non-empty text becomes `Unknown`. A plain string instead of an object (`"stockStatus": "{{Product_availability}}"`) is read the same way.
- **rules**: the first row whose `condition` is true wins; conditions use the [Decision](Decision.md) syntax. A row without a condition or a value never matches. With no match and no `otherwise`, the status stays blank.

The editor may store the unused keys of the other modes as well (`value`, `smartText`, `rules`, `otherwise`); only the ones of the current `mode` count.

## Outputs

None. The step's effect is the row it adds to the search results.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `description` empty | Please fill in the highlighted fields. |
| editor | info | status line: a fixed `stockStatus` that is not a value, or a rule without condition or value | %1: '%2' is not one of the values. |

There are no publish-time checks. The step picker offers it only in flows on When an item search is performed; a hand-written definition that uses it elsewhere is not rejected, it just does nothing.

## Runtime errors

| condition | message |
|---|---|
| `unitCost`, `unitPrice` or `stockAmount` is not a number | The %1 of the search result is not a number: %2 |
| not inside an item search (Info log entry, no error) | No item search is in progress - the search result was not added. "Add search result" only works when the flow is started from the item search. |

`%1` is the field caption (Unit Cost, Unit Price, Stock Amount), `%2` the text that was given.

## Example

Inside a For Each over the supplier's products, with a Parser step `Product` that reads the current product:

```json
{
  "id": "6B2C3D4E-5F6A-4B7C-8D9E-0F1A2B3C4D01",
  "type": "action",
  "action": 5564012,
  "description": "Add search result",
  "slug": "AddResult",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/af-sf-add-result.svg",
  "terminating": false,
  "configuration": {
    "description": "{{Product_name}}",
    "description2": "",
    "vendorNo": "V-ACME",
    "vendorItemNo": "{{Product_sku}}",
    "manufacturer": "{{Product_brand}}",
    "manufacturerItemNo": "{{Product_mpn}}",
    "gtin": "{{Product_ean}}",
    "imageUrl": "{{Product_image}}",
    "unitOfMeasure": "PCS",
    "unitCost": "{{Product_price}}",
    "unitPrice": "{{Product_rrp}}",
    "stockAmount": "{{Product_stock}}",
    "stockStatus": {
      "mode": "rules",
      "rules": [
        { "condition": "{{Product_stock}} > 10", "value": "InStock" },
        { "condition": "{{Product_stock}} > 0", "value": "LowStock" }
      ],
      "otherwise": "OutOfStock"
    },
    "payload": "{{Product_id}}"
  },
  "outputs": []
}
```

A complete search flow is in [examples/supplier-item-search.json](../../examples/supplier-item-search.json).

## Gotchas

- `vendorNo` is the vendor's number **in Business Central**. Write it as a constant per supplier flow; the supplier's API does not know it.
- Without `vendorNo` and `vendorItemNo` an imported item is never recognised again, so `ExistingItemNo` stays empty and the import flow creates duplicates.
- Put what the import needs in `payload`. The selection flow gets only the result's fields and the payload, not the search flow's other outputs.
- Keep the search flow fast. The user waits for it, and the trigger's `timeoutSec` (default 30) covers all of its steps.
- An empty `stockAmount` is `0`, and the column shows only if at least one result has a non-zero amount. Use `stockStatus` when the supplier only reports a grade.
