#!/usr/bin/env python3
"""Regenerate docs/actions/README.md, docs/validation-rules.md and spec/index.json from the spec files.

The step specs and pages themselves are generated from the apps that own the steps by
tools/sync_step_docs.py, which runs this script at the end.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(root, kind):
    out = []
    for f in sorted((root / "spec" / kind).glob("*.json")):
        s = json.loads(f.read_text(encoding="utf-8"))
        out.append(s)
    return out


STAGES = ["import", "publish", "editor", "runtime"]


def esc(t):
    return (t or "").replace("|", "\\|").replace("\n", " ")


def write_rules_catalog(root, actions, triggers):
    lines = [
        "# Validation rule catalog",
        "",
        "Generated from `spec/` by `tools/build_index.py`. Do not edit by hand.",
        "",
        "Rules are grouped by stage (see [validation.md](validation.md)): **publish** rules are what AutoFlow enforces before a flow goes live, **editor** rules are what the step's configuration dialog enforces (not re-checked at publish, but a definition that breaks them usually fails at runtime), and **runtime** rules are errors raised while a step runs.",
        "",
    ]
    for stage in STAGES:
        rows = []
        for s in triggers + actions:
            for r in s.get("rules") or []:
                if r.get("stage") == stage and r.get("severity") != "info":
                    kind = "triggers" if s.get("kind") == "trigger" else "actions"
                    rows.append(f"| [{s.get('caption')}]({kind}/{s['name']}.md) | {r.get('severity')} | {esc(r.get('check'))} | {esc(r.get('message'))} | {'yes' if r.get('machine') else ''} |")
        if not rows:
            continue
        lines += [f"## Stage: {stage}", "", "| Step | Severity | Check | Message | Auto-checked |", "|---|---|---|---|:---:|"] + rows + [""]
    (root / "docs" / "validation-rules.md").write_text("\n".join(lines), encoding="utf-8")


def build(root=ROOT):
    """Write the generated files under root; returns (number of actions, number of triggers)."""
    root = Path(root)
    actions = load(root, "actions")
    triggers = load(root, "triggers")

    index = {
        "actions": [{k: s.get(k) for k in ("name", "id", "caption", "category", "terminating", "group", "availability", "feature", "app") if (k not in ("feature", "app") or s.get(k))} for s in actions],
        "triggers": [{k: s.get(k) for k in ("name", "id", "caption", "category", "availability", "app") if k != "app" or s.get(k)} for s in triggers],
    }
    (root / "spec" / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    by_cat = {}
    for s in actions:
        by_cat.setdefault(s.get("category") or "Other", []).append(s)
    lines = [
        "# Actions",
        "",
        "Every action step has `\"type\": \"action\"` and `\"action\": <ordinal>`. The ordinal is the number stored in the JSON; the name is the enum value name used for the file names here.",
        "",
        "- **Terminating** steps must be the last step in their sequence (`\"terminating\": true`).",
        "- **Group** steps carry `edges` with nested step sequences.",
        "- Steps with an `app` in [`spec/index.json`](../../spec/index.json) come from a separate app and only exist where that app is installed.",
    ]
    if any(s.get("availability") == "dark-launched" for s in actions):
        lines.append("- **Early access** steps are released in stages (selected customers first, everyone a few weeks later): they only work where their AutoFlow feature is already switched on. Use them only when the user confirms it is.")
    lines += [
        "",
        "Machine-readable list: [`spec/index.json`](../../spec/index.json). The step pages and specs are generated from the apps that own the steps; see [app-step-docs.md](../app-step-docs.md).",
        "",
    ]
    for cat in sorted(by_cat):
        lines += [f"## {cat}", "", "| Action | `action` | Terminating | Group | Page |", "|---|---:|:---:|:---:|---|"]
        for s in sorted(by_cat[cat], key=lambda x: x.get("caption") or x["name"]):
            lines.append(
                f"| {s.get('caption')}{' (early access)' if s.get('availability') == 'dark-launched' else ''} | `{s['id']}` | {'yes' if s.get('terminating') else ''} | {'yes' if s.get('group') else ''} | [{s['name']}]({s['name']}.md) |"
            )
        lines.append("")
    (root / "docs" / "actions" / "README.md").write_text("\n".join(lines), encoding="utf-8")
    write_rules_catalog(root, actions, triggers)
    return len(actions), len(triggers)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    actions, triggers = build(Path(argv[0]) if argv else ROOT)
    print(f"{actions} actions, {triggers} triggers indexed")


if __name__ == "__main__":
    main()
