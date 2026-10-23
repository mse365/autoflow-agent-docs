# Loop Over Elements (For Each Loop)

[← All actions](README.md)

Repeats the steps in its body once for each item of an array, a collection or a set of linked records.

| | |
|---|---|
| Enum name | `ForEachLoop` |
| Ordinal | `"action": 101` |
| Category | Control |
| Terminating | `false` |
| Group / edges | Yes: one fixed edge, `"for-each"` (the loop body) |
| Availability | GA |

## What it does

On the first pass the step resolves `selector`, collects all items into its `items` output and sets `total`. On each pass it sets `currentItem` to the item at the current position and runs the body (the `for-each` edge). After the body finishes, the engine runs the loop step again for the next item until `iteration` reaches `total`, and then continues with the step after the loop. The item set is captured once on the first pass, so changes the body makes to the source do not change what is iterated. An empty collection skips the body entirely. There is no iteration cap. The loop runs exactly `total` times.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `selector` | string | yes | – | Exactly one SmartField placeholder `{{name}}`. It can point to an array output (e.g. a find-records step's `{{<slug>_results}}`), a collection, or a dotted relation such as `{{trigger_Rec.SalesLines}}`, where `SalesLines` is a `reference` definition in `smartFieldDefs` (see [selector fields](../references-and-smart-fields.md#16-selector-fields-reference-inputs)). Bare names without `{{ }}` are rejected. The raw, unsubstituted value is used. |

## Edges

| value | default description | meaning |
|---|---|---|
| `for-each` | `for each` | Loop body. Runs once per item. Skipped when the collection is empty. |

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `total` | value | – | Number of items. |
| `iteration` | value | – | Current pass, 1-based (`1`..`total`). |
| `items` | value **or** reference | table of the records (reference only) | All items, stored as `items[0]`..`items[total-1]` (zero-based). |
| `currentItem` | value **or** reference | same as `items` | The item of the current pass (= `items[iteration-1]`). |

`items` and `currentItem` are declared as `{"type":"reference","tableNo":N}` when the selector resolves to record references, and as `{"type":"value"}` otherwise. The editor derives this from the selector. Do the same in hand-written JSON so that downstream steps can bind record fields.

Reference outputs inside the body as `{{<slug>_currentItem}}`, `{{<slug>_iteration}}` and `{{<slug>_total}}`. For a record item, address a field as `{{<slug>_currentItem.no}}` (see [field paths](../references-and-smart-fields.md#13-walking-a-path-through-records)).

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `selector` is empty (required field in the configuration dialog) | `Please fill in the highlighted fields.` |

## Runtime errors

| condition | message |
|---|---|
| Selector is not a `{{name}}` placeholder | `The selector '%1' must use the SmartField placeholder notation (e.g. '{{name}}'). Bare selector names are no longer accepted – open the SmartField picker on the For Each step config to insert a valid placeholder.` |
| Selector resolves to a non-empty scalar, or a dotted path doesn't resolve to records | `The provided selector '%1' does not resolve to an array or iterable reference.` |

For a plain `{{<slug>_<output>}}` selector, a name that doesn't exist at run time (a collection nothing was added to, or a typo) and a **blank** output (e.g. a parser step that matched nothing) count as an empty collection, not as an error: the loop is skipped silently. Check the selector name carefully.

## Example

```json
{
  "id": "2C9F1E7B-5A44-4D2B-9C1E-3F6A7B8C9D01",
  "type": "action",
  "action": 101,
  "description": "Loop Over Sales Lines",
  "slug": "LoopOverSalesLines",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/refresh.svg",
  "terminating": false,
  "configuration": {
    "selector": "{{FindSalesLines_results}}"
  },
  "outputs": [
    { "name": "total", "type": "value" },
    { "name": "iteration", "type": "value" },
    { "name": "items", "type": "reference", "tableNo": 37 },
    { "name": "currentItem", "type": "reference", "tableNo": 37 }
  ],
  "edges": [
    { "id": "2C9F1E7B-5A44-4D2B-9C1E-3F6A7B8C9D02", "value": "for-each", "description": "for each", "steps": [] }
  ]
}
```

## Gotchas

- The outputs of steps **inside** the body are deleted each time control returns to the loop step and again when the loop ends. Use them only within the same pass. To keep results, add them to a collection.
- If an array output is also a record reference (as find-records results are), the array entries are iterated, one item per entry.
- For a plain record reference that is not an array, every record in the reference's current filter is iterated.
- The step also writes a runtime-only `result` (`for-each`) that the engine uses for routing. Do not declare it in `outputs`.
