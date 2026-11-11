# Create Element

[← All actions](README.md)

Declares a single-slot variable that holds one text value or one record reference, with an optional initial value.

| | |
|---|---|
| Enum name | `ElementCreate` |
| Ordinal | `"action": 202` |
| Category | Data |
| Terminating | `false` |
| Group / edges | No |
| Availability | GA |

## What it does

The step creates a named slot and publishes it as an output, so that later steps can read it and [Set Element](ElementSet.md) steps can overwrite it. A Value element always writes its slot at run time: the resolved `initialValue`, or `''` if none is given. As a result, references to it resolve even before any Set Element step runs. A Reference element writes its slot only when `initialValue` is given. Otherwise the slot stays unset until a Set Element step fills it.

The element is published under the **bare name you type**, not under `<slug>_<name>`: an element called `Amount` is `{{Amount}}` everywhere in the flow, whatever the step's slug is. That is why the name must be unique across the whole flow.

> **Before 27.0.41:** the output was addressed as `{{<slug>_<elementName>}}` (for example `{{Total_Amount}}`), the name was not checked against a grammar, and a name longer than 30 characters was silently truncated at run time. See [Migration](#migration-from-the-prefixed-form) below.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `elementName` | string (max 30) | yes | `""` | Name of the element and of the step's output, written exactly as it is referenced: `{{<elementName>}}`. Plain text. Grammar `[A-Za-z][A-Za-z0-9-]*`, 1–30 characters (letter first, then letters, digits or hyphens; no spaces, no underscore). Must be unique in the flow, compared case-insensitively against **every** other output name: every `<slug>_<output>` of every other step (trigger keys as cut at 30 characters) and every other Create Element / Create Collection name, in all branches and loop bodies. |
| `elementType` | integer | no | `0` | `0` = Value, `1` = Reference. A missing or unknown value is treated as `0`. |
| `tableNo` | integer | if `elementType` = 1 | `0` | Table that the reference points to. The editor writes `0` for Value elements. |
| `initialValue` | string | no | `""` | **Value:** SmartText (SmartFields, SmartFormulas, SmartControls), resolved at run time. **Reference:** a single `{{name}}` that resolves to an upstream Reference output of the same table, or empty. |

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `<elementName>` | `value` | – | when `elementType` = 0 |
| `<elementName>` | `reference` | `<tableNo>` | when `elementType` = 1 |

The output entry carries two extra keys that mark it as unprefixed:

```json
{ "name": "Amount", "type": "value", "unprefixed": true, "nameKey": "elementName" }
{ "name": "Customer", "type": "reference", "tableNo": 18, "unprefixed": true, "nameKey": "elementName" }
```

- `unprefixed: true` tells the run time, the field picker, the dangling-reference check and the loop/branch cleanup to use the bare name. **Write it**: an output without the flag registers as `<slug>_<elementName>`, the pre-27.0.41 behaviour, and `{{<elementName>}}` then doesn't resolve. The validator reports a missing flag as `output.unprefixed-expected`.
- `nameKey` names the configuration key that holds the name (`elementName`), so the editor can rename both when it duplicates the step.

To reference the element, use `{{<elementName>}}`, for example `{{Amount}}`. For a Reference element you can also use field paths such as `{{Customer.name}}` (see [field paths](../references-and-smart-fields.md#13-walking-a-path-through-records)).

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `elementName` non-empty | Please fill in the highlighted fields. |
| editor | error | `elementName` matches `[A-Za-z][A-Za-z0-9-]*` and is at most 30 characters | The name "%1" cannot be used. Start with a letter and use only letters, digits or hyphens (no spaces or underscores, at most 30 characters). |
| editor | error | `elementName` is not used by any other output in the flow (case-insensitive, against every `<slug>_<output>` and every other element / collection name) | The name "%1" is already used by another output in this flow. Choose a different name. |
| editor | error | `tableNo` non-zero when `elementType` = 1 | Please fill in the highlighted fields. |
| publish | error | no element / collection name is used by more than one output of the flow (case-insensitive). Hard stop ahead of the confirmable warnings; also returned by a Flow API import or validate call, one issue per name: *The output name "%1" is used by more than one step output. Every name must be unique.* | This flow cannot be published because these names are used by more than one step output:\\%1\\Rename the Create Element or Create Collection step so that every name is unique. |

The first and fourth rules are required-field checks in the configuration dialog. The grammar and uniqueness rules appear in the dialog's status line while you type, block **Save**, and are checked again when the editor persists the step. Publishing re-runs only the uniqueness check (as the duplicate-name error); an invalid name in a hand-written file is accepted by import and publish, so keep to the grammar yourself. The validator checks all of them (`ElementCreate.elementName-grammar`, `ElementCreate.elementName-maxLength`, `publish.duplicate-output-name`).

Because the name is a placeholder root, a `{{<elementName>…}}` token is never mistaken for a `{{<slug>_…}}` reference by the dangling-reference warning, even when it contains no underscore at all.

## Runtime errors

- `Reference elements require a single SmartField placeholder for the initial value, e.g. '{{name}}'. Got: %1`: occurs for a Reference element whose `initialValue` is not a single placeholder.
- `Reference '%1' not found in context.`: the placeholder does not resolve to a Reference in the current run.

## Example

```json
{
  "id": "9A8B7C6D-5E4F-4A3B-8C2D-1E0F9A8B7C6D",
  "type": "action",
  "action": 202,
  "description": "Create Amount Element",
  "slug": "Total",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/createelement.svg",
  "terminating": false,
  "configuration": {
    "elementName": "Amount",
    "elementType": 0,
    "tableNo": 0,
    "initialValue": "0"
  },
  "outputs": [
    { "name": "Amount", "type": "value", "unprefixed": true, "nameKey": "elementName" }
  ]
}
```

Later steps read it as `{{Amount}}` and a [Set Element](ElementSet.md) step selects it with `"elementSelector": "{{Amount}}"`.

## Migration from the prefixed form

- No upgrade rewrites existing flows. A flow saved before 27.0.41 keeps its stored outputs (without `unprefixed`) and its `{{<slug>_<elementName>}}` references, and keeps working as before.
- The migration happens when the Create Element step is **saved in the flow editor**: its outputs are regenerated with `unprefixed: true`, and the root of every `{{<slug>_<elementName>…}}` token in every step configuration of the flow (all branches, dotted paths, indexes and `;format` suffixes included) is rewritten to `{{<elementName>…}}`. The same rewrite runs whenever the name is changed later.
- Import does not migrate. When you write or update a file by hand, be consistent: either the pre-27.0.41 form (outputs without the flag, `{{<slug>_<elementName>}}` references) or the current form (flag set, bare references). Mixing them leaves the references unresolved.
- Duplicating the step in the editor renames the copy's element to `<name>2`, `<name>3`, … (shortened to stay within 30 characters), updates `elementName` and rewrites the references inside the copy.

## Gotchas

- Neither the editor nor the run time checks that a Reference `initialValue` belongs to the same table as `tableNo`. Keep them consistent yourself.
- If the step sits inside a loop or branch body, its slot is removed when the body is left. Create elements at the level where you need to read them.
- Uniqueness compares full resolved names: an element named `Rec` is fine next to `{{trigger_Rec}}`, but not next to a collection named `rec` or another element named `Rec` anywhere in the flow.
