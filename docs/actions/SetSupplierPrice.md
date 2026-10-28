# Set supplier price

[← All actions](README.md) · [Supplier Foundation overview](../apps/SupplierFoundation.md)

Writes the purchase price a supplier reported into Business Central's purchase prices, for the vendor of a supplier code.

| | |
|---|---|
| Enum name | `SetSupplierPrice` (AL: `mse365 AF-SF SetSupplierPrice`) |
| Ordinal | `"action": 5564014` |
| Category | AutoFlow Supplier Foundation |
| Terminating | `false` |
| Group / edges | No |
| Availability | Requires the **AutoFlow Supplier Foundation** app. Offered for every trigger. |

## What it does

Typically used in a flow on [When a price update is requested](../triggers/PriceUpdate.md). The step writes the price where Business Central's own purchase price calculation reads it. Business Central then uses it as the direct unit cost of new purchase lines, and Supplier Foundation shows it as *Supplier Price* on sales and purchase lines.

Where it goes depends on how the environment calculates prices:

- **Extended price calculation on** (the *new pricing experience* in Feature Management): into the supplier code's **purchase price list**. The first price creates the list, numbered from *Price List Nos.* on the Purchases & Payables Setup, in the vendor's currency, and stores its code on the supplier code (*Price List Code*, field `6`). A user can also enter an existing purchase price list of the vendor there.
- **Off**: into the legacy **Purchase Price** table, for the vendor and its currency.

Each item, variant and unit of measure has **one** price, without a starting date or minimum quantity. Setting it again updates that price; an unchanged price writes nothing. The price is active at once. If *Allow Editing Active Price* is off in the Purchases & Payables Setup, the step sets the whole price list to Draft and back to Active around the change, which touches every line of the list.

The step logs an Info entry: "Price of item %1 set to %2 in price list %3."

## Configuration

Every key is a SmartText string. Values are trimmed.

| key | type | required | default | max | description |
|---|---|---|---|---|---|
| `supplierCode` | string | yes | `""` | 20 | The [supplier code](../apps/SupplierFoundation.md#supplier-codes), e.g. `ACME`. Its vendor gets the price. |
| `itemNo` | string | yes | `""` | 20 | The item. It must exist. |
| `variantCode` | string | no | `""` | 10 | The variant the price is for. Empty for the item itself. |
| `unitOfMeasureCode` | string | no | `""` | 10 | The unit the price refers to. Empty: with price lists, the item's purchase unit (what Business Central puts on a new price list line); in the legacy table, an empty unit. |
| `directUnitCost` | string | yes | `""` | – | The price, in the vendor's currency. A number, see below. |

**`directUnitCost`** is read like the numbers in [Add search result](AddSearchResult.md): `1234.5` and `1234,5` are both 1234.5. With both separators, the last one is the decimal separator and the other is dropped (`1,234.50`, `1.234,50`). A comma alone is always decimal, so `1,234` is 1.234. Empty means `0` and sets a price of 0. Any other text fails the step.

## Outputs

| name | type | tableNo | set | notes |
|---|---|---|---|---|
| `PriceListCode` | value | – | always | The price list the price went into. Empty when the legacy purchase prices were used. |

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `supplierCode`, `itemNo` or `directUnitCost` empty | Please fill in the highlighted fields. |

There are no publish-time checks.

## Runtime errors

| condition | message |
|---|---|
| `supplierCode` empty, longer than 20 characters, or not set up | The supplier code %1 is not set up. Add it on the Supplier Codes page. |
| `directUnitCost` is not a number | The %1 of the search result is not a number: %2 (`%1` = Direct Unit Cost; the text is shared with Add search result) |
| item, variant or unit of measure does not exist | Business Central's own error |
| price lists, no Price List Code yet, and *Price List Nos.* empty | The supplier code %1 has no price list yet, and no number series is set up to create one. Fill in Price List Nos. on the Purchases & Payables Setup, or enter a price list on the supplier code. |
| the supplier code's Price List Code belongs to another vendor | Price list %1 of supplier code %2 is not a price list of vendor %3. Clear the price list on the supplier code (a new one is then created) or enter one of the vendor's purchase price lists. |

## Example

In a flow on When a price update is requested, with a Parser step `Price` that read the supplier's answer:

```json
{
  "id": "3E9A7C21-4B6D-4F80-A1C3-5D7E9F0B2C14",
  "type": "action",
  "action": 5564014,
  "description": "Set supplier price",
  "slug": "SetPrice",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/af-sf-set-price.svg",
  "terminating": false,
  "configuration": {
    "supplierCode": "ACME",
    "itemNo": "{{trigger_Item.no}}",
    "variantCode": "",
    "unitOfMeasureCode": "",
    "directUnitCost": "{{Price_price}}"
  },
  "outputs": [
    { "name": "PriceListCode", "type": "value" }
  ]
}
```

## Gotchas

- An empty `directUnitCost` is not an error: it sets the price to 0. If the supplier may not answer with a price, check `{{Price_price}} != ''` first.
- The price is in the **vendor's** currency, which is the currency of the price list. Convert it in the flow if the supplier quotes in another currency.
- Changing the supplier code's vendor clears its Price List Code. The next price then creates a new list for the new vendor.
- A sales line's *Supplier Price* is calculated for the line's *Supplier No.* (field `5564012`; no price is shown while it is empty), at the work date and the line's quantity, unit and variant. A purchase line's is calculated for its Buy-from Vendor. Set the price for the unit the lines use, or leave the unit empty to use the item's purchase unit.
- Leaving the unit empty means different things in the two modes: the item's purchase unit with price lists, an empty unit in the legacy table.
