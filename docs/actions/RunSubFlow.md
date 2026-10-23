# Run SubFlow

[← All actions](README.md)

Calls another flow (a SubFlow) inline. Typed inputs go in, and the SubFlow's declared outputs come back as outputs of this step.

| | |
|---|---|
| Enum name | `RunSubFlow` |
| Ordinal | `"action": 5564411` |
| Category | SubFlows |
| Terminating | `false` |
| Group / edges | No |
| Availability | GA. Hidden from the generic step picker: every published SubFlow appears as its own tile, which creates this step. |

## What it does

The step looks up the SubFlow by its **Code** and loads the pinned version. It then projects the input bindings onto the SubFlow trigger's outputs and runs the SubFlow body **synchronously, inside the caller's transaction**. There is no commit between the caller and the SubFlow.

The SubFlow stops when it reaches a **Return SubFlow Output** step. The JSON object that step builds becomes this step's outputs. A SubFlow that reaches its end without such a step returns nothing, which is not an error.

Errors inside the SubFlow fail this step with the inner error message unchanged. Inside the SubFlow:

- Sleep and other deferrals are not allowed.
- HTTP yields (Respond to webhook) are not allowed.
- Nesting is limited (default depth 32, set in AutoFlow Setup).

## How the called flow is identified

- **Code, not No.** `configuration.subFlowCode` holds the SubFlow's **Code**: the flow's `Code` field, format `[NAMESPACE.]CODE`, e.g. `ACME.CUSTOMER_LOOKUP`. The flow No. comes from a number series, means nothing in another company or environment, and never appears in the step.
- **Code rules.** A SubFlow can't be published without a Code (*"A Code must be set on the Flow Card before this SubFlow can be published. Run-SubFlow steps and templates reference SubFlows by Code, not by No."*). Once the flow has been published, the Code can't be changed to another value; only the **Reset Code** action on the flow card clears it, and that breaks all callers. Codes are unique per company. Other flows don't need a Code.
- **What travels with the SubFlow.** Export writes the Code to the root `code` property. Save as template also writes it into the SubFlow trigger's configuration (`subFlowCode`, `iconUrl`).
- **Import restores the Code.** On import ("Create from file", template install), the Code is put back onto the new flow, unless another flow in that company already uses it or it is malformed. In that case the import still succeeds, but the new flow has no Code until you set one by hand.

### The version pin (`subFlowVersion`)

In 27.0.39, `subFlowVersion` is an **integer**: the internal ID of a SubFlow version record in *this* database. It is not a version number, and the same ID means something else (or nothing) in another company or environment. The editor shows it as "Version %1".

At run time the pin must be the ID of an existing version **of that SubFlow**. There is **no automatic fallback** to the published version: a missing pin, an unknown ID, or the ID of another flow's version is a run-time error.

Don't write the pin as a string. A string such as `"1.2.0"` can't be read as an integer, so import and the run fail.

### Re-pinning on import

After "Create from file", a template install, an "Update from template" or "Duplicate", every Run SubFlow step in the definition, including steps nested in edges, is re-pinned:

