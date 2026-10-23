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

## Quick start

```sh
git clone https://github.com/mse365/autoflow-agent-docs.git
python3 autoflow-agent-docs/tools/validate_flow.py my-flow.json
```

Point your agent at `AGENTS.md`. For example, add it to your agent's instructions, or tell Claude Code: *"Read autoflow-agent-docs/AGENTS.md before editing flow JSON."*

Round trip in Business Central:

1. **Export Flow** on an existing flow to get its JSON, or let the agent write a new one.
2. Let the agent edit it, then run the validator.
3. Choose **Create from file** to import it as a new draft flow, review it in the editor, then **Publish**.

## Scope and versioning

- Documents **AutoFlow 27.0**. Only generally available steps are included; steps in preview are added once they ship.
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
