# AutoFlow flow definitions: instructions for AI agents

You are working with **AutoFlow** flow definitions: the JSON documents that *Export current version* produces and *Create from file* imports into Microsoft Dynamics 365 Business Central. This repository is your reference, verified against AutoFlow 27.0.40. Use it in place of guessing. If the user's AutoFlow is older, follow the **Before 27.0.40** notes; if it is newer, say that these docs may be out of date.

## Workflow

1. **Read the format first**: [docs/flow-definition.md](docs/flow-definition.md). It covers the root object, the trigger and action step shapes, edges, ids, slugs, outputs and execution order.
2. **Pick the trigger** from [docs/triggers/README.md](docs/triggers/README.md) and **the actions** from [docs/actions/README.md](docs/actions/README.md). Then open each step's page: it lists every configuration key, its type and default, the outputs it produces, its validation rules, and a valid example.
   Steps from a separate app (category *AutoFlow Supplier Foundation*) need that app installed. Read its overview, [docs/apps/SupplierFoundation.md](docs/apps/SupplierFoundation.md), before you write such a flow.
3. **Wire data between steps** with `{{<slug>_<output>}}` tokens. The syntax (field paths, loop items, formulas, dates, conditions) is in [docs/references-and-smart-fields.md](docs/references-and-smart-fields.md).
4. **Validate before you hand over**:
   ```sh
   python3 tools/validate_flow.py flow.json --strict
   ```
   Fix every `error` and `warning`. Explain any `lint` you keep. Then go through the checklist in [docs/validation.md](docs/validation.md#preflight-checklist-for-agents).
5. **Import it, if you have API access**: `python3 tools/af_api.py import flow.json`. It lands as a draft and prints the issues publishing would stop or warn on – fix them and import again (each import is a new draft version, so don't import after every small edit). Never tell the user the flow is live: they review and publish the draft in the flow editor.
6. **Tell the user what the environment needs**: credentials (by code), called SubFlows and manual flows (by Code, imported and published first), number series, dimension codes, tables or fields from extensions, and apps such as AutoFlow Supplier Foundation.

## Rules that are easy to get wrong

- Every flow needs a root `code` (`NAMESPACE.NAME`, e.g. `ACME.BLOCKED-CUSTOMER`) before it can be published. Importing a file whose `code` already exists in the company adds a new draft version to that flow instead of creating a new one, so pick a new `code` for a new flow and keep the existing one when you change a flow.
- `steps[0]` is the trigger, and its slug is always `trigger`.
- Ids are upper-case GUIDs without braces, unique across **steps and edges**. Generate new ones for every new or copied step.
- Slugs match `^[A-Za-z][A-Za-z0-9-]{0,19}$`: no underscore, unique case-insensitively. Renaming a slug means rewriting every `{{oldSlug_…}}` yourself.
- `outputs` are **not** regenerated on import. Write them exactly as the step's page says, and keep them in sync with `configuration`.
- `terminating` must match the step (Error, Return PDF, Set File Name, Return SubFlow Output, Set document field values), and terminating steps must be last in their sequence.
- Group steps need `edges` whose `value`s match what the step returns. **Case** routes on `configuration.branches`, which must agree with `edges`.
- Outputs produced inside a branch or loop body are **discarded** when the group finishes. Create collections and elements *before* the loop that fills them.
- A `{{token}}` that doesn't resolve is left in the text verbatim, with no error. Publish only warns when the **slug** is unknown, not a wrong output name or field. The validator checks output names and scope for you.
- Leaf field names in paths are lower case with punctuation removed: `{{trigger_Rec.selltocustomerno}}`. Hops into related tables need a `smartFieldDefs` reference definition.
- Configuration keys are case-sensitive. Some are capitalised: `Message` (Log, Send Notification) and `Error` (Error).
- Editor-stage rules are **not** checked at publish. Satisfy them anyway; they are what makes the step work.
- Publish warnings block a non-interactive (API) publish.
- Steps marked **early access** (e.g. the AutoFlow Tasks steps *Approval task* and *Selection task*) are dark-launched: they only work where their feature is enabled for the environment, and are refused at publish everywhere else. Use them only when the user asks for them or confirms the feature is enabled, then validate with `--features <feature>`. Task steps also need a trigger that can wait – never an interactive document or page trigger, a PDF/report-file-name trigger or a SubFlow.

## Modifying an existing flow

- Get the current definition first. With API access: `python3 tools/af_api.py list` to find it, then `python3 tools/af_api.py export <code> -o flow.json` (the draft if there is one, else the published version; `--published` forces the published one). Without it, ask the user for the file from **Export current version**.
- Keep the root `code`: that is what makes the import a new draft version of the same flow.
- Change only what you need. Keep existing ids, slugs, `x`/`y` and `notes`.
- After changing a step's configuration, regenerate that step's `outputs`, then re-check every reference to that step.
- When inserting a step, give it a new id and a unique slug. Positions (`x`/`y`) are optional.
- Re-run the validator on the whole document, not just the changed step.

## Flow API access

`tools/af_api.py` calls the AutoFlow Flow API as the signed-in user. It needs `AF_ENVIRONMENT` and `AF_COMPANY` (and `python3 tools/af_api.py login` once, which the **user** completes in the browser). On a `Not signed in` or `HTTP 401` error, ask the user to run `login`; on `HTTP 403`, they lack the AutoFlow permission set `mse365 AF ALL` in that company. The API cannot publish, delete or change setup, so don't look for a way to. If the user has no API access, fall back to export and *Create from file* by hand.

On-premises or on a container, `AF_BASE_URL` (plus `AF_USERNAME` / `AF_PASSWORD`, Basic authentication with the user's normal password) replaces `AF_ENVIRONMENT` and `login`. Behind a reverse proxy, derive it from the web client URL: append `rest` to the instance segment and add `/api` – `https://<host>/<instance>/` becomes `https://<host>/<instance>rest/api`. `https://<host>/<instance>/api` returns 404.

A `CERTIFICATE_VERIFY_FAILED` error while curl works means Python has no CA bundle (python.org builds on macOS): tell the user to `export SSL_CERT_FILE=/etc/ssl/cert.pem` or run *Install Certificates.command*.

## Machine-readable data

- `spec/actions/*.json`, `spec/triggers/*.json`: per-step configuration, outputs, edges and rules ([format](spec/_FORMAT.md)).
- `spec/index.json`: all steps with ordinals.
- `spec/smart-syntax.json`: token grammar, built-in tokens, formula functions, date grammar, condition operators.
