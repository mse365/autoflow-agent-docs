# Create Collection

[← All actions](README.md)

Declares an empty, named list of text values or record references that later Add to Collection steps fill.

| | |
|---|---|
| Enum name | `CreateCollection` |
| Ordinal | `"action": 200` |
| Category | Data |
| Terminating | `false` |
| Group / edges | no |
| Availability | GA |

## What it does

The step declares a collection and publishes it as an output so that later steps can select it. It does nothing at run time, because an empty collection has no runtime form. The collection only exists once an [Add to Collection](AddToCollection.md) step has appended an item. Items are stored as `<slug>_<collectionName>[0]`, `[1]`, and so on.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `collectionName` | string | yes | `""` | Name of the collection and of the step's single output. Plain text, with no SmartText support. Use an identifier-like name (letters, digits, hyphens), because it is embedded in `{{...}}` placeholders. |
| `collectionType` | integer | yes | `0` | `0` = Value (a list of text values), `1` = Reference (a list of record references). A missing or unknown value is treated as `0`. |
| `tableNo` | integer | if `collectionType` = 1 | `0` | Table that the references point to. The editor writes `0` for Value collections. It is copied into the output's `tableNo`. |

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `<collectionName>` | `value` | – | when `collectionType` = 0 |
| `<collectionName>` | `reference` | `<tableNo>` | when `collectionType` = 1 |

No output is generated while `collectionName` is empty. To reference the collection, use `{{<slug>_<collectionName>}}`, for example `{{OrderList_Orders}}`. Use that selector in Add to Collection, in For Each, and in aggregate SmartFormulas. A single item can be addressed as `{{OrderList_Orders[0]}}`.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `collectionName` must be non-empty | Please fill in the highlighted fields. |
| editor | error | `collectionType` must be 0 or 1 | – |
| editor | error | `tableNo` must be non-zero when `collectionType` = 1 | Please fill in the highlighted fields. |

These are checks in the config canvas and the step's validity check. Publishing does not re-run them. At publish time only the generic warnings apply: a dangling `{{slug_…}}` reference, or a terminating step that has a successor.

## Runtime errors

None. The step never fails.

## Example

```json
{
  "id": "6B1C8D2E-3F4A-4B5C-9D6E-7F8091A2B3C4",
  "type": "action",
  "action": 200,
  "description": "Create Orders Collection",
  "slug": "OrderList",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/createcollection.svg",
  "terminating": false,
  "configuration": {
    "collectionName": "Orders",
    "collectionType": 1,
    "tableNo": 36
  },
  "outputs": [
    { "name": "Orders", "type": "reference", "tableNo": 36 }
  ]
}
```

## Gotchas

- Use the full output name in selectors: `{{<slug>_<collectionName>}}`, not just the collection name.
- If no item is ever added, the collection does not exist at run time. Steps that iterate over it then see nothing.
- When a loop or branch body is left, AutoFlow removes the runtime values of the steps inside that body. Put the Create Collection step at a level that stays readable for as long as you need the collection, typically before the loop that fills it.
- The editor's default slug is the PascalCase form of the description, capped at 20 characters. "Create Orders Collection" becomes `CreateOrdersCollecti`. Choose a short custom slug instead.
