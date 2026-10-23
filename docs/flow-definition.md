# Flow definition format

A flow definition is a single UTF-8 JSON document. It is what **Export Flow** downloads (`AutoFlow_<FlowNo>_<VersionId>.json`) and what **Create from file** imports. Everything about a flow's logic lives in this document; environment-specific things (credentials, webhook registrations, the flow's number, folder, licensing) do not.

## Top-level object

```jsonc
{
  "name": "Notify sales on blocked customer",   // flow description
  "code": "ACME.BLOCKED_CUSTOMER",             // optional, cross-environment identifier
  "iconUrl": "https://…/icon.svg",             // optional, flow icon
  "steps": [ /* trigger first, then action steps */ ],
  "notes": [ /* optional canvas sticky notes */ ],
  "smartFieldDefs": { /* optional record-path definitions, see references-and-smart-fields.md §1.8 */ }
}
```

| Key | Type | Required | Notes |
|---|---|---|---|
| `name` | string | yes | Becomes the flow's **Description** on import (truncated to 100 characters). If another flow already has that description, the import appends ` (2)`, ` (3)`, … |
| `code` | string | no | Flow **Code**, max 60 characters. Format `[NAMESPACE.]CODE`: `A–Z`, `0–9`, `_`, `-`, at most one `.`, not first or last. BC uppercases it. **Required for SubFlows**, since Run SubFlow steps call a SubFlow by its Code. On import the code is skipped without an error if another flow in the company already uses it or if it is malformed. |
| `iconUrl` | string | no | Must be empty or start with `https://` (case-insensitive). If it doesn't, it is skipped on import. |
| `steps` | array | yes | `steps[0]` **must** be the trigger. The other entries are the top-level action sequence, run in array order. |
| `notes` | array | no | Canvas notes; they have no effect at runtime. See [Notes](#notes). |
| `smartFieldDefs` | object | no | Flow-level definitions of how `{{slug_output.Segment…}}` paths walk related records. See [references-and-smart-fields.md §1.8](references-and-smart-fields.md#18-smartfielddefs-the-flow-level-path-definitions). |

Only `name`, `code` and `iconUrl` are read from the root on import. The rest of the document is stored verbatim as the flow's draft version. **Import performs no validation**: a malformed definition imports fine and fails later, at publish or at runtime. That's why the checks in [validation.md](validation.md) exist.

## Trigger step (`steps[0]`)

```json
{
  "id": "6F1C2B0A-3D4E-4F50-8A9B-0C1D2E3F4A5B",
  "type": "trigger",
  "trigger": 5564450,
  "description": "Customer modified",
  "slug": "trigger",
  "iconUrl": "https://…",
  "configuration": { },
  "outputs": [ { "name": "record", "type": "reference", "tableNo": 18 } ],
  "level": 0
}
```

| Key | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | Unique step id (see [Ids](#ids)). |
| `type` | `"trigger"` | yes | |
| `trigger` | integer | yes | Trigger enum ordinal. See [triggers/README.md](triggers/README.md). |
| `description` | string | yes | Label on the canvas. |
| `slug` | string | yes | Always `"trigger"`. Downstream steps reference trigger outputs as `{{trigger_<output>}}`. |
| `iconUrl` | string | recommended | The trigger's standard icon. Used for display only. |
| `configuration` | object | yes | Trigger-specific; see the trigger's page. Use `{}` when it has none. |
| `outputs` | array | yes | What the trigger exposes to later steps. **Generate these exactly as documented** on the trigger's page, because reference resolution and the field pickers read them. |
| `level` | integer | no | Written as `0`. The engine ignores stored `level` values (see [Nesting](#nesting-edges-and-execution-order)). |

## Action step

```json
{
  "id": "0B7E5D84-91A2-4C3F-B6D7-E8F9A0B1C2D3",
  "type": "action",
  "action": 5564413,
  "description": "Send email to sales",
  "slug": "SendEmailToSales",
  "iconUrl": "https://…",
  "terminating": false,
  "configuration": { },
  "outputs": [ ]
}
```

| Key | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | Unique across the whole definition, including edge ids. |
| `type` | `"action"` | yes | Only steps with `type: "action"` are executed and validated as actions. |
| `action` | integer | yes | Action enum ordinal. See [actions/README.md](actions/README.md). An unknown ordinal fails at runtime with *"Step '%1' has no valid action in the flow definition."* |
| `description` | string | yes | Canvas label. Also used to name the step in validation messages. |
| `slug` | string | yes | Reference name for this step's outputs. See [Slugs](#slugs). |
| `iconUrl` | string | recommended | The action's standard icon. The editor derives the block colour from it (for example error, sub-flow and start-flow icons). |
| `terminating` | boolean | yes | Must match the action's definition (`true` for Error, SubFlow Output, …). A terminating step must be the **last** step in its sequence and must have no edges. |
| `configuration` | object | yes | Action-specific; see the action's page. |
| `outputs` | array | yes | Must match what the action generates from its configuration. See the action's page. |
| `edges` | array | group steps only | Branches or loop bodies. See below. |
| `customIconUrl` | string | no | Display-only icon override (Run SubFlow writes the called flow's icon here). |
| `x`, `y` | integer | no | Canvas position relative to the parent: the canvas for top-level steps, the parent group for nested ones. Omit them to auto-layout. |
| `status` | object | no | Written by the editor for run visualisation; ignored at runtime. Omit it. |
| `level` | integer | no | Ignored on read. Omit it. |

## Edges (group steps)

Group steps (Decision, Case, For Each Loop, While Loop, …) carry `edges`. Each edge holds a nested step sequence:

```json
"edges": [
  { "id": "…", "value": "true",  "description": "Yes", "steps": [ /* action steps */ ] },
  { "id": "…", "value": "false", "description": "No",  "steps": [ ] }
]
```

| Key | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | Unique, same format as step ids. |
| `value` | string | yes | Matched **exactly** (string comparison) against the value the group step returns at runtime. Use the values from the step's page. For dynamic edges (Case), they're derived from the configuration. |
| `description` | string | yes | Branch label. |
| `steps` | array | yes | Nested steps. Use `[]` for an empty branch. |
| `x`, `y` | integer | no | Anchor position of the empty-branch placeholder. |

## Nesting, edges and execution order

- Steps in one `steps` array run in order. The trigger runs first, then `steps[1]`, `steps[2]`, ….
- When a group step finishes, it reports an **edge value**. The engine looks up the edge with that `value`. If it has at least one step, execution continues with that edge's first step. If no edge matches, or the matching edge is empty, execution continues after the group step.
- When the last step of an edge finishes, control returns to the **group step**. If the group step asked to repeat (loops), it runs again with the next iteration. Otherwise execution continues with the step after the group.
- `level` is derived from the JSON path (the number of `edges` you're nested under) and is never read from the stored value.
- Loop iterations get iteration ids such as `1`, `1-2`. They appear in run history but don't change how you reference data inside a loop body. See [references-and-smart-fields.md](references-and-smart-fields.md).
- **Output lifetime:** when control leaves a group step, the outputs of every step inside its edges are discarded. Loops do this on every pass. Nothing after a group, and no loop condition, can read outputs produced inside a branch. Create collections and elements **before** the group that fills them.
- The engine gives every action an `iteration` output (1-based).
- A step that fails is retried from that same step when the run is restarted.

## Ids

Ids are GUIDs **without braces**, as AL `Format(CreateGuid())` prints them, upper case:

```
"id": "3F2504E0-4F89-41D3-9A0C-0305E82C3301"
```

They must be unique across all steps **and** edges in the definition, because lookups use them as keys. When you write new steps, generate fresh UUID v4 values and upper-case them. When you copy steps, **regenerate** the ids of the copied steps and edges.

## Slugs

A slug names a step so other steps can reference its outputs (`{{<slug>_<output>}}`).

- Grammar: `^[A-Za-z][A-Za-z0-9-]{0,19}$`. Letter first, letters/digits/hyphens, max **20** characters, **no underscore**, because `_` separates the slug from the output name.
- Unique within the definition. Generated slugs are compared case-insensitively, so treat `SendMail` and `sendmail` as a collision.
- `trigger` is reserved for the trigger step.
- The editor generates slugs as PascalCase from the description, with umlauts transliterated, a leading non-letter stripped, and a numeric suffix `2`, `3`, … on collision (`SendEmail`, `SendEmail2`).
- Renaming a slug in the editor rewrites all `{{oldSlug_…}}` references in the flow. When you rename by hand, **you** must rewrite every reference too.

Full reference syntax: [references-and-smart-fields.md](references-and-smart-fields.md).

## Outputs

```json
{ "name": "statusCode", "type": "value" }
{ "name": "record", "type": "reference", "tableNo": 18 }
```

- `value`: a scalar or text value.
- `reference`: a record reference into BC table `tableNo`. Downstream steps can navigate its fields. See [references-and-smart-fields.md](references-and-smart-fields.md).

The editor regenerates `outputs` from `configuration` every time a step is saved. If you write JSON by hand, produce exactly what the step's page documents. Stale outputs show up as dangling references or broken field pickers.

## Notes

Canvas sticky notes, display only:

```json
{ "id": "…", "html": "Runs <b>nightly</b>", "color": "yellow", "x": 40, "y": 320, "width": 220, "height": 120 }
```

`color` is one of `yellow`, `pink`, `blue`, `green`, `lavender`, `grey`. `html` is sanitised to `b`, `i`, `u`, `br` and text. `width` and `height` are optional; leave them out to auto-size.

## What is *not* in the definition

These are environment-local, so an agent can't set them through JSON:

- Flow **No.**, status (draft or published), published and draft version ids, folder, category.
- Credentials and secrets. Steps reference them by key. Each environment must have matching credential records; see the HTTP Request and Azure Blob pages.
- Webhook URLs and registrations, which are created on publish.
- Licensing.

## Lifecycle: import → draft → publish

1. **Import** (*Create from file*): creates a new flow in **Draft** with this definition. No validation runs.
2. **Edit**: the editor rewrites the step you edit (configuration, outputs, slug) and leaves everything else alone.
3. **Publish**: runs the publish checks in [validation.md](validation.md). Hard errors block publishing. Warnings ask for confirmation, and a non-interactive (API) publish treats them as *No*, so a flow with warnings can't be published headless.
4. **Run**: runtime errors are logged per step on the execution.