1. If a flow with `subFlowCode` exists in the target company: a pin that is the ID of one of **its** versions is kept. Any other pin (absent, unknown, or another flow's version) is replaced by that SubFlow's **currently published version ID**.
2. If no flow has that Code, or it has no published version, the step is left exactly as imported and the import still succeeds. The step fails at run time until the SubFlow is installed and published and the step is re-pinned: open and confirm the step (it re-resolves through the Code the same way), or import the caller again.
3. `inputBindings` are never touched. They are keyed by parameter **name**.

**For hand-written JSON, leave out `subFlowVersion`** and import the caller after the SubFlow is published in the target company; import then fills in the published version. Write an integer pin only when you copy it from an export of the same database.

Recommended order: **import and publish the SubFlow first, then import the callers.**

"Save as template" removes `subFlowVersion` from every Run SubFlow step, and fails if a referenced SubFlow Code is not published in the source company.

> **Next release (not in 27.0.39):** the pin becomes the SubFlow's version **number** as a string, e.g. `"1.2.0"`, which is the same in every environment, and every flow gets a mandatory Code. Integer pins keep working there. Leaving `subFlowVersion` out of hand-written JSON works in both releases.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `subFlowCode` | string (≤ 60) | yes | `""` | Code of the SubFlow (see above). No SmartFields. |
| `subFlowVersion` | integer | yes at run time | – | Version pin: the internal ID of one of the SubFlow's versions in this database (see above). Leave it out in hand-written JSON; import fills it in when the SubFlow is published in the target. Never a string. |
| `inputBindings` | object | no | `{}` | `{ "<paramName>": "<expression>" }`. Keys are the SubFlow trigger's `inputs[].name` (case-sensitive). For **Value** inputs the expression is any SmartText (`{{trigger_Rec.no}}`, literals, formulas). For **Reference** inputs it must be a **flat** wrapped selector `{{name}}` that names a reference in the calling flow, e.g. `{{trigger_Rec}}`: no dots, no `[n]`. Anything else is passed as plain text. Keys that match no declared input are still passed in, but the editor drops them when the step is confirmed. |
| `customIconUrl` | string | no | `""` | Display only. The SubFlow's icon, copied by the editor and mirrored to the step's top-level `customIconUrl`. |

### Input contract (the SubFlow trigger side)

The called flow starts with the trigger **When invoked as a SubFlow** (`"trigger": 5564404`). Its configuration declares the inputs:

```json
"configuration": {
  "inputs": [
    { "name": "CustomerNo", "type": "Value", "required": true },
    { "name": "Customer", "type": "Reference", "tableNo": 18, "required": false }
  ],
  "subFlowCode": "ACME.CUSTOMER_LOOKUP",
  "iconUrl": ""
}
```

- Keep `name` to letters, digits and `_`, and unique. Nothing checks this, but the name becomes part of a `{{trigger_<name>}}` token.
- `type` is `"Value"` or `"Reference"`. `tableNo` is only written for Reference inputs; `0` means any table.
- `required` is shown in the editor but **not enforced at run time**. A missing binding simply leaves the input empty.
- Inside the SubFlow, each input is a trigger output: `{{<triggerSlug>_<name>}}`, normally `{{trigger_CustomerNo}}`. `<triggerSlug>_<name>` is cut to 30 characters, so with the slug `trigger` keep input names to 22 characters.
- `subFlowCode` and `iconUrl` in the trigger configuration are only written when the SubFlow is saved as a template. They let import restore the flow's Code and icon.

## Outputs

The editor builds this step's `outputs[]` from the `configuration.outputs` of the **Return SubFlow Output** step in the SubFlow version it resolves: the pinned version if it belongs to the SubFlow, otherwise the currently published one. If the SubFlow has several such steps, the first one found (document order, depth-first into edges) counts. If the Code is unknown in this company, the step gets no outputs.

| name | type | tableNo | notes |
|---|---|---|---|
| *each SubFlow output `name`* | value, or reference when declared `"Reference"` | the declared `tableNo` (reference only) | Names are truncated to 30 characters. |

Downstream: `{{<thisStepSlug>_<outputName>}}`, e.g. `{{CustomerLookup_CreditLimit}}`.

At run time every returned entry is added as a **value** output that holds the text the SubFlow returned. Return scalar values (a No., a SystemId) when the caller needs a record; Reference-typed returns don't arrive as records (see [Return SubFlow Output](SubFlowOutput.md#gotchas)).

## Validation

The step has no publish check of its own. The generic dangling-slug warning still applies.

| stage | severity | rule | message |
|---|---|---|---|
| editor (status line) | warning | No flow with this Code, or it has no published version. Doesn't block saving, but confirming the step then clears all `inputBindings`. | SubFlow "%1" is not installed on this system, or has no published version. Install and publish it, then reopen this step. |
| editor (status line) | warning | A Reference binding points at a different table than the input's `tableNo`. Doesn't block saving. | Parameter "%1" expects a reference to table %2, but the selected reference resolves to table %3. |
| editor | info | A newer published version exists; the dialog offers a one-click switch | A newer version of this SubFlow is available. |
| save as template | error | A referenced Code is not published in this company | Run-SubFlow step references SubFlow Code "%1", but no SubFlow with that Code is published on this tenant. Publish the missing SubFlow first, or remove the Run-SubFlow step before saving as template. |

## Runtime errors

| condition | message |
|---|---|
| `subFlowCode` empty or unknown | No SubFlow with Code "%1" exists in this company. |
| Pin missing, `0` or not an existing version ID | SubFlow %1 has no published version pinned in the call (version %2). |
| Pin is a version of another flow (typical after copying JSON between databases) | SubFlow %1 is pinned to version %2, which belongs to a different flow. The call was imported from another system; open the step and pick the version to run. |
| Nesting too deep (AutoFlow Setup, default 32) | Maximum SubFlow nesting depth (%1) exceeded. Call chain: %2. |
| Empty definition | SubFlow %1 version %2 has an empty definition. |
| No steps | SubFlow %1 version %2 has no trigger step. |
| Sleep inside the SubFlow | Step %1 (%2) requested a deferred resume, but the flow is running synchronously. Use Sleep or other time-based deferral steps only outside of synchronous frames (Webhook sync phase or SubFlow body). |
| Respond to webhook inside the SubFlow | Step %1 (%2) requested an HTTP yield, but it is running inside a SubFlow. Yield is only valid in the synchronous phase of a Webhook flow. |
| An error in a SubFlow step | That step's own error message. |

## Example

A hand-written call, without a pin; import pins it to the published version of `ACME.CUSTOMER_LOOKUP`:

```json
{
  "id": "5F4DCC3B-5AA7-4C0D-9E1A-2B3C4D5E6F70",
  "type": "action",
  "action": 5564411,
  "description": "Customer lookup",
  "slug": "CustomerLookup",
  "iconUrl": "https://statics.autoflow.mse365.de/icons/subtask.svg",
  "customIconUrl": "",
  "terminating": false,
  "configuration": {
    "subFlowCode": "ACME.CUSTOMER_LOOKUP",
    "inputBindings": {
      "CustomerNo": "{{trigger_Rec.selltocustomerno}}",
      "Customer": "{{FindCustomer_Rec}}"
    },
    "customIconUrl": ""
  },
  "outputs": [
    { "name": "CreditLimit", "type": "value" },
    { "name": "Blocked", "type": "value" }
  ]
}
```

After import (or in an export) the configuration also carries an integer pin, e.g. `"subFlowVersion": 42`.

(`trigger_Rec` and `FindCustomer_Rec` stand for outputs of earlier steps in the calling flow.)

## Gotchas

- A Code mismatch is silent until run time. Check that `subFlowCode` matches the SubFlow's Code; it is compared upper-cased.
- Don't open and confirm the step before the SubFlow is installed and published: with nothing to resolve, the parameter grid is empty and confirming saves empty `inputBindings`.
- When a SubFlow's inputs or outputs change, publish a new SubFlow version and switch the callers to it. The old pin keeps running the old version.
- Bindings for inputs that no longer exist are dropped when you confirm the step in the editor. Keep parameter names stable.
- The SubFlow runs as part of the caller's execution. In the execution log, its steps appear under this step.
