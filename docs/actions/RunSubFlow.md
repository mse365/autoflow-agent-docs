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
- **Code rules.** A SubFlow cannot be published without a Code. Once it has been published, the Code is locked; only an explicit "Reset Code" clears it, and that breaks all callers. Codes are unique per company.
- **What travels with the SubFlow.** When you export a SubFlow or save it as a template, its Code is written to the root `code` property and into its trigger configuration (`subFlowCode`, `iconUrl`).
- **Import restores the Code.** On import ("Create from file", template install), the Code is put back onto the new flow, unless another flow in that company already uses it. In that case the import still succeeds, but the new flow has no Code until you set one by hand.

### The version pin (`subFlowVersion`)

`subFlowVersion` stores which SubFlow version the call runs:

- **Current format**: the version **number** as a string with a dot, e.g. `"1.2.0"`. It is the same in every environment.
- **Legacy format**: an integer local version ID, which only means something in the database that issued it.

At run time the pin must resolve to an existing version of that SubFlow. There is **no automatic fallback** to "latest": a missing or unresolvable pin is a run-time error.

### What happens on import into another environment

After "Create from file", a template install or an "Update from template", every Run SubFlow step in the definition, including steps nested in edges, is re-pinned:

1. If a flow with `subFlowCode` exists in the target company **and** has a published version: a pin that is absent, unknown, or belongs to another flow is replaced by that SubFlow's **currently published version**. A pin that already resolves to one of its own versions is kept.
2. If the SubFlow is **not** there yet, or is not published, the step is left exactly as imported and the import still succeeds. The step will fail at run time until the SubFlow is installed and published, and the step is then re-pinned. You re-pin it by opening and confirming the step, which re-resolves through the Code, or by importing the caller again.
3. `inputBindings` are never touched. They are keyed by parameter **name** and are replayed by name against whatever version is resolved.

Recommended order: **import and publish the SubFlow first, then import the callers.** In a hand-written definition you may leave out `subFlowVersion` if the SubFlow is already published in the target company when you import.

"Save as template" also fails if a referenced SubFlow Code is not published in the source company, and it converts legacy integer pins to version numbers.

## Configuration

| key | type | required | default | description |
|---|---|---|---|---|
| `subFlowCode` | string (≤ 60) | yes | `""` | Code of the SubFlow (see above). No SmartFields. |
| `subFlowVersion` | string or integer | effectively yes | – | Version pin: a version number string such as `"1.2.0"`, or a legacy integer ID. It may be omitted when importing, if the SubFlow is already published in the target (import fills it in). |
| `inputBindings` | object | no | `{}` | `{ "<paramName>": "<expression>" }`. Keys are the SubFlow trigger's `inputs[].name` (case-sensitive). For **Value** inputs the expression is any SmartText (`{{trigger_Rec.no}}`, literals, formulas). For **Reference** inputs it must be a **flat** wrapped selector `{{name}}` that names a reference in the calling flow, e.g. `{{trigger_Rec}}`: no dots, no `[n]`. |
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

- `name` uses letters, digits and `_` only, and must be unique.
- `type` is `"Value"` or `"Reference"`. `tableNo` is only written for Reference inputs; `0` means any table.
- `required` is shown in the editor but **not enforced at run time**. A missing binding simply leaves the input empty.
- Inside the SubFlow, each input is a trigger output: `{{<triggerSlug>_<name>}}`, normally `{{trigger_CustomerNo}}`.
- `subFlowCode` and `iconUrl` in the trigger configuration are only written when the SubFlow is saved as a template. They let import restore the flow's Code and icon.

## Outputs

This step's `outputs[]` mirror the `configuration.outputs` of the **Return SubFlow Output** step in the pinned SubFlow version. If the pin does not resolve, the currently published version is used. If the SubFlow has several such steps, the first one found (document order, depth-first into edges) counts.

| name | type | tableNo | notes |
|---|---|---|---|
| *each SubFlow output `name`* | value, or reference when declared `"Reference"` | the declared `tableNo` (reference only) | Names are truncated to 30 characters. |

Downstream: `{{<thisStepSlug>_<outputName>}}`, e.g. `{{CustomerLookup_CreditLimit}}`.

At run time every returned entry is added as a **value** output that holds the text the SubFlow returned. Non-scalar JSON is serialized. Return scalar values (a No., a SystemId) when the caller needs a record; Reference-typed returns are not reliable (see [Return SubFlow Output](SubFlowOutput.md#gotchas)).

## Validation

| stage | severity | rule | message |
|---|---|---|---|
| editor | error | `subFlowCode` empty, or the pin does not resolve to a positive version ID | *(no message – the step counts as not configured)* |
| editor (status line) | error | No SubFlow with this Code, or it has no published version | SubFlow "%1" is not installed on this system, or has no published version. Install and publish it, then reopen this step. |
| editor (status line) | error | A Reference binding points at a different table than the input's `tableNo` | Parameter "%1" expects a reference to table %2, but the selected reference resolves to table %3. |
| editor | info | A newer published version exists | A newer version of this SubFlow is available. (one-click "Switch to version %1") |
| save as template | error | The referenced Code is not published in this company | Run-SubFlow step references SubFlow Code "%1", but no SubFlow with that Code is published on this tenant. Publish the missing SubFlow first, or remove the Run-SubFlow step before saving as template. |

No step-specific publish check exists. The generic dangling-slug warning still applies.

## Runtime errors

| condition | message |
|---|---|
| Unknown Code | No SubFlow with Code "%1" exists in this company. |
| Pin missing or unresolvable | SubFlow %1 has no published version pinned in the call (version %2). |
| Legacy pin belongs to another flow | SubFlow %1 is pinned to version %2, which belongs to a different flow. The call was imported from another system; open the step and pick the version to run. |
| Nesting too deep | Maximum SubFlow nesting depth (%1) exceeded. Call chain: %2. |
| Empty definition | SubFlow %1 version %2 has an empty definition. |
| No steps | SubFlow %1 version %2 has no trigger step. |
| Sleep inside the SubFlow | Step %1 (%2) requested a deferred resume, but the flow is running synchronously. Use Sleep or other time-based deferral steps only outside of synchronous frames (Webhook sync phase or SubFlow body). |
| Respond to webhook inside the SubFlow | Step %1 (%2) requested an HTTP yield, but it is running inside a SubFlow. Yield is only valid in the synchronous phase of a Webhook flow. |
| An error in a SubFlow step | That step's own error message. |

## Example

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
    "subFlowVersion": "1.0.0",
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

(`trigger_SelltoCustomerNo` and `FindCustomer_Rec` stand for outputs of earlier steps in the calling flow.)

## Gotchas

- A Code mismatch is silent until run time. Check that `subFlowCode` matches the SubFlow's Code exactly; it is compared upper-cased.
- When a SubFlow's inputs or outputs change, publish a new SubFlow version and switch the callers to it. The old pin keeps running the old contract.
- Renamed SubFlow inputs drop the old binding when you confirm the step in the editor. Keep parameter names stable.
- The SubFlow runs as part of the caller's execution. In the execution log, its steps appear under this step, as a child execution.
