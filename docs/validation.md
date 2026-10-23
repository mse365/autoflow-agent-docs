# Validation: what AutoFlow checks, and when

AutoFlow checks a flow definition at four stages. Knowing which stage a rule belongs to tells you how strictly to treat it.

| Stage | When | Effect of a failure |
|---|---|---|
| **import** | *Create from file* | Almost nothing is checked. The definition is stored as-is (as a new flow, or as a new draft version of the flow that already has its `code`). |
| **editor** | A step's configuration dialog is confirmed in the flow editor | The dialog refuses to save. Mostly these are required fields (*"Please fill in the highlighted fields."*) plus a few step-specific checks. **They are not re-run at publish**, so a hand-written definition can skip them. Treat them as requirements anyway: a definition that breaks them nearly always fails at runtime. |
| **publish** | *Publish changes* on a draft (activates it) | **error**: publish is refused. **warning**: the user is asked to confirm. A non-interactive (API) publish answers *No*, so a flow with warnings can't be published headless. |
| **runtime** | While a step runs | The step fails, the run stops with status *Error* and the message is logged. A restart retries the failed step. |

Run the preflight validator before handing a definition to a user:

```sh
python3 tools/validate_flow.py my-flow.json          # human-readable
python3 tools/validate_flow.py my-flow.json --json   # machine-readable
python3 tools/validate_flow.py my-flow.json --strict # also fail on warnings
```

It reports `error` (AutoFlow refuses the definition or it will certainly fail), `warning` (publish asks for confirmation) and `lint` (AutoFlow doesn't check this, but it's almost certainly a mistake).

## Import

What *Create from file* does with the root:

