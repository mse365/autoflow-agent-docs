# Add to Collection

[← All actions](README.md)

Appends one text value or one record reference to a collection declared by a Create Collection step.

| | |
|---|---|
| Enum name | `AddToCollection` |
| Ordinal | `"action": 201` |
| Category | Data |
| Terminating | `false` |
| Group / edges | no |
| Availability | GA |

## What it does

The step finds the first free index of the target collection (`…[0]`, `…[1]`, …) and writes the item there. For a Value collection, the item is the resolved text of `value`. For a Reference collection, `value` must be a single `{{name}}` placeholder of an upstream Reference output, and the record reference it points to is stored. The step is usually placed inside a For Each loop to collect results.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `collectionSelector` | string | yes | `""` | Exactly one placeholder naming the Create Collection output, for example `{{OrderList_Orders}}`. It must be wrapped in `{{ }}` and must not contain a dotted path. It is read unresolved. |
| `value` | string | yes | `""` | **Value collection:** SmartText (SmartFields, SmartFormulas, SmartControls), resolved before it is appended. **Reference collection:** exactly one `{{name}}` that resolves to a Reference output of the same table. |
| `derivedType` | string | yes | `""` | `"value"` or `"reference"`. This must match the collection's type. At run time only this key decides how the item is stored. A missing or empty value means text. |
| `derivedTableNo` | integer | no | `0` | Table number of the collection (0 for Value). Informational. |

The editor works out `derivedType` and `derivedTableNo` from the selected collection and saves them. **When you write JSON by hand, you must set them yourself.**

## Outputs

None. The items become part of the Create Collection step's output (`<slug>_<collectionName>[n]`).

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `collectionSelector` resolves to an upstream output | – |
| editor | error | `value` is non-empty for Value collections | Please fill in the highlighted fields. |
| editor | error | Reference collection: `value` is a single `{{name}}` that resolves to a Reference output with the same `tableNo` | – |
| editor | warning | `derivedType` is `"value"` or `"reference"` and matches the collection | – |
| runtime | error | `collectionSelector` is empty | Collection selector is required. |
| runtime | error | `collectionSelector` is not a `{{name}}` placeholder | The Collection selector '%1' must use the SmartField placeholder notation, e.g. '{{name}}'. |
| runtime | error | `collectionSelector` contains `.` | The Collection selector '%1' must point to a top-level output – dotted paths cannot be collections. |

The editor checks are not re-run at publish. Only the generic dangling-reference warning applies there.

## Runtime errors

- `Reference collections require a single SmartField placeholder for the Value, e.g. '{{name}}'. Got: %1`: occurs when `derivedType` = `reference` and `value` is not a single placeholder.
- `Reference '%1' not found in context.`: the placeholder does not resolve to a Reference in the current run.
- `Execution entry %1 not found.`: the step was run outside a flow execution.

## Example

The following step adds the current loop record to a Reference collection of Sales Headers.

```json
{
  "id": "2D7E9A40-5B1C-4C8D-8E2F-3A4B5C6D7E8F",
  "type": "action",
  "action": 201,
  "description": "Add to Orders",
  "slug": "AddOrder",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/addtocollection.svg",
  "terminating": false,
  "configuration": {
    "collectionSelector": "{{OrderList_Orders}}",
    "value": "{{EachOrder_item}}",
    "derivedType": "reference",
    "derivedTableNo": 36
  },
  "outputs": []
}
```

For a Value collection, use something like `"value": "{{EachOrder_currentItem.no}}"`, `"derivedType": "value"` and `"derivedTableNo": 0`.

## Gotchas

- `{{EachOrder_item}}` in the example is illustrative. Use the real Reference output name of your loop or Find Records step.
- If `derivedType` is missing, an item added to a Reference collection is stored as text and later reference access fails.
- Steps that sit inside a loop body lose their runtime values when the body is left. Collection items survive as long as the Create Collection step's level is still active.
