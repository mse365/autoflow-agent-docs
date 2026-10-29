# Flow definition format

A flow definition is a single UTF-8 JSON document. It is what **Export current version** downloads (`AutoFlow_<Code>_<version>.json`, see [Flow Code and versions](#flow-code-and-versions)) and what **Create from file** imports. Everything about a flow's logic lives in this document; environment-specific things (credentials, webhook registrations, the flow's number, folder, licensing) do not.

## Top-level object

```jsonc
{
  "name": "Notify sales on blocked customer",   // flow description
  "code": "ACME.BLOCKED_CUSTOMER",             // flow Code, needed before the flow can be published
  "version": "1.2.0",                          // written by export; informational on import
  "iconUrl": "https://…/icon.svg",             // optional, flow icon
  "steps": [ /* trigger first, then action steps */ ],
  "notes": [ /* optional canvas sticky notes */ ],
  "smartFieldDefs": { /* optional record-path definitions, see references-and-smart-fields.md §1.8 */ },
  "translations": { /* optional, the flow name in other languages, see Translations */ }
}
```

| Key | Type | Required | Notes |
|---|---|---|---|
| `name` | string | yes | Becomes the flow's **Description** on import (truncated to 100 characters). If another flow already has that description, the import appends ` (2)`, ` (3)`, … |
| `code` | string | recommended | Flow **Code**, max 60 characters. Format `[NAMESPACE.]CODE`: `A–Z`, `0–9`, `_`, `-`, at most one `.`, not first or last. BC uppercases it. **Every flow needs a Code before it can be published.** Use your own namespace, e.g. `ACME.BLOCKED-CUSTOMER`. Run SubFlow and Start flow steps call flows by Code. If a flow in the company already has this Code, import offers to add the file as a **new draft version of that flow** instead of creating a new flow (see [Flow Code and versions](#flow-code-and-versions)). A malformed code is skipped without an error. |
| `version` | string | no | Version number `major.minor.patch` of the exported version, e.g. `"1.2.0"`. Written by export (missing for versions from before 27.0.40). On import it is only informational: it is never stored in the definition, and the new draft gets its own number. Don't invent one for a hand-written definition. |
| `iconUrl` | string | no | Must be empty or start with `https://` (case-insensitive). If it doesn't, it is skipped on import. |
| `steps` | array | yes | `steps[0]` **must** be the trigger. The other entries are the top-level action sequence, run in array order. |
| `notes` | array | no | Canvas notes; they have no effect at runtime. See [Notes](#notes). |
| `smartFieldDefs` | object | no | Flow-level definitions of how `{{slug_output.Segment…}}` paths walk related records. See [references-and-smart-fields.md §1.8](references-and-smart-fields.md#18-smartfielddefs-the-flow-level-path-definitions). |
| `translations` | object | no | The flow name in other languages. See [Translations](#translations). |

Only `name`, `code`, `iconUrl` and `version` are read from the root on import (`version` is then removed). The rest of the document is stored verbatim as the flow's draft version. **Import performs no validation**: a malformed definition imports fine and fails later, at publish or at runtime. That's why the checks in [validation.md](validation.md) exist.

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
  "outputs": [ { "name": "Rec", "type": "reference", "tableNo": 18 }, { "name": "ChangedFields", "type": "value" } ],
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
| `translations` | object | no | The step's texts in other languages (description, branch labels, prose configuration keys). See [Translations](#translations). |

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

`color` is one of `yellow`, `pink`, `blue`, `green`, `lavender`, `grey`. In `html`, only `b`, `i`, `u`, `br` and text survive: the editor strips every other tag (keeping its text) when it shows or saves the note. `width` and `height` are optional; leave them out to auto-size.

## Translations

Since 27.0.41 a flow can carry its texts in several languages. The default text stays exactly where it is (`name`, `description`, the edge `description`, the prose keys of `configuration`); the other languages sit next to it in a `translations` map, so a reader that does not know about translations still sees the default text.

```jsonc
{
  "name": "Mahnung versenden",
  "translations": { "ENU": { "name": { "text": "Send reminder", "src": "3f1a…" } } },
  "steps": [ {
    "id": "…", "type": "action", "action": 5564557,
    "description": "Kunde benachrichtigen",
    "configuration": { "Message": "Hallo {{trigger_Rec.name}}", "display": 0,
                       "actions": [ { "label": "Öffnen", "type": "2", "target": "21", "record": "{{trigger_Rec}}" } ] },
    "translations": {
      "ENU": {
        "description":                    { "text": "Notify customer", "src": "9b0c…" },
        "configuration.Message":          { "text": "Hello {{trigger_Rec.name}}", "src": "c4e2…" },
        "configuration.actions[0].label": { "text": "Open", "src": "7a51…" },
        "edge:4D2F…":                     { "text": "Yes", "src": "e019…" }
      }
    }
  } ]
}
```

- **Language key**: the Business Central language code of table *Language*, upper case, e.g. `DEU`, `ENU`, `FRA`. A user sees the language of their Business Central session.
- **Paths** (keys of a language map): on the flow only `name`; on a step `description`, `configuration.<key>` for a prose configuration key, `configuration.<rows>[<index>].<column>` for one row of a repeater (0-based index), and `edge:<edgeId>` for the label of one of the step's own edges.
- **Entry**: `{ "text": "<translation>", "src": "<hash>" }`. `src` is the hash of the default text the translation was made for (16 hex characters, the first 16 of a lower-case SHA-256 of the UTF-8 text). When the default text changes, the translation is *outdated*: still used, but flagged on the Translations worksheet. When you write translations by hand, you may set `src` to `""` – the worksheet then shows them as outdated until someone confirms them, which is the honest state. An empty `text` counts as no translation.
- **Which configuration keys**: only the keys the step declares as prose – the step pages mark them (*Translatable*: …). Technical values (selectors, filters, URLs, codes) are never translated; a translation for such a key is ignored by the editor's worksheet.
- **Fallback**: no translation, or an empty one, means the default text is used. Nothing fails because of a missing translation.
- **Edges**: the branch labels are stored on the *step* (`edge:<id>`), not inside the edge object. When you copy a step, generate new edge ids and rename these keys accordingly, as the editor does.
- **Where it shows**: the execution viewer, the Flow Workspace preview and the flow pickers show descriptions, branch labels and the flow name in the viewer's language. Using the translated *configuration* texts at run time (the message of a notification, the body of an email) is controlled per step by an output language, coming in a later release.

Rename a slug? Translated texts reference the same `{{slug_…}}` tokens as the default text – rewrite them there too.

## What is *not* in the definition

These are environment-local, so an agent can't set them through JSON:

- Flow **No.**, status (draft or published), the version number of the stored version (export adds it as `version`, import ignores it), folder, category.
- Credentials and secrets. Steps reference them by key. Each environment must have matching credential records; see the HTTP Request and Azure Blob pages.
- Webhook URLs and registrations, which are created on publish.
- Licensing.

## Flow Code and versions

- **Code.** Every flow needs a Code before it can be published: *"Flow %1 (%2) has no Code. Enter a Code on the flow card before activating it – for example YOURCOMPANY.FLOW-NAME. The Code identifies the flow across companies and environments."* Codes are unique per company. The Code can be changed on the flow card at any time, unless the flow is linked to a public gallery template or to someone else's template. Changing it breaks Run SubFlow and Start flow steps that call the old Code.
- **Version numbers.** Every version has a number `major.minor.patch`. A new or imported flow starts as draft `0.0.1`. **Edit flow** on a published flow creates a draft with the next patch number (with `0.0.3` active, the draft is `0.0.4`); publishing keeps the number. Minor and major only change through the template gallery. Versions from before 27.0.40 that were neither published nor draft at upgrade time have no number (shown as `–`).
- **Export.** *Export current version* (flow card, Flow Workspace or flow list; on a flow with a draft beside the published version it asks which one) and *Export* on a version in **Flow Versions** add the root `version` key and name the file `AutoFlow_<Code>_<version>.json`, e.g. `AutoFlow_ACME.BLOCKED-CUSTOMER_1.2.0.json`. Without a Code the flow No. is used, and for an unnumbered version its internal ID (and no `version` key).
- **Import when the Code exists.** If a flow in the company already has the file's `code` (compared upper-cased), *Create from file* asks instead of creating a second flow:
  - *"Flow %1 (%2) already has the Code %3. Import the file as a new draft version of that flow?"*
  - If the flow already has an open draft: *"Flow %1 (%2) already has the Code %3 and an open draft (version %4). Import the file as a new draft version of that flow? The current draft stays available in the version history."*
  - If the file's `version` is lower than the flow's highest version, this line is put in front, and the default answer is *No*: *"Caution: the file contains version %1, which is older than the flow's current version %2."*

  **Yes** stores the definition as a new draft with the flow's next version number; **Created From** shows the file's `version`. The flow's description, Code and icon are **not** changed (the file's `name` and `iconUrl` are ignored), and the published version keeps running until the draft is published. Run SubFlow steps are re-pinned as on every import. **No** cancels the import. Without a matching Code, import creates a new flow, as before.
- **Template references.** A flow installed or updated from the gallery also has a read-only **Template reference** version (e.g. `1.3.0`) with a working draft (`1.3.1`). A template reference can't be published (*"Version %1 is a template reference and cannot be activated. Create a draft from it and activate that instead."*). **Update from template** merges your changes with the template's, matching steps, edges and notes by `id`. When you edit the JSON of such a flow, keep existing ids, so your changes merge instead of turning into delete-and-add conflicts. Positions (`x`, `y`), `level`, the root `code`/`version` and Run SubFlow `subFlowVersion` pins are ignored by the merge.
- **Run SubFlow pins** use the SubFlow's version number (`"1.2.0"`), which is the same in every environment. See [Run SubFlow](actions/RunSubFlow.md).

Before 27.0.40: only SubFlows and manual flows needed a Code, versions had no numbers, export named the file `AutoFlow_<FlowNo>_<VersionId>.json` without a `version` key, and a file whose Code already existed was imported as a new flow without a Code.

## Lifecycle: import → draft → publish

1. **Import** (*Create from file*): creates a new flow in **Draft** (version `0.0.1`) with this definition, or, after a confirmation, a new draft version of the flow that already has the file's `code`. No validation runs.
2. **Edit**: the editor rewrites the step you edit (configuration, outputs, slug) and leaves everything else alone.
3. **Publish changes** (activates the draft): runs the publish checks in [validation.md](validation.md). Hard errors block publishing. Warnings ask for confirmation, and a non-interactive (API) publish treats them as *No*, so a flow with warnings can't be published headless.
4. **Run**: runtime errors are logged per step on the execution.
