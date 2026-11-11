# Form task

[← All actions](README.md)

Hands a form to a user or a task group, waits in the background until they have filled it in, and continues with one output per field. The form has typed fields (text, numbers, dates, dropdowns, records), optional sections, repeater sections (tables the person fills in row by row), prefilled values and an optional preview next to the form.

| | |
|---|---|
| Enum name | `FormTask` |
| Ordinal | `"action": 5564426` |
| Category | Tasks |
| Terminating | `false` |
| Group / edges | No |
| Availability | Generally available from AutoFlow 27.0.41 (part of AutoFlow Tasks). Background triggers only, the same list as the [Approval task](ApprovalTask.md#where-it-can-be-used). |

## What it does

On its first run the step builds the form from its configuration. First comes a section without a heading that holds every field with no section, then the configured `sections` in order. Prefills, dropdown values, the records a record field offers and the prefilled rows of a repeater are resolved at this moment and are a snapshot.

The step then creates a task in the AutoFlow task inbox and the run **parks**. Waiting works exactly as for the [Approval task](ApprovalTask.md#what-it-does): the task is checked every poll interval (default 5 minutes), the run continues at once when the user the flow runs as completes it, the step fails on a cancelled task, each loop pass creates its own task, and a retried run reuses its task.

The person fills in the form and completes it. Completing is refused while a required field is empty, a number or date cannot be read, a dropdown value is not in the list (unless `freeText`), or a record is not one of the offered ones. They can save a draft and continue later. Rows of a repeater in which every cell is empty are dropped.

## Where it can be used

Background triggers only. The trigger list, the webhook `WaitForResponse` caveat and the SubFlow rule are the same as for the [Approval task](ApprovalTask.md#where-it-can-be-used).

## Licensing

Anyone can be an assignee or a group member, with no seat needed. **Completing** a form task needs a paid AutoFlow licence **and an AutoFlow Tasks seat**.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `instructions` | string | yes | – | What to fill in and why, shown above the form. Supports SmartFields `{{..}}`, SmartFormulas `[[..]]` and SmartControls `{#..#}`. |
| `assignType` | integer | no | `0` | `0` = user, `1` = task group. Any other value counts as user. This step has no "user who started the flow" mode. |
| `assignee` | string | yes | – | Type 0: a Business Central **user name** (or user security ID). Type 1: a **task group code**. Case-insensitive and trimmed. Can be a SmartField resolved at runtime. |
| `dueDate` | string | no | `""` | A date (`yyyy-mm-dd` is safest) or a SmartDate such as `[@ calc(today, "+5D") @]`. If it doesn't resolve to a date, it is ignored silently. |
| `sections` | array | no | `[]` | Rows of `{ "caption", "name", "kind", "rowsFrom", "allowAdd" }`, described below. The editor always writes the array. |
| `fields` | array | yes | – | Rows of `{ "section", "caption", "name", "type", "required", "value", "options", "freeText", "tableNo", "filters" }`, described below. At least one field. |
| `previewKind` | integer | no | `0` | `0` = no preview, `1` = HTML (`previewHtml`), `2` = a document (`previewDocument`). |
| `previewHtml` | string | no | `""` | Kind 1: the HTML to show. See [Preview](#preview). |
| `previewDocument` | string | no | `""` | Kind 2: one placeholder `{{name}}` holding a reference to an Incoming Document Attachment or an AutoFlow document. See [Preview](#preview). |

### `sections[]`

| field | type | default | description |
|---|---|---|---|
| `caption` | string | `""` | The heading on the task card. |
| `name` | string | – | How fields and outputs refer to the section. Letters and digits only, starting with a letter, at most 20 characters. Unique among all section **and** field names, case-insensitive. |
| `kind` | string | `"normal"` | `"normal"`: fields one below the other. `"repeater"`: a table with one column per field. Anything else counts as normal. |
| `rowsFrom` | string | `""` | Repeater only. Exactly one placeholder `{{name}}` that points to records (a reference, an array such as `{{FindCust_results}}`, or an iterator) or to a value or an array of values. The raw form is used. Each record or value becomes one prefilled row, at most **1,000**. Empty: no prefilled rows. |
| `allowAdd` | boolean | `false` | Repeater only. `true`: the person may add and delete rows. `false`: the prefilled rows stay as they are. |

### `fields[]`

Write every key on every row, as the editor does.

| field | type | default | description |
|---|---|---|---|
| `section` | string | `""` | The `name` of the field's section, case-insensitive. Empty, or a name no section has: the section without a heading at the top. |
| `caption` | string | `""` | The label on the task card. |
| `name` | string | – | The name of the field's output, or of the column in a repeater. Same rules as a section name. |
| `type` | string | `"text"` | `"text"`, `"multiline"`, `"boolean"`, `"integer"`, `"decimal"`, `"date"`, `"datetime"`, `"dropdown"` or `"reference"` (a record). |
| `required` | boolean | `false` | The task can only be completed once the field is filled in. No effect on a boolean field. |
| `value` | string | `""` | Prefill, as SmartText. For a `reference` field: exactly one placeholder `{{name}}` that holds a record (the first one of an array); anything else prefills nothing. See below for repeaters. |
| `options` | string | `""` | Dropdown only: the values to choose from, separated by `;` or line breaks. An entry that is exactly one placeholder holding several values, such as `{{Parser_codes}}`, adds each of them. |
| `freeText` | boolean | `false` | Dropdown only: the person may also type a value that is not in the list. |
| `tableNo` | integer | `0` | Reference only: the table whose records the field offers. |
| `filters` | array | `[]` | Reference only: `[{ "fieldNo": <int>, "filter": "<BC filter>" }]`, as for [Find Records](FindRecords.md). `filter` may contain SmartFields, resolved when the task is created. |

A `reference` field offers the records of its table that match `filters`, in primary-key order and at most **1,000**, looked up when the task is created.

Prefills are converted to the field's type where they can be read: a `date` to `2026-11-02`, a `datetime` to `2026-11-02T09:30`, a `decimal` to `1.25`, a `boolean` to `true` / `false`. A text that cannot be read stays as it is.

**Prefills in a repeater.** With `rowsFrom`, a prefill that **starts with the `rowsFrom` name**, e.g. `{{FindCust_results.name}}` for `rowsFrom` `{{FindCust_results}}`, is resolved once per row against that row's record or value. Any other prefill is the same in every row.

### Preview

The preview is shown next to the form and follows what the person enters. Unlike everything else, it is resolved live on the task card, not when the task is created.

- `previewKind` 1: `previewHtml` is HTML with SmartText. Besides the outputs of earlier steps, it can use the form's own fields under the step's **own slug**, named as later steps see them: `{{<slug>_<field>}}` (a record field drills into its record, e.g. `{{Order_customer.name}}`), a repeater's rows in a loop `{#for {{<slug>_<section>}} #}…{{<slug>_<section>.<column>}}…{#endfor#}`, and `{{<slug>_<section>Count}}`.
- `previewKind` 2: `previewDocument` is one placeholder holding a document reference. It can be one of the form's own `reference` fields, `{{<slug>_<field>}}`, so the preview shows the document the person chose.

## Outputs

Declare them in this order: the fields outside repeaters in `fields` order, then for each repeater section its rows and count, then `completedBy` and `task`.

| name | type | tableNo | notes |
|---|---|---|---|
| `<field name>` | value, or reference for a `reference` field | = the field's `tableNo` (reference) | One per field that is **not** in a repeater section. Values are text: `true` / `false`, `12`, `1.25`, `2026-11-02`, `2026-11-02T09:30:00`. An empty record field writes no output. |
| `<section name>` | reference | `5564267` | One per repeater section: its rows. `{{<slug>_<section>}}` is the first row, `{{<slug>_<section>[0]}}`, `{{<slug>_<section>[1]}}`, … each one. The declared output also carries `"columns"`, see below. |
| `<section name>Count` | value | – | One per repeater section: the number of rows. |
| `completedBy` | value | – | User name of who completed the task. |
| `task` | reference | `5564323` | The task record (`mse365 AF-CO Task`). |

The outputs are written once the task is completed.

A repeater's rows output carries the section's columns, one entry per field of the section, in `fields` order:

```json
{ "name": "lines", "type": "reference", "tableNo": 5564267, "columns": [
  { "name": "item", "type": "reference", "tableNo": 27 },
  { "name": "quantity", "type": "value" }
] }
```

`type` is `"reference"` with the field's `tableNo` for a `reference` field, and `"value"` (no `tableNo`) for every other type. [Read task repeater](ReadTaskRepeater.md) and [For Each](ForEachLoop.md) take the columns from here, so keep them in sync with `fields`.

Each row is a record of table 5564267 whose fields are the columns. To work with the rows, loop over `{{<slug>_<section>}}` with For Each and read the current row with Read task repeater.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `instructions` or `assignee` is empty | `Please fill in the highlighted fields.` |
| publish | error | The trigger cannot wait (see [Approval task](ApprovalTask.md#where-it-can-be-used)) | `The task step '%1' cannot be used in this flow: its trigger runs while the user works on the record (or answers right away), so the flow cannot wait for a person there. Use a trigger that runs in the background, such as a record trigger, a schedule or a manual start.` |

`%1` is the step **id**. The step's own messages are not run: `Add at least one field to the form.`, `The name '%1' is used more than once. Field and section names must be unique.`, `The name '%1' is not valid: use letters and digits only, at most %2 characters, starting with a letter.`, `The field '%1' is in section '%2', which does not exist.`, `Choose the table of the record field '%1'.`, `Enter the values of the dropdown '%1'.`, `The prefill of '%1' must use the rows of its section, for example {{%2.Name}}.`, `The repeater section '%1' has no fields.` and `Choose the document the preview shows.` Satisfy them anyway.

In the editor, a section or field row without a name gets one derived from its caption (camelCase, `Delivery date` → `deliveryDate`, cut at 20 characters). Import does not do this, so write the names yourself.

## Runtime errors

| condition | message |
|---|---|
| `fields` is empty | `The form has no fields.` |
| A `filters` row of a record field cannot be applied (`%1` = field name, `%2` = field number) | `The filter of the record field '%1' cannot be applied to field %2.` |
| Assignee empty / user missing / user disabled / group missing | The same messages as the [Approval task](ApprovalTask.md#runtime-errors). |
| Inline frame, SubFlow, cancelled task | The same messages as the [Approval task](ApprovalTask.md#runtime-errors). |

## Example

The step asks the purchasing group for a delivery date, a vendor and the order lines. The lines are prefilled from a Find Records step with slug `FindItems` on table 27, and the preview lists what was entered:

```json
{
  "id": "8C2F4B60-5D7E-4A1B-9C3D-2E4F6A8B0C01",
  "type": "action",
  "action": 5564426,
  "description": "Complete purchase request",
  "slug": "Request",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/forms.svg",
  "terminating": false,
  "configuration": {
    "instructions": "Please complete the purchase request and check the quantities.",
    "assignType": 1,
    "assignee": "PURCHASING",
    "dueDate": "[@ calc(today, \"+3D\") @]",
    "sections": [
      { "caption": "Lines", "name": "lines", "kind": "repeater", "rowsFrom": "{{FindItems_results}}", "allowAdd": true }
    ],
    "fields": [
      { "section": "", "caption": "Delivery date", "name": "deliveryDate", "type": "date", "required": true, "value": "[@ calc(today, \"+7D\") @]", "options": "", "freeText": false, "tableNo": 0, "filters": [] },
      { "section": "", "caption": "Vendor", "name": "vendor", "type": "reference", "required": true, "value": "", "options": "", "freeText": false, "tableNo": 23, "filters": [ { "fieldNo": 39, "filter": "''" } ] },
      { "section": "", "caption": "Priority", "name": "priority", "type": "dropdown", "required": false, "value": "Normal", "options": "Low;Normal;High", "freeText": false, "tableNo": 0, "filters": [] },
      { "section": "lines", "caption": "Item", "name": "item", "type": "reference", "required": true, "value": "{{FindItems_results}}", "options": "", "freeText": false, "tableNo": 27, "filters": [] },
      { "section": "lines", "caption": "Quantity", "name": "quantity", "type": "decimal", "required": true, "value": "1", "options": "", "freeText": false, "tableNo": 0, "filters": [] }
    ],
    "previewKind": 1,
    "previewHtml": "<h3>Request for {{Request_vendor.name}}</h3><p>Delivery: {{Request_deliveryDate}}</p><ul>{#for {{Request_lines}} #}<li>{{Request_lines.quantity}} x {{Request_lines.item}}</li>{#endfor#}</ul>",
    "previewDocument": ""
  },
  "outputs": [
    { "name": "deliveryDate", "type": "value" },
    { "name": "vendor", "type": "reference", "tableNo": 23 },
    { "name": "priority", "type": "value" },
    { "name": "lines", "type": "reference", "tableNo": 5564267, "columns": [
      { "name": "item", "type": "reference", "tableNo": 27 },
      { "name": "quantity", "type": "value" }
    ] },
    { "name": "linesCount", "type": "value" },
    { "name": "completedBy", "type": "value" },
    { "name": "task", "type": "reference", "tableNo": 5564323 }
  ]
}
```

`PURCHASING` must be an existing task group. Field 39 of table 23 is the vendor's *Blocked* field.

## Gotchas

- Do not name a field or section `completedBy` or `task`: the step's own outputs use those names.
- The form is a snapshot. Prefills, dropdown values and offered records do not update while the task waits; only the preview does.
- Only the first 1,000 records are offered by a record field, and only the first 1,000 rows of `rowsFrom` are prefilled. Narrow the table with `filters`, and the list before the step.
- Tell the user which task group or user the flow expects. A missing group or a misspelled user name only fails when the step runs.
- The task's subject is the step's `description`, so name it like the task ("Complete customer data", not "Form").
- A repeater with no `rowsFrom` and `allowAdd` = `false` shows an empty table nobody can fill.