| Input | Behaviour |
|---|---|
| File encoding | Read as UTF-8. |
| `name` | New flow only: becomes the flow description, truncated to 100 characters. A duplicate description gets ` (2)`, ` (3)`, … appended. |
| `code` | If a flow in the company already has this Code (compared upper-cased), import asks whether to add the file as a **new draft version of that flow**; *No* cancels the import. The questions are listed in [flow-definition.md](flow-definition.md#flow-code-and-versions). That flow's description, Code and icon stay as they are. Otherwise a new flow is created and gets the Code if it is valid; a malformed Code is **silently dropped**, and the flow can't be published until a Code is set. |
| `version` | Informational. A lower version than the flow's highest one adds a caution to the question above. Removed from the stored definition; the draft gets the flow's next version number (`0.0.1` for a new flow). |
| `iconUrl` | New flow only: applied only if it starts with `https://`. Otherwise it is silently dropped. |
| everything else | Stored verbatim as the draft. `outputs` are **not** regenerated, and steps are not validated. |
| Run SubFlow steps | A pin that names a version of the called SubFlow in this company is kept. Otherwise the step is re-pinned to the SubFlow's published version (written as its version number), if that SubFlow exists and is published. If not, the step is left unchanged and fails at runtime. **Import and publish SubFlows before the flows that call them.** See [Run SubFlow](actions/RunSubFlow.md#re-pinning-on-import). |

## Publish

Checks run in this order. The first hard error stops the publish.

1. **Permission.** The user must be allowed to publish flows.
2. **Code** (error). Every flow needs a Code: *"Flow %1 (%2) has no Code. Enter a Code on the flow card before activating it – for example YOURCOMPANY.FLOW-NAME. The Code identifies the flow across companies and environments."* Set it with the root `code` on import.
3. **Not a template reference** (error): *"Version %1 is a template reference and cannot be activated. Create a draft from it and activate that instead."* Only possible for flows from the template gallery.
4. **At least one action step** (error). The message: *"A flow must contain at least one action step before it can be published. Add a step after the trigger and try again."* Action steps inside edges count.
5. **Trigger configuration** (error). Wrapped as *"This flow's trigger cannot be published:"* followed by a bulleted list. Only these triggers have such checks: Manual, the four interactive document triggers (modified, released, posted, reopened) and the two page triggers. See each trigger's page.
6. **Step warnings**, collected for every action step and confirmed together:
   - **Terminating step with a successor**: *"Step "%1" is a terminating step but has a successor – terminating steps must end the path."* This is decided by the step's own `terminating` flag in the JSON, so the flag must be correct.
   - **Step-specific publish checks**: Sleep (duration), Confirm dialog (dialog in a non-interactive or post-write position), Send Notification (actions and targets). See [validation-rules.md](validation-rules.md#stage-publish).
   - **Dangling references**: *"Step "%1" references unknown slug "%2"."* AutoFlow scans every string inside every step's `configuration`. For each `{{…}}`, it takes the text before the **first underscore** as a slug and warns if no step has that slug. Tokens without an underscore, such as built-ins like `{{today}}`, are skipped. The check doesn't look at output names or field paths, so `{{trigger_Typo}}` passes publish and then silently resolves to the literal text at runtime. The validator's `reference.unknown-output` lint catches this.
7. **Licensing** (error). SubFlows don't count toward the flow limit and skip this step. Republishing a flow that is already counted needs no new slot. The messages:
   - Free tier full (2 published flows per production environment; sandboxes are unlimited, every paid license model has unlimited flows): *"All flows of the AutoFlow free tier in this environment are in use. To publish this flow, unpublish another one, or license AutoFlow in the AutoFlow portal (portal.mse365.de) for unlimited flows."*
   - AutoFlow not activated in the company, or the license expired: *"Your tenant is not registered with the licensing server. Please contact support."*
   - *"The licensing server is currently unreachable. Please try again later."* and *"Flow registration failed. Please try again later."*
8. **Trigger registration**: job queue entries (scheduled, global record triggers), webhook registration, and so on. Some triggers check their configuration only here, as hard errors that undo the whole publish:
   - **When a PDF is printed** and **When a report file name is generated**: at least one report line, and only one published flow per trigger in the environment. See their pages.
   - **Webhook**: registration problems, including a production environment without a paid license, are reported on the flow card, not as errors.

Before 27.0.40: only SubFlows and Manual flows needed a Code (with their own messages), and a full license said *"You have no licensed flows remaining. Please upgrade your package in the AutoFlow Licensing page."*

## What is never checked by AutoFlow (but breaks flows)

These are the most common silent failures. The validator flags most of them.

- **Wrong output name or field path** in a `{{…}}` token. Unresolved tokens are left in the text **verbatim** with no error, and SmartFormulas `[[…]]` in the same text are then not evaluated either.
- **Stale `outputs`** that no longer match the configuration. Downstream references and field pickers break.
- **Wrong `terminating` flag.** A terminating step with the flag set to `false` escapes the publish warning but still ends the path at runtime.
- **Edge values that don't match** what the group step returns. That branch is never taken. For **Case**, routing uses `configuration.branches`, so it and `edges` must agree.
- **Outputs used outside their scope.** Outputs produced inside a branch or loop body are discarded when control leaves the group.
- **Duplicate ids** across steps and edges. Lookups return the first match.
- **Steps under the wrong trigger.** The step picker hides trigger-specific steps such as Respond to Webhook, Return PDF and Set File Name, but publish doesn't reject them. They then do nothing or fail at runtime.
- **Environment-specific references**: credential codes, flow Codes (Run SubFlow, Start flow) and SubFlow version pins, number series, dimension codes, table, field, page and report numbers from extensions. The JSON is accepted, but the target must exist in the environment.
- **Synchronous contexts.** Steps that wait or defer, such as Sleep with a deferral, fail when they're reached in a synchronous run: the webhook wait phase, SubFlow bodies, and interactive triggers.

## Preflight checklist for agents

Before you hand a definition over:

1. `steps[0]` is the trigger with `slug: "trigger"`. Its `trigger` ordinal and `configuration` follow the trigger's page, and `outputs` are generated as documented.
2. Every action has a known `action` ordinal, the correct `terminating` flag, `configuration` and `outputs` as documented, and `edges` if it is a group step.
3. Ids are unique GUIDs (upper case, no braces). Slugs match `^[A-Za-z][A-Za-z0-9-]{0,19}$` and are unique, case-insensitive.
4. Every `{{slug_output…}}` points at a step that runs **earlier on the same path**, at an output that step really has, and isn't inside a finished branch or loop.
5. Terminating steps are last in their sequence.
6. All editor-stage rules on each step's page are met. They aren't enforced at publish, but they are what makes the step work.
7. The root `code` is set (every flow needs one to be published), and environment dependencies (credentials, Codes of called flows, tables and fields from extensions) are listed for the user.
8. `python3 tools/validate_flow.py flow.json --strict` reports no errors or warnings, except dangling-reference warnings you can explain.

All rules, by step: [validation-rules.md](validation-rules.md).
