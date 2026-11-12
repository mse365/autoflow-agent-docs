#!/usr/bin/env python3
"""Repository self-check (run in CI).

1. Every spec file parses and has the required top-level keys.
2. Every JSON block under "## Example" in docs/actions and docs/triggers parses, and a
   minimal flow built around it validates without errors.
3. Every file in examples/ validates without errors or warnings.
4. Generated files (docs/actions/README.md, docs/validation-rules.md, spec/index.json) are up to date.
5. Step pages and specs are generated copies (tools/sync_step_docs.py): every page starts with the
   generated banner, every step is listed in spec/sources.json with the app it comes from, every
   entry there has both files, and the spec's "app" key matches it.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import validate_flow as vf  # noqa: E402
import sync_step_docs as sync  # noqa: E402

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


def check_sources():
    problems = []
    src = ROOT / sync.SOURCES
    if not src.exists():
        return [f"{sync.SOURCES} is missing – run tools/sync_step_docs.py"]
    sources = json.loads(src.read_text(encoding="utf-8"))
    for folder, _kind in sync.KINDS:
        listed = sources.get(folder) or {}
        pages = {p.stem for p in (ROOT / "docs" / folder).glob("*.md") if p.name != "README.md"}
        specs = {p.stem for p in (ROOT / "spec" / folder).glob("*.json")}
        for n in sorted(pages):
            md = ROOT / "docs" / folder / f"{n}.md"
            if not md.read_text(encoding="utf-8").startswith(sync.BANNER_PREFIX):
                problems.append(f"{md.relative_to(ROOT)}: no generated banner – step pages are edited in the app that owns the step, then copied with tools/sync_step_docs.py")
        for n in sorted((pages | specs) - set(listed)):
            problems.append(f"{folder}/{n}: not listed in {sync.SOURCES} – step files come from tools/sync_step_docs.py")
        for n, app in sorted(listed.items()):
            if n not in pages:
                problems.append(f"{sync.SOURCES}: {folder}/{n} has no docs/{folder}/{n}.md")
            if n not in specs:
                problems.append(f"{sync.SOURCES}: {folder}/{n} has no spec/{folder}/{n}.json")
                continue
            spec_app = json.loads((ROOT / "spec" / folder / f"{n}.json").read_text(encoding="utf-8")).get("app")
            expected = None if app == sync.BASE_APP else app
            if spec_app != expected:
                problems.append(f"spec/{folder}/{n}.json: app is {spec_app!r}, {sync.SOURCES} says {expected!r}")
    return problems


def main():
    problems = []
    specs = vf.load_specs()

    for f in sorted((ROOT / "spec").glob("*/*.json")):
        s = json.loads(f.read_text(encoding="utf-8"))
        missing = [k for k in REQUIRED if k not in s]
        if missing:
            problems.append(f"{f.relative_to(ROOT)}: missing {missing}")

    problems += check_sources()

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
                rep = vf.validate({"name": "example", "code": "EXAMPLE.CHECK", "steps": steps}, specs)
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
