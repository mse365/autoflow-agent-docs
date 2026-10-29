# Selection task

[← All actions](README.md)

Hands a list to a user or a task group, waits in the background until they have chosen one or more rows, and continues with the chosen records (or values) and their count. The list can be the records of a reference, array or iterator, or a list of plain values.

> **Early access.** This step is part of AutoFlow Tasks and ships with the release after 27.0.40. AutoFlow Tasks is rolled out in stages: it is switched on for selected customers first (portal feature flag `tasks`) and for everyone else a few weeks later. Until it is switched on for an environment, the step is hidden in the editor and publishing refuses it. Only use it when the user confirms AutoFlow Tasks is enabled for them.

| | |
|---|---|
| Enum name | `SelectionTask` |
| Ordinal | `"action": 5564423` |
| Category | Tasks |
| Terminating | `false` |
| Group / edges | No |
| Availability | Dark-launched (AutoFlow Tasks). Background triggers only, the same list as the [Approval task](ApprovalTask.md#where-it-can-be-used). |

## What it does

On its first run the step resolves `input` into rows, with one row per record or value and at most **1,000** rows. Longer lists are cut, which is logged and shown on the task card. For records, each row holds the configured `columns`, resolved against that row's record, or the primary key if no columns are configured. For values, there is one column holding the value. The values are a snapshot taken at this moment.

If the list is empty, no task is created. `onEmpty` then decides: fail the step, or continue with `count` = `"0"`.

Otherwise the step creates a task in the AutoFlow task inbox and the run **parks**. Waiting works exactly as for the [Approval task](ApprovalTask.md#what-it-does): the task is checked every poll interval (default 5 minutes), the run continues at once when the user the flow runs as completes it, the step fails on a cancelled task, each loop pass creates its own task, and a retried run reuses its task.

The person chooses exactly one row, or at least one row with `multiSelect`. If a chosen record was deleted in the meantime, they are asked to change the selection.

## Where it can be used

Background triggers only. The trigger list, the webhook `WaitForResponse` caveat and the SubFlow rule are the same as for the [Approval task](ApprovalTask.md#where-it-can-be-used).

## Licensing

Anyone can be an assignee or a group member, with no seat needed. **Completing** a selection task needs a paid AutoFlow licence **and an AutoFlow Tasks seat**. The exception is `assignType` 2 (the user who started the flow) while they follow the run in its progress dialog, which is free even on the free tier. The editor's status line warns when a fixed assignee has no seat, or no member of a fixed group has one.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `instructions` | string | yes | – | What to choose and why, shown on the task card. Supports SmartFields `{{..}}`, SmartFormulas `[[..]]` and SmartControls `{#..#}`. |
| `assignType` | integer | no | `0` | `0` = user, `1` = task group, `2` = the user who started the flow (`assignee` is ignored). |
| `assignee` | string | unless type 2 | `""` | Type 0: a Business Central **user name** (or user security ID). Type 1: a **task group code**. Case-insensitive and trimmed. Can be a SmartField resolved at runtime. |
| `input` | string | yes | – | Exactly one placeholder `{{name}}` that points to records (a reference, an array such as `{{FindCust_results}}`, or an iterator such as a dotted relation) or to a value or an array of values. The raw form is used. See [selector fields](../references-and-smart-fields.md#16-selector-fields-reference-inputs). |
| `inputKind` | string | no | `"reference"` | `"reference"` or `"value"`. The editor derives it from the input's type. It decides the type of the `results` output. At runtime the step goes by what the input actually holds. |
| `tableNo` | integer | records | `0` | The table of the input's records, which becomes the `tableNo` of `results`. `0` for values. |
| `columns` | array | no | `[]` | Records only: rows of `{ "caption", "value" }`. `value` is SmartText that **starts with the input's name**, e.g. `{{FindCust_results.name}}` for input `{{FindCust_results}}`, and is resolved once per row. Empty: one primary-key column. |
| `valueCaption` | string | no | `""` | Values only: caption above the values. Empty: the input's name. |
| `multiSelect` | boolean | no | `false` | `true`: one or more rows. `false`: exactly one. |
| `onEmpty` | integer | no | `0` | Empty list: `0` = fail the step, `1` = continue with `count` `"0"` and no `results`. |
| `dueDate` | string | no | `""` | A date (`yyyy-mm-dd` is safest) or a SmartDate such as `[[TODAY+5D]]`. If it doesn't resolve to a date, it is ignored silently. |

A column whose SmartFields all start with the input is resolved against the row alone, which is fast. Columns that also use other SmartFields work too, but each row then resolves against the whole flow context.

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `results` | reference (records) / value (values) | = `configuration.tableNo` (records) | The chosen rows, shaped like Find Records: `{{<slug>_results}}` is the first, `{{<slug>_results[0]}}`, `{{<slug>_results[1]}}`, … each one, in list order. Loop over them with For Each (`{{<slug>_results}}`). Not set when the list was empty. |
| `count` | value | – | Number of chosen rows. `"0"` when `onEmpty` = 1 let an empty list through. |
| `completedBy` | value | – | User name of who completed the task. |
| `task` | reference | `5564323` | The task record (`mse365 AF-CO Task`). |

The outputs are written once the task is completed. Write `results` with `"type": "value"` (no `tableNo`) when `inputKind` is `"value"`.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `instructions` or `input` is empty, or `assignee` is empty with `assignType` 0/1 | `Please fill in the highlighted fields.` |
| publish | error | AutoFlow Tasks is not enabled for the environment | `The task step '%1' cannot be published: AutoFlow Tasks is not enabled for this environment.` |
| publish | error | The trigger cannot wait (see [Approval task](ApprovalTask.md#where-it-can-be-used)) | `The task step '%1' cannot be used in this flow: its trigger runs while the user works on the record (or answers right away), so the flow cannot wait for a person there. Use a trigger that runs in the background, such as a record trigger, a schedule or a manual start.` |

`%1` is the step **id**. The step's own messages, including the column check `The column '%1' must use the list to choose from, for example {{%2.Name}}.`, are not run. A column that does not use the input shows the same value in every row.

## Runtime errors

| condition | message |
|---|---|
| Empty list and `onEmpty` = 0. An `input` that is not a single `{{name}}` placeholder also resolves to an empty list. | `The list to choose from (%1) is empty, so there is nothing to choose. To continue instead, set "If the list is empty" to "Continue with no results".` |
| The input holds records and values | `The list to choose from (%1) holds both records and values. Choose a list of records or a list of values.` |
| `assignType` 2 and the run has no user | `The task cannot be assigned to the user who started the flow: the run has no user.` |
| Assignee empty / user missing / user disabled / group missing | The same messages as the [Approval task](ApprovalTask.md#runtime-errors). |
| Tasks switched off, inline frame, SubFlow, cancelled task | The same messages as the [Approval task](ApprovalTask.md#runtime-errors). |

## Example

The step lets a user pick the customers to remind, from the results of a Find Records step with slug `FindCust` on table 18:

```json
{
  "id": "6B1E9A20-3C4D-4E5F-8A9B-0C1D2E3F4A01",
  "type": "action",
  "action": 5564423,
  "description": "Choose customers to remind",
  "slug": "PickCust",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/list-check.svg",
  "terminating": false,
  "configuration": {
    "instructions": "Choose the customers that should get a payment reminder today.",
    "assignType": 2,
    "assignee": "",
    "input": "{{FindCust_results}}",
    "inputKind": "reference",
    "tableNo": 18,
    "columns": [
      { "caption": "No.", "value": "{{FindCust_results.no}}" },
      { "caption": "Name", "value": "{{FindCust_results.name}}" },
      { "caption": "Balance due", "value": "{{FindCust_results.balancedue}}" }
    ],
    "valueCaption": "",
    "multiSelect": true,
    "onEmpty": 1,
    "dueDate": ""
  },
  "outputs": [
    { "name": "results", "type": "reference", "tableNo": 18 },
    { "name": "count", "type": "value" },
    { "name": "completedBy", "type": "value" },
    { "name": "task", "type": "reference", "tableNo": 5564323 }
  ]
}
```

## Gotchas

- `assignType` 2 suits a manually started flow ("pick what to process"). In a background run, the assignee is the user the run executes as (for a schedule, the user who set it up), and they need a seat to complete the task from the inbox.
- Follow the step with a For Each over `{{<slug>_results}}`, or with a Decision on `{{<slug>_count}}` when `onEmpty` is 1.
- Column values are captured when the task is created. They do not update while the task waits.
- Only the first 1,000 rows are offered. Filter the input (e.g. Find Records `limit` / filters) instead of relying on the cut.
