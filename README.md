# AutoFlow agent docs

Agent-facing reference for **AutoFlow flow definitions**: the JSON behind every flow in [AutoFlow](https://autoflow365.app) for Microsoft Dynamics 365 Business Central.

Use it to let an AI agent such as Claude Code, Copilot or Cursor **write or modify flows as JSON**, then import them with *Create from file*. Every step is documented with its configuration keys, outputs, and the validation rules AutoFlow applies. A validator runs those rules locally, so problems surface before you import or publish.

## Contents

| | |
|---|---|
| [AGENTS.md](AGENTS.md) | Start here if you're an agent: workflow and the rules that are easy to get wrong |
| [docs/flow-definition.md](docs/flow-definition.md) | The JSON format: root, trigger, action steps, edges, ids, slugs, outputs, execution order |
| [docs/references-and-smart-fields.md](docs/references-and-smart-fields.md) | `{{slug_output}}` references, field paths, SmartFormula, SmartDate, conditions |
| [docs/triggers/](docs/triggers/README.md) | One page per trigger |
| [docs/actions/](docs/actions/README.md) | One page per action |
| [docs/validation.md](docs/validation.md) | What AutoFlow checks at import, in the editor, at publish and at runtime |
| [docs/validation-rules.md](docs/validation-rules.md) | Every rule of every step, with the exact message text |
| [spec/](spec/) | Machine-readable specs for every step |
| [examples/](examples/) | Complete, valid flow definitions |
| [tools/validate_flow.py](tools/validate_flow.py) | Preflight validator (Python 3, no dependencies) |
| [tools/af_api.py](tools/af_api.py) | Find, export and import flows through the AutoFlow Flow API (Python 3, no dependencies) |

## Quick start

```sh
git clone https://github.com/mse365/autoflow-agent-docs.git
python3 autoflow-agent-docs/tools/validate_flow.py my-flow.json
```

Point your agent at `AGENTS.md`. For example, add it to your agent's instructions, or tell Claude Code: *"Read autoflow-agent-docs/AGENTS.md before editing flow JSON."*

Round trip in Business Central, over the AutoFlow Flow API (the release after 27.0.40), signed in as you:

```sh
export AF_ENVIRONMENT=Production AF_COMPANY="CRONUS AG"
python3 autoflow-agent-docs/tools/af_api.py login                 # once: sign in with a code
python3 autoflow-agent-docs/tools/af_api.py export ACME.INVOICE-MAIL -o flow.json
# … the agent edits flow.json and runs the validator …
python3 autoflow-agent-docs/tools/af_api.py import flow.json      # lands as a draft
```

The import never publishes. It reports what publishing would stop or warn on, and you publish the draft in the flow editor. Setup and permissions: [Give Claude Code access to your flows](https://docs.autoflow365.app/docs/guides/flow-api).

- **On-premises or a container:** set `AF_BASE_URL` to the API root instead of `AF_ENVIRONMENT`, and `AF_USERNAME` / `AF_PASSWORD` for Basic authentication with the user's normal password. Behind a reverse proxy, take the web client URL, append `rest` to the instance segment and add `/api`: web client `https://bc.example.com/f0552b78fae8/` → `AF_BASE_URL=https://bc.example.com/f0552b78fae8rest/api` (`…/f0552b78fae8/api` returns 404).
- **`CERTIFICATE_VERIFY_FAILED` on macOS** with Python from python.org: that build has no CA bundle. `export SSL_CERT_FILE=/etc/ssl/cert.pem`, or run *Install Certificates.command* from its Applications folder.

Without the API, the same round trip works by hand:

1. **Export current version** on an existing flow to get its JSON, or let the agent write a new one.
2. Let the agent edit it, then run the validator.
3. Choose **Create from file** to import it as a draft: a new flow, or a new draft version of the flow that already has the file's `code` (after a confirmation). Review it in the editor, then **Publish changes**.

## Scope and versioning

- Verified against **AutoFlow 27.0.40**, released 23 October 2026. To see your version, open *Extension Management* in Business Central and look at the AutoFlow entry.
- Where older releases behave differently in a way that matters for writing JSON, the page has a short **Before 27.0.40** note.
- Steps that are dark-launched (enabled per environment on request) are included and marked **early access**, for early-access customers and testing. They only work where their feature is enabled, and their details may still change. All other steps are generally available.
- The docs describe behaviour, not internals. Where behaviour was inferred rather than confirmed, the step page says so.
- The flow definition JSON is AutoFlow's own storage format, not a public API with compatibility guarantees. Always validate against the docs for your AutoFlow version.

## Contributing

Found a mismatch between these docs and AutoFlow's behaviour? Please open an issue with the step, the JSON you used, and what happened.

After changing anything in `spec/`, run:

```sh
python3 tools/build_index.py   # regenerates indexes and the rule catalog
python3 tools/check_repo.py    # validates every documented example
```

## License

[MIT](LICENSE) © mse Software GmbH
