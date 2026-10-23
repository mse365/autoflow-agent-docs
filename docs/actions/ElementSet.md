# Set Element

[← All actions](README.md)

Overwrites the slot of an element created by a Create Element step with a new value or record reference.

| | |
|---|---|
| Enum name | `ElementSet` |
| Ordinal | `"action": 203` |
| Category | Data |
| Terminating | `false` |
| Group / edges | No |
| Availability | GA |

## What it does

The step replaces the content of the element's single slot. It never appends; use Add to Collection for lists. For a Value element, the resolved text of `value` is stored, and an empty `value` clears the slot. For a Reference element, `value` must be a single `{{name}}` placeholder of an upstream Reference output, and that record reference is stored.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `elementSelector` | string | yes | `""` | Exactly one placeholder naming the Create Element output, for example `{{Total_Amount}}`. It must be wrapped in `{{ }}` and must not contain a dotted path. It is read unresolved. |
| `value` | string | no | `""` | **Value element:** SmartText, resolved before it is stored; empty clears the slot. **Reference element:** exactly one `{{name}}` that resolves to a Reference output of the same table. |
| `derivedType` | string | yes | `""` | `"value"` or `"reference"`. This must match the element's type. At run time only this key decides how the value is stored. A missing or empty value means text. |
| `derivedTableNo` | integer | no | `0` | Table number of the element (0 for Value). Not used at run time. |

The editor works out `derivedType` and `derivedTableNo` from the selected element when the dialog is saved (if it can't resolve the selector, it writes `""` and `0`). **When you write JSON by hand, you must set them yourself.**

## Outputs

None. The new content is read through the Create Element step's output (`{{<createSlug>_<elementName>}}`).

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `elementSelector` is empty (required field in the configuration dialog) | Please fill in the highlighted fields. |
| runtime | error | `elementSelector` empty | Element selector is required. |
| runtime | error | `elementSelector` not a placeholder | The Element selector '%1' must use the SmartField placeholder notation, e.g. '{{name}}'. |
| runtime | error | `elementSelector` dotted | The Element selector '%1' must point to a top-level output – dotted paths cannot be elements. |

The configuration dialog also shows a live status line while you edit. It is advisory: it doesn't stop the dialog from saving, and nothing re-checks it at publish (only the generic dangling-reference warning applies there). Each message is prefixed with the field it concerns:

| condition | status message |
|---|---|
| element not chosen yet | Element: Pick an element from the SmartField picker. |
| `elementSelector` is not a `{{name}}` placeholder | Element: The Element field must be a SmartField placeholder, e.g. {{elementName}}. |
| `elementSelector` is dotted | Element: The Element placeholder must point to a top-level Create Element output – dotted paths are not elements. |
| `elementSelector` does not resolve upstream | Element: Cannot resolve %1 against the available outputs of upstream steps. |
| Reference element: `value` is not a single placeholder | Value: A Reference element requires a single SmartField placeholder, e.g. {{find-records_results}}. |
| a placeholder in `value` does not resolve upstream | Value: Cannot resolve %1 against the available outputs of upstream steps. |
| Reference element: `value` resolves to a Value output | Value: %1 resolves to a Value SmartField but the element expects a Reference. |
| Reference element: table mismatch | Value: %1 references table %2 but the element holds a reference to table %3. |

When the configuration is valid, the status reads `✓ Value` or `✓ Reference: <table caption> (<table no>)`. Treat every status problem as an error when you write JSON by hand.

## Runtime errors

- `Reference elements require a single SmartField placeholder for the Value, e.g. '{{name}}'. Got: %1`
- `Reference '%1' not found in context.`
- `Execution entry %1 not found.`

## Example

The following step adds the current line amount to a running total kept in a Value element.

```json
{
  "id": "4C3B2A19-0F8E-4D7C-B6A5-948372615F0E",
  "type": "action",
  "action": 203,
  "description": "Set Total_Amount",
  "slug": "AddToTotal",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/setelement.svg",
  "terminating": false,
  "configuration": {
    "elementSelector": "{{Total_Amount}}",
    "value": "[[{{Total_Amount}} + {{EachLine_currentItem.amount}}]]",
    "derivedType": "value",
    "derivedTableNo": 0
  },
  "outputs": []
}
```

## Gotchas

- `EachLine` in the example stands for a For Each step over sales lines, and `Total` for the Create Element step that declared `Amount`.
- If `derivedType` is missing, a Reference element is overwritten with text.
