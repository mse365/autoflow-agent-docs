# Approval task

[← All actions](README.md)

Asks a user or a task group to approve or reject, waits in the background until the task is decided, and continues along the Approved or Rejected branch.

> **Early access.** This step is part of AutoFlow Tasks and ships with the release after 27.0.40. AutoFlow Tasks is rolled out in stages: it is switched on for selected customers first (portal feature flag `tasks`) and for everyone else a few weeks later. Until it is switched on for an environment, the step is hidden in the editor and publishing refuses it. Only use it when the user confirms AutoFlow Tasks is enabled for them.

| | |
|---|---|
| Enum name | `ApprovalTask` |
| Ordinal | `"action": 5564560` |
| Category | Tasks |
| Terminating | `false` |
| Group / edges | Yes: two fixed edges, `"true"` (Approved) and `"false"` (Rejected) |
| Availability | Dark-launched (AutoFlow Tasks). Background triggers only; see [Where it can be used](#where-it-can-be-used). |

## What it does

On its first run the step resolves its configuration and creates a task in the AutoFlow task inbox. The task's subject is the step's `description` (or the flow's description if that is empty), and the task card shows `instructions` and the attachments. The assignee gets an e-mail, or every group member does for a group (plus a delegate while the assignee is out of office), unless they turned new-task e-mails off.

The run then **parks**. No session is held, so a task can stay open for days. The engine wakes the step up every poll interval (AutoFlow Setup *Task Poll Interval (Min.)*, default 5 minutes) to check the task:

- **Still open**: park again.
- **Approved / rejected**: write the outputs, then take edge `"true"` or `"false"`.
- **Cancelled** (by an administrator, or because the run was deleted): the step fails.

When the user the flow runs as decides the task themselves, the run continues at once instead of at the next check.

Decision rules: an assignee or group member approves or rejects, and a rejection needs a comment. With a group and `requiredApprovals` > 1, the task completes when that many *different* members have approved, and the first rejection rejects it.

Each pass of a loop creates its own task. A retried or restarted run finds the task it already created instead of creating a second one.

## Where it can be used

The flow has to be able to wait, so the step is refused (hard publish error) and hidden in the step list when the trigger runs inline:

| Trigger | `trigger` |
|---|---|
| When a record is created or modified (interactive) | `5564529` |
| When a document is released (interactive) | `5564543` |
| When a document is posted (interactive) | `5564549` |
| When a document is reopened (interactive) | `5564409` |
| When a page is opened (interactive) | `5564407` |
| When a page is closed (interactive) | `5564408` |
| When a PDF is printed | `5564405` |
| When a report file name is generated | `5564406` |
| When invoked as a SubFlow | `5564404` |

Use record triggers (insert/modify/delete), Scheduled, Manual or Webhook instead. In a Webhook flow with `WaitForResponse`, place the step **after** Respond to Webhook. In the synchronous phase it cannot park, so it fails. A flow that is run as a SubFlow fails at the step at runtime, whatever its trigger.

## Licensing

Anyone can be an assignee or a group member: any enabled Business Central user, with no AutoFlow Tasks seat needed. **Deciding** an approval needs a paid AutoFlow licence.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `instructions` | string | yes | – | What the approver should check, shown on the task card. Supports SmartFields `{{..}}`, SmartFormulas `[[..]]` and SmartControls `{#..#}`. |
| `assignType` | integer | no | `0` | `0` = user, `1` = task group. Any other value counts as user. |
| `assignee` | string | yes | – | Type 0: a Business Central **user name** (or user security ID). Type 1: a **task group code**. Case-insensitive and trimmed. Can be a SmartField resolved at runtime, e.g. `{{trigger_Rec.assignedUserId}}`. |
| `requiredApprovals` | integer | no | `1` | Groups only: how many different members must approve. Values below 1 count as 1. More than 1 needs `assignType` 1 and at least that many group members. |
| `dueDate` | string | no | `""` | A date (`yyyy-mm-dd` is safest) or a SmartDate such as `[[TODAY+5D]]`. If it doesn't resolve to a date, it is ignored silently. Overdue tasks are highlighted in the inbox. |
| `attachments` | array | no | `[]` | Rows of `{ "type", "reference", "url", "caption" }`, described below. The editor always writes the array. |

Attachment rows:

| field | used for | description |
|---|---|---|
| `type` | all | `"record"` (a record the approver can open), `"document"` (a file to preview and download: an AutoFlow document or an Incoming Document Attachment record) or `"link"`. |
| `reference` | record, document | Exactly one placeholder `{{name}}` that points to a reference, an array or an iterator (see [selector fields](../references-and-smart-fields.md#16-selector-fields-reference-inputs)). **Each record it holds becomes one attachment**, so `{{FindLines_results}}` attaches every found record. |
| `url` | link | SmartText. If it is exactly one placeholder holding an array of values, each value becomes a link. |
| `caption` | all | SmartText caption, used for every attachment the row produces. |

A row that resolves to nothing is skipped without an error. An empty list is no reason to stop an approval.

## Edges

| value | default description | taken when |
|---|---|---|
| `true` | `Approved` | the task was approved |
| `false` | `Rejected` | the task was rejected |

Keep the order `true` then `false`.

## Outputs

| name | type | tableNo | notes |
|---|---|---|---|
| `result` | value | – | `"true"` / `"false"`. The engine routes on it. |
| `approved` | value | – | Same as `result`. |
| `comment` | value | – | Approved: all approvers' comments joined with `; `. Rejected: the rejecting comment. |
| `decidedBy` | value | – | Approved: the approvers' user names joined with `, `. Rejected: the rejecting user. |
| `task` | reference | `5564323` | The task record (`mse365 AF-CO Task`), e.g. for a link in a follow-up e-mail. |

The outputs are written only once the task is decided.

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `instructions` or `assignee` is empty | `Please fill in the highlighted fields.` |
| publish | error | AutoFlow Tasks is not enabled for the environment | `The task step '%1' cannot be published: AutoFlow Tasks is not enabled for this environment.` |
| publish | error | The trigger is one of those listed under [Where it can be used](#where-it-can-be-used) | `The task step '%1' cannot be used in this flow: its trigger runs while the user works on the record (or answers right away), so the flow cannot wait for a person there. Use a trigger that runs in the background, such as a record trigger, a schedule or a manual start.` |

`%1` is the step **id**. Both publish checks are hard errors, not "publish anyway" warnings. The step's own messages (`Enter the instructions for the approver.`, `Choose who approves: a user or a task group.`, `At least one approval is needed.`, `More than one approval needs a task group as the assignee.`) are not run.

## Runtime errors

| condition | message |
|---|---|
| AutoFlow Tasks was switched off after publishing | `AutoFlow Tasks is not enabled for this environment.` |
| Running inline (backstop for the publish check) | `Task steps cannot run in a trigger that runs while the user works on the record (for example when a document is released, posted or modified). Run the task from a flow with a background trigger instead.` |
| The flow runs as a SubFlow | `Task steps cannot run inside a sub-flow. Put the task step into the calling flow.` |
| `assignee` resolves to empty | `The task has no assignee. Choose a user or a group in the step.` |
| User does not exist | `The task cannot be assigned to user %1: the user does not exist.` |
| User is disabled | `The task cannot be assigned to user %1: the user is disabled.` |
| Group does not exist | `The task cannot be assigned to group %1: the group does not exist.` |
| `requiredApprovals` > 1 without a group | `A task that needs more than one approval must be assigned to a group.` |
| `requiredApprovals` > group member count | `The task needs %1 approvals, but group %2 has only %3 member(s).` |
| The task was cancelled while the flow waited | `Task %1 was cancelled by %2: %3` |

## Example

```json
{
  "id": "4D7A2C10-8B3E-4F21-9C5D-1E2F3A4B5C01",
  "type": "action",
  "action": 5564560,
  "description": "Approve purchase order",
  "slug": "ApprovePO",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/check-circle.svg",
  "terminating": false,
  "configuration": {
    "instructions": "Please check purchase order {{trigger_Rec.no}} for {{trigger_Rec.buyfromvendorname}}.",
    "assignType": 1,
    "assignee": "PURCHASING",
    "requiredApprovals": 1,
    "dueDate": "[[TODAY+3D]]",
    "attachments": [
      { "type": "record", "reference": "{{trigger_Rec}}", "url": "", "caption": "Purchase order" }
    ]
  },
  "outputs": [
    { "name": "result", "type": "value" },
    { "name": "approved", "type": "value" },
    { "name": "comment", "type": "value" },
    { "name": "decidedBy", "type": "value" },
    { "name": "task", "type": "reference", "tableNo": 5564323 }
  ],
  "edges": [
    { "id": "4D7A2C10-8B3E-4F21-9C5D-1E2F3A4B5C02", "value": "true", "description": "Approved", "steps": [] },
    { "id": "4D7A2C10-8B3E-4F21-9C5D-1E2F3A4B5C03", "value": "false", "description": "Rejected", "steps": [] }
  ]
}
```

`PURCHASING` must be an existing task group, and the `trigger_…` placeholders are illustrative.

## Gotchas

- Tell the user which **task group** or user the flow expects. Task groups are set up in Business Central (*AutoFlow Task Groups*), and a missing group only fails when the step runs.
- The task's subject is the step's `description`, so make it meaningful ("Approve purchase order", not "Approval").
- A SmartField `assignee` is only checked at runtime. A misspelled user name fails the step, not the publish.
- Outputs from inside the Approved/Rejected branches are discarded when the step finishes, like any group step.
