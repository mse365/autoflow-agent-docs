#!/usr/bin/env python3
"""Repository self-check (run in CI).

1. Every spec file parses and has the required top-level keys.
2. Every JSON block under "## Example" in docs/actions and docs/triggers parses, and a
   minimal flow built around it validates without errors.
3. Every file in examples/ validates without errors or warnings.
4. Generated files (docs/actions/README.md, docs/validation-rules.md, spec/index.json) are up to date.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import validate_flow as vf  # noqa: E402

FENCE = re.compile(r"```json\s*\n(.*?)\n```", re.S)
REQUIRED = ("kind", "name", "id", "caption", "configuration", "outputs", "rules")
STUB_TRIGGER = {
    "id": "00000000-0000-4000-8000-000000000001", "type": "trigger", "trigger": 100,
    "description": "Manual", "slug": "trigger", "iconUrl": "", "configuration": {}, "outputs": [],
}
STUB_ACTION = {
    "id": "00000000-0000-4000-8000-000000000002", "type": "action", "action": 104,
    "description": "Log", "slug": "StubLog", "iconUrl": "", "terminating": False,
    "configuration": {"Message": "x"}, "outputs": [],
}


def example_blocks(md):
    text = md.read_text(encoding="utf-8")
    m = re.search(r"^## Example.*?(?=^## |\Z)", text, re.S | re.M)
    return FENCE.findall(m.group(0)) if m else []


def main():
    problems = []
    specs = vf.load_specs()

    for f in sorted((ROOT / "spec").glob("*/*.json")):
        s = json.loads(f.read_text(encoding="utf-8"))
        missing = [k for k in REQUIRED if k not in s]
        if missing:
            problems.append(f"{f.relative_to(ROOT)}: missing {missing}")

    checked = 0
    for kind in ("actions", "triggers"):
        for md in sorted((ROOT / "docs" / kind).glob("*.md")):
            if md.name == "README.md":
                continue
            for block in example_blocks(md):
                try:
                    obj = json.loads(block)
                except json.JSONDecodeError as e:
                    problems.append(f"{md.relative_to(ROOT)}: example is not valid JSON ({e})")
                    continue
                if not isinstance(obj, dict) or obj.get("type") not in ("trigger", "action"):
                    continue  # configuration fragment
                steps = [obj, STUB_ACTION] if obj["type"] == "trigger" else [STUB_TRIGGER, obj]
                rep = vf.validate({"name": "example", "steps": steps}, specs)
                for i in rep.items:
                    if i["severity"] == "error":
                        problems.append(f"{md.relative_to(ROOT)}: {i['rule']} {i['where']}: {i['message']}")
                checked += 1

    for ex in sorted((ROOT / "examples").glob("*.json")):
        rep = vf.validate(json.loads(ex.read_text(encoding="utf-8")), specs)
        for i in rep.items:
            if i["severity"] in ("error", "warning"):
                problems.append(f"{ex.relative_to(ROOT)}: {i['severity']} {i['rule']} {i['where']}: {i['message']}")

    generated = ["docs/actions/README.md", "docs/validation-rules.md", "spec/index.json"]
    before = {g: (ROOT / g).read_text(encoding="utf-8") if (ROOT / g).exists() else None for g in generated}
    subprocess.run([sys.executable, str(ROOT / "tools" / "build_index.py")], check=True, capture_output=True)
    for g in generated:
        if (ROOT / g).read_text(encoding="utf-8") != before[g]:
            problems.append(f"{g} was out of date – regenerated, commit it")

    print(f"checked {checked} documented examples")
    for p in problems:
        print("FAIL", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
