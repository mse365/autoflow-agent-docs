# Read task repeater

[← All actions](README.md)

Reads the rows a person entered in a repeater section of a [Form task](FormTask.md) and writes each column as an output, for all rows or for one row (typically the current item of a For Each over the repeater).

| | |
|---|---|
| Enum name | `ReadTaskRepeater` |
| Ordinal | `"action": 5564427` |
| Category | Tasks |
| Terminating | `false` |
| Group / edges | No |
| Availability | Generally available from AutoFlow 27.0.41 (part of AutoFlow Tasks). Creates no task and does not wait, so it has no trigger restriction of its own. |

## What it does

The step resolves `input` into the rows it holds: every row of a repeater output, or the single row of an indexed entry or a For Each `currentItem`. For each row it reads the columns listed in `columns` and writes them as outputs: `<column>` for the first row and `<column>[i]` for every row. `count` is the number of rows read.

The columns are not chosen freely. They are a copy of the `columns` that the Form task's repeater output carries. In the editor the step takes them over when it is saved and again whenever another step of the flow is edited, so it follows the form. A [For Each](ForEachLoop.md) over the repeater passes the columns on to its `items` and `currentItem` outputs in the same way.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `input` | string | yes | – | Exactly one placeholder `{{name}}`: the rows output of a Form task repeater (`{{<formSlug>_<section>}}`), one row of it (`{{<formSlug>_<section>[2]}}`), or the `currentItem` of a For Each over it (`{{<loopSlug>_currentItem}}`). The raw form is used. See [selector fields](../references-and-smart-fields.md#16-selector-fields-reference-inputs). |
| `columns` | array | yes | – | Rows of `{ "name", "type", "tableNo" }`: the same entries as the `columns` of the repeater output that `input` points at. `type` is `"value"` or `"reference"`; `tableNo` only for `"reference"`. |

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `<column name>` | value, or reference for a `"reference"` column | = the column's `tableNo` (reference) | One per `columns` row, in order. `{{<slug>_<column>}}` is the column of the first row (for a single row: of that row), `{{<slug>_<column>[0]}}`, `{{<slug>_<column>[1]}}`, … of each row. Not written when there is no row. |
| `count` | value | – | Number of rows read. |

Values have the format the Form task stores them in: `true` / `false`, `12`, `1.25`, `2026-11-02`, `2026-11-02T09:30:00`.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `input` is empty | `Please fill in the highlighted fields.` |

The step's own messages (`Choose the repeater of a form task to read.`, `The step knows no columns of %1. Choose the repeater of a form task and save the step.`) are not run. Without `columns` the step only writes `count`.

## Runtime errors

| condition | message |
|---|---|
| `input` holds plain values, or records that are not rows of a Form task repeater (`%1` = the input) | `%1 is not a repeater of a form task. Choose the repeater output of a Form task step, or one row of it.` |

An `input` that resolves to nothing is not an error: `count` is `"0"`. This is the case for a repeater the person left empty, and also for an `input` that is not a single `{{name}}` placeholder.

## Example

Inside the body of a For Each with slug `EachLine` over `{{Request_lines}}` (the repeater of the [Form task example](FormTask.md#example)), the step reads the current row:

```json
{
  "id": "9D3A5C70-6E8F-4B2C-8D4E-3F5A7B9C1D01",
  "type": "action",
  "action": 5564427,
  "description": "Read line",
  "slug": "Line",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/table-rows.svg",
  "terminating": false,
  "configuration": {
    "input": "{{EachLine_currentItem}}",
    "columns": [
      { "name": "item", "type": "reference", "tableNo": 27 },
      { "name": "quantity", "type": "value" }
    ]
  },
  "outputs": [
    { "name": "item", "type": "reference", "tableNo": 27 },
    { "name": "quantity", "type": "value" },
    { "name": "count", "type": "value" }
  ]
}
```

The For Each step declares its `items` and `currentItem` outputs as `{ "type": "reference", "tableNo": 5564267, "columns": [ … ] }` with the same columns. Later steps in the body use `{{Line_item.no}}` and `{{Line_quantity}}`.

## Gotchas

- Keep `columns` and `outputs` equal to the repeater's fields in the Form task. At run time the step reads the columns from its own configuration, not from the form.
- Used directly on the repeater (`{{<formSlug>_<section>}}`) the step reads all rows at once: `{{<slug>_<column>[i]}}` per row and `count`. Inside a For Each on `currentItem` it reads one row and `count` is `"1"`.
- Do not name a repeater column `count`: the step's own output uses that name.
- Outputs written inside a For Each body are discarded when the loop finishes, like any step in a loop.
