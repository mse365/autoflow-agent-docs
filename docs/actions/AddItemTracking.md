# Add Item Tracking

[← All actions](README.md)

Assigns a serial, lot or package number to a sales or purchase line by creating an item-tracking reservation entry.

| | |
|---|---|
| Enum name | `AddItemTracking` |
| Ordinal | `"action": 5564417` |
| Category | Records |
| Terminating | `false` |
| Group / edges | No |
| Availability | GA |

## What it does

The step resolves `reference` to a **Sales Line (37)** or **Purchase Line (39)**. From the line it derives the item, variant, location, quantity per unit of measure, the date (shipment date or expected receipt date) and the direction:

- Inbound (positive): purchase documents, and sales return orders and sales credit memos.
- Outbound (negative): purchase return orders and purchase credit memos, and all other sales documents.

If the line already has a reservation without a serial number, the tracking is attached to that reservation. Otherwise a surplus item-tracking entry is created. For a drop-shipment **purchase** line, the tracking is also mirrored to the linked sales order line. The step has no outputs.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `reference` | string | yes | `""` | One SmartField placeholder resolving to the sales or purchase line, e.g. `"{{FindSalesLine_results}}"`. |
| `trackingType` | integer | yes | `0` | `0` = Serial No., `1` = Lot No., `2` = Package No. |
| `value` | string | yes | `""` | The serial, lot or package number. **This is the key the step reads.** SmartText (SmartFields, `[[formulas]]` and SmartControls are resolved before the step runs). Truncated to the target field length. |
| `trackingValue` | string | no | `""` | The same number as written by the visual editor. It is **not read at runtime**. Set it to the same text as `value` so the editor shows it. |
| `quantity` | string | no | `"1"` | Quantity in the line's unit of measure, as **text**, parsed in invariant format (`"2"`, `"2.5"`). Ignored for serial numbers (always 1). For lot and package numbers it must be > 0. SmartText. |

## Outputs

None.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `reference` is not a `{{…}}` placeholder | `Select the sales or purchase line to add item tracking to.` |
| editor | error | `value` is empty | `Enter the serial, lot or package number to assign.` |

There are no publish-time checks specific to this step. A Confirm dialog after this step gets a publish warning, because this step writes to the database.

## Runtime errors

| condition | message |
|---|---|
| Reference does not resolve | `Reference "%1" cannot be resolved to a record.` |
| Reference is not a Sales Line / Purchase Line | `The Add Item Tracking step must reference a Sales Line or a Purchase Line, but the reference points to "%1".` |
| `value` empty after resolution | `Enter the %1 to assign.` (`%1` = `serial number` / `lot number` / `package number`) |
| Lot/package with quantity ≤ 0, missing or not parseable | `Enter a quantity greater than zero.` |
| Item has no Item Tracking Code | `Item %1 is not set up for item tracking, so no serial, lot or package number can be assigned.` |
| Sales line is a drop shipment | `This sales line is a drop shipment. For drop shipments, add the item tracking on the linked purchase order line instead – it is mirrored to the sales side automatically.` |

## Example

```json
{
  "id": "9D1F3A5C-7E9B-4D1F-8A3C-5E7A9C1B3D57",
  "type": "action",
  "action": 5564417,
  "description": "Add Item Tracking",
  "slug": "AddItemTracking",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/arrow-bear-right-2.svg",
  "terminating": false,
  "configuration": {
    "reference": "{{FindPurchaseLine_results}}",
    "trackingType": 1,
    "value": "{{Parser_lotNo}}",
    "trackingValue": "{{Parser_lotNo}}",
    "quantity": "{{Parser_qty}}"
  },
  "outputs": []
}
```

## Gotchas

- **Key mismatch in the product:** the visual editor saves the number as `trackingValue`, but the runtime and the editor check read `value`. A step configured only in the editor therefore fails at runtime with "Enter the … number to assign." In JSON, always write `value`, and write `trackingValue` with the same content.
- `quantity` is text in invariant format. Use `"2.5"`, not `"2,5"`.
- If the line's `No.` is not an existing item (e.g. a G/L account line), the step does nothing and still succeeds.
- `trackingType` is the integer ordinal, not `"Lot"`.
