#!/usr/bin/env python3
"""Regenerate docs/actions/README.md and spec/index.json from the spec files."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(kind):
    out = []
    for f in sorted((ROOT / "spec" / kind).glob("*.json")):
        s = json.loads(f.read_text(encoding="utf-8"))
        out.append(s)
    return out


STAGES = ["import", "publish", "editor", "runtime"]


def esc(t):
    return (t or "").replace("|", "\\|").replace("\n", " ")


def write_rules_catalog(actions, triggers):
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
    (ROOT / "docs" / "validation-rules.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    actions = load("actions")
    triggers = load("triggers")

    index = {
        "actions": [{k: s.get(k) for k in ("name", "id", "caption", "category", "terminating", "group", "availability")} for s in actions],
        "triggers": [{k: s.get(k) for k in ("name", "id", "caption", "category", "availability")} for s in triggers],
    }
    (ROOT / "spec" / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

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
        "",
        "Machine-readable list: [`spec/index.json`](../../spec/index.json).",
        "",
    ]
    for cat in sorted(by_cat):
        lines += [f"## {cat}", "", "| Action | `action` | Terminating | Group | Page |", "|---|---:|:---:|:---:|---|"]
        for s in sorted(by_cat[cat], key=lambda x: x.get("caption") or x["name"]):
            lines.append(
                f"| {s.get('caption')} | `{s['id']}` | {'yes' if s.get('terminating') else ''} | {'yes' if s.get('group') else ''} | [{s['name']}]({s['name']}.md) |"
            )
        lines.append("")
    (ROOT / "docs" / "actions" / "README.md").write_text("\n".join(lines), encoding="utf-8")
    write_rules_catalog(actions, triggers)
    print(f"{len(actions)} actions, {len(triggers)} triggers indexed")


if __name__ == "__main__":
    main()
