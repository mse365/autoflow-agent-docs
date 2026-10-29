#!/usr/bin/env python3
"""Preflight validator for AutoFlow flow definition JSON.

Mirrors the checks AutoFlow runs at import, publish and (where statically knowable)
runtime, plus the per-step rules recorded in ../spec. Standard library only.

Usage:
    python3 tools/validate_flow.py flow.json [more.json ...] [--json] [--strict] [--features tasks]

--features names the dark-launched AutoFlow features (portal feature flags) the user confirmed are
enabled for their environment; steps that need one of them are then not reported as early access.

Exit code: 0 = no errors (warnings allowed unless --strict), 1 = errors found, 2 = bad input.

Severities:
    error    AutoFlow will refuse this (publish hard stop) or it will certainly fail at runtime.
    warning  AutoFlow's publish asks for confirmation; a headless/API publish fails.
    lint     Not checked by AutoFlow, but very likely a mistake.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC_DIR = ROOT / "spec"

GUID_RE = re.compile(r"^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$")
SLUG_RE = re.compile(r"^[A-Za-z][A-Za-z0-9-]{0,19}$")
CODE_RE = re.compile(r"^[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)?$")
NOTE_COLORS = {"yellow", "pink", "blue", "green", "lavender", "grey"}
JSON_TYPES = {
    "string": str,
    "boolean": bool,
    "object": dict,
    "array": list,
}


# --------------------------------------------------------------------------- spec loading

def load_specs():
    specs = {"action": {}, "trigger": {}}
    for kind, folder in (("action", "actions"), ("trigger", "triggers")):
        d = SPEC_DIR / folder
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.json")):
            try:
                spec = json.loads(f.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:  # pragma: no cover - repo integrity
                print(f"warning: cannot read spec {f}: {e}", file=sys.stderr)
                continue
            if isinstance(spec.get("id"), int):
                specs[kind][spec["id"]] = spec
    return specs


# --------------------------------------------------------------------------- helpers

class Report:
    def __init__(self):
        self.items = []

    def add(self, severity, rule, where, message):
        self.items.append({"severity": severity, "rule": rule, "where": where, "message": message})

    def count(self, severity):
        return sum(1 for i in self.items if i["severity"] == severity)


def get_path(obj, dotted):
    cur = obj
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return False, None
    return True, cur


def is_empty(v):
    return v is None or (isinstance(v, str) and v.strip() == "") or (isinstance(v, (list, dict)) and len(v) == 0)


def type_ok(value, value_type):
    if value_type in ("number", "decimal"):
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if value_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    py = JSON_TYPES.get(value_type)
    return True if py is None else isinstance(value, py)


def iter_strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for v in node.values():
            yield from iter_strings(v)
    elif isinstance(node, list):
        for v in node:
            yield from iter_strings(v)


def placeholder_slugs(text):
    """Same algorithm as AutoFlow's dangling-reference check: for every {{...}} take the part
    before the first underscore as the slug (placeholders without an underscore are ignored)."""
    out = []
    rest = text
    while True:
        p = rest.find("{{")
        if p < 0:
            return out
        rest = rest[p + 2:]
        e = rest.find("}}")
        if e < 0:
            return out
        inner = rest[:e]
        u = inner.find("_")
        if u > 0:
            out.append((inner[:u], inner[u + 1:]))
        rest = rest[e + 2:]


# --------------------------------------------------------------------------- walking

def walk_steps(steps, path, parent=None):
    """Yield (step, path, siblings, index, parent_step) recursively, descending into edges."""
    for i, step in enumerate(steps):
        p = f"{path}[{i}]"
        yield step, p, steps, i, parent
        if isinstance(step, dict) and isinstance(step.get("edges"), list):
            for j, edge in enumerate(step["edges"]):
                if isinstance(edge, dict) and isinstance(edge.get("steps"), list):
                    yield from walk_steps(edge["steps"], f"{p}.edges[{j}].steps", step)


def visible_slugs(steps, inherited=("trigger",), path="$.steps"):
    """Yield (step, path, visible) where visible = slugs whose outputs are in scope for the step:
    the trigger, earlier siblings on the path (but not what ran inside their branches, which is
    discarded when the group finishes), enclosing group steps, and the step itself."""
    seen = list(inherited)
    for i, step in enumerate(steps):
        p = f"{path}[{i}]"
        if not isinstance(step, dict):
            continue
        slug = step.get("slug") if isinstance(step.get("slug"), str) else None
        here = seen + ([slug] if slug else [])
        yield step, p, set(here)
        if isinstance(step.get("edges"), list):
            for j, edge in enumerate(step["edges"]):
                if isinstance(edge, dict) and isinstance(edge.get("steps"), list):
                    yield from visible_slugs(edge["steps"], tuple(here), f"{p}.edges[{j}].steps")
        if slug:
            seen.append(slug)


def label(step, where):
    if isinstance(step, dict) and step.get("description"):
        return f'{where} "{step["description"]}"'
    return where


# --------------------------------------------------------------------------- checks

def check_root(doc, r):
    if not isinstance(doc, dict):
        r.add("error", "root.object", "$", "Definition must be a JSON object.")
        return False
    if not isinstance(doc.get("name"), str) or not doc["name"].strip():
        r.add("error", "root.name", "$.name", "'name' must be a non-empty string (becomes the flow description).")
    elif len(doc["name"]) > 100:
        r.add("lint", "root.name-length", "$.name", "'name' is longer than 100 characters and will be truncated on import.")
    code = doc.get("code")
    if code in (None, ""):
        r.add("error", "root.code-required", "$.code",
              "Every flow needs a Code before it can be published (AutoFlow 27.0.40 and later). "
              "Add a root 'code' such as \"ACME.FLOW-NAME\", or set it on the flow card after import.")
    else:
        if not isinstance(code, str) or len(code) > 60 or not CODE_RE.match(code):
            r.add("error", "root.code", "$.code",
                  'Code must be empty or match <NAMESPACE.>CODE – letters A–Z, digits, "_" and "-" only, '
                  'with at most one "." separator and no empty halves (max 60 chars). Import silently drops an invalid code.')
    icon = doc.get("iconUrl")
    if icon not in (None, "") and (not isinstance(icon, str) or not icon.lower().startswith("https://")):
        r.add("warning", "root.iconUrl", "$.iconUrl", 'Icon URL must be empty or start with "https://" (it is dropped on import otherwise).')
    steps = doc.get("steps")
    if not isinstance(steps, list) or not steps:
        r.add("error", "root.steps", "$.steps", "'steps' must be a non-empty array whose first entry is the trigger.")
        return False
    notes = doc.get("notes")
    if notes is not None:
        if not isinstance(notes, list):
            r.add("error", "notes.array", "$.notes", "'notes' must be an array.")
        else:
            for i, n in enumerate(notes):
                w = f"$.notes[{i}]"
                if not isinstance(n, dict):
                    r.add("error", "notes.object", w, "Note must be an object.")
                    continue
                for k in ("id", "html", "color", "x", "y"):
                    if k not in n:
                        r.add("lint", "notes.key", w, f"Note is missing '{k}'.")
                if n.get("color") not in NOTE_COLORS:
                    r.add("lint", "notes.color", w, f"Note color must be one of {sorted(NOTE_COLORS)}.")
    return True


def check_steps(doc, specs, r, strict_outputs, features=()):
    steps = doc["steps"]
    ids = {}
    slugs = {}  # lower -> original
    slug_outputs = {}  # slug -> set(output names)
    action_count = 0

    trig = steps[0]
    if not isinstance(trig, dict) or trig.get("type") != "trigger":
        r.add("error", "trigger.first", "$.steps[0]", "The first step must be the trigger (type \"trigger\").")
    flow_trigger = trig.get("trigger") if isinstance(trig, dict) else None
    for step, where, siblings, idx, parent in walk_steps(steps, "$.steps"):
        if not isinstance(step, dict):
            r.add("error", "step.object", where, "Step must be an object.")
            continue
        sid = step.get("id")
        if not isinstance(sid, str) or not sid:
            r.add("error", "step.id", where, "Step needs a string 'id'.")
        else:
            if not GUID_RE.match(sid):
                r.add("lint", "step.id-format", where, "Ids are normally GUIDs without braces (e.g. 3F2504E0-4F89-41D3-9A0C-0305E82C3301).")
            if sid.upper() in ids:
                r.add("error", "step.id-unique", where, f"Duplicate id '{sid}' (also at {ids[sid.upper()]}). Ids must be unique across steps and edges.")
            else:
                ids[sid.upper()] = where
        for e_i, edge in enumerate(step.get("edges") or []) if isinstance(step.get("edges"), list) else []:
            if isinstance(edge, dict) and isinstance(edge.get("id"), str):
                eu = edge["id"].upper()
                ew = f"{where}.edges[{e_i}]"
                if eu in ids:
                    r.add("error", "step.id-unique", ew, f"Duplicate id '{edge['id']}' (also at {ids[eu]}).")
                else:
                    ids[eu] = ew

        stype = step.get("type")
        is_root_first = where == "$.steps[0]"
        if stype == "trigger":
            if not is_root_first:
                r.add("error", "trigger.position", where, "Only steps[0] may be a trigger.")
            check_trigger(step, where, specs, r, features)
        elif stype == "action":
            action_count += 1
            check_action(step, where, siblings, idx, specs, r, features, flow_trigger)
        else:
            r.add("error", "step.type", where, "Step 'type' must be \"trigger\" (steps[0]) or \"action\".")

        if not isinstance(step.get("description"), str):
            r.add("lint", "step.description", where, "Step should have a string 'description' (used as label and in messages).")

        slug = step.get("slug")
        if stype == "trigger":
            if slug != "trigger":
                r.add("error", "trigger.slug", where, "The trigger's slug must be \"trigger\".")
        elif stype == "action":
            if not isinstance(slug, str) or not SLUG_RE.match(slug):
                r.add("error", "step.slug", where,
                      f"Slug {slug!r} is invalid: letter first, then letters/digits/'-', max 20 chars, no underscore.")
            elif slug == "trigger":
                r.add("error", "step.slug-reserved", where, "Slug 'trigger' is reserved for the trigger step.")
            elif slug.lower() == "trigger":
                r.add("lint", "step.slug-reserved", where, f"Slug '{slug}' differs from the trigger's slug only in case; pick a distinct slug.")
        if isinstance(slug, str) and slug:
            if slug in slugs.values() and stype == "action":
                r.add("error", "step.slug-unique", where, f"Slug '{slug}' is already used by another step. Slugs must be unique.")
            elif slug.lower() in slugs and stype == "action":
                r.add("lint", "step.slug-unique-ci", where,
                      f"Slug '{slug}' differs from '{slugs[slug.lower()]}' only in case. "
                      "The editor treats that as a collision; pick a distinct slug.")
            slugs[slug.lower()] = slug
            names = set()
            for o in step.get("outputs") or [] if isinstance(step.get("outputs"), list) else []:
                if isinstance(o, dict) and isinstance(o.get("name"), str):
                    if stype == "trigger":
                        # trigger outputs are registered as <slug>_<name>, cut at 30 characters,
                        # so only the truncated name resolves
                        names.add(o["name"][:max(0, 30 - len(slug) - 1)])
                    else:
                        names.add(o["name"])
            slug_outputs[slug] = names

        if not isinstance(step.get("configuration"), dict):
            r.add("error", "step.configuration", where, "'configuration' must be an object ({} when empty).")
        outs = step.get("outputs")
        if not isinstance(outs, list):
            r.add("error", "step.outputs", where, "'outputs' must be an array ([] when none).")
        else:
            for o_i, o in enumerate(outs):
                ow = f"{where}.outputs[{o_i}]"
                if not isinstance(o, dict) or not isinstance(o.get("name"), str) or o.get("type") not in ("value", "reference"):
                    r.add("error", "output.shape", ow, "Output must be {name, type: \"value\"|\"reference\"[, tableNo]}.")
                elif o["type"] == "reference" and not (isinstance(o.get("tableNo"), int) and o["tableNo"] > 0):
                    r.add("error", "output.tableNo", ow, "A reference output needs a positive integer 'tableNo'.")

    # lint: steps that only work with certain triggers (spec "worksWithTriggers")
    flow_trigger = trig.get("trigger") if isinstance(trig, dict) else None
    for step, where, *_ in walk_steps(steps, "$.steps"):
        if not isinstance(step, dict) or step.get("type") != "action":
            continue
        spec = specs["action"].get(step.get("action")) if isinstance(step.get("action"), int) else None
        allowed = (spec or {}).get("worksWithTriggers")
        if allowed and flow_trigger not in allowed:
            r.add("lint", "action.trigger-mismatch", where,
                  f"{spec.get('caption')} only works in flows on trigger {', '.join(str(a) for a in allowed)}; "
                  f"here it does nothing.")

    # publish: at least one action
    if action_count == 0:
        r.add("error", "publish.empty-flow", "$.steps",
              "A flow must contain at least one action step before it can be published. Add a step after the trigger and try again.")

    # lint: references to steps that are not in scope at this point of the path
    if len(steps) > 1:
        for step, where, visible in visible_slugs(steps, inherited=()):
            if not isinstance(step.get("configuration"), dict):
                continue
            for s in iter_strings(step["configuration"]):
                for ref_slug, _ in placeholder_slugs(s):
                    if ref_slug in slug_outputs and ref_slug not in visible:
                        r.add("lint", "reference.out-of-scope", where,
                              f"'{ref_slug}' is not in scope here: it runs later, on another branch, or inside a group "
                              f"whose branch outputs are discarded when the group finishes.")

    # publish: dangling references (mirrors AutoFlow) + lint: unknown output names
    for step, where, *_ in walk_steps(steps, "$.steps"):
        if not isinstance(step, dict) or not isinstance(step.get("configuration"), dict):
            continue
        for s in iter_strings(step["configuration"]):
            for ref_slug, rest in placeholder_slugs(s):
                if ref_slug not in slug_outputs:
                    r.add("warning", "publish.dangling-reference", where,
                          f'Step "{step.get("description", "")}" references unknown slug "{ref_slug}".')
                elif strict_outputs:
                    out_name = re.split(r"[.\[|:;]", rest, maxsplit=1)[0]  # ;<format> suffix
                    known = slug_outputs[ref_slug]
                    if known and out_name not in known | {"iteration"}:  # engine adds 'iteration' to every action
                        r.add("lint", "reference.unknown-output", where,
                              f"'{{{{{ref_slug}_{rest}}}}}': step '{ref_slug}' has no output named '{out_name}' (has: {', '.join(sorted(known))}).")


def check_trigger(step, where, specs, r, features=()):
    t = step.get("trigger")
    if not isinstance(t, int) or isinstance(t, bool):
        r.add("error", "trigger.ordinal", where, "'trigger' must be the trigger enum ordinal (integer).")
        return
    spec = specs["trigger"].get(t)
    if spec is None:
        if specs["trigger"]:
            r.add("error", "trigger.unknown", where, f"Unknown trigger ordinal {t}. See docs/triggers/README.md.")
        return
    check_availability(spec, where, r, features)
    check_config_rules(spec, step.get("configuration"), where, r)


def check_action(step, where, siblings, idx, specs, r, features=(), flow_trigger=None):
    a = step.get("action")
    if not isinstance(a, int) or isinstance(a, bool):
        r.add("error", "action.ordinal", where, "'action' must be the action enum ordinal (integer).")
        return
    spec = specs["action"].get(a)
    term = step.get("terminating")
    if not isinstance(term, bool):
        r.add("lint", "action.terminating-type", where, "'terminating' should be a boolean.")
    edges = step.get("edges")
    has_edges = isinstance(edges, list) and len(edges) > 0

    # publish: terminating step must end its path
    if term is True and (idx < len(siblings) - 1 or has_edges):
        r.add("warning", "publish.terminating-successor", where,
              f'Step "{step.get("description", "")}" is a terminating step but has a successor – terminating steps must end the path.')

    if edges is not None:
        if not isinstance(edges, list):
            r.add("error", "edges.array", where, "'edges' must be an array.")
        else:
            seen = set()
            for e_i, edge in enumerate(edges):
                ew = f"{where}.edges[{e_i}]"
                if not isinstance(edge, dict):
                    r.add("error", "edge.object", ew, "Edge must be an object.")
                    continue
                if not isinstance(edge.get("value"), str):
                    r.add("error", "edge.value", ew, "Edge 'value' must be a string (matched exactly at runtime).")
                elif edge["value"] in seen:
                    r.add("lint", "edge.value-unique", ew, f"Duplicate edge value '{edge['value']}' – only the first one is ever taken.")
                else:
                    seen.add(edge["value"])
                if not isinstance(edge.get("steps"), list):
                    r.add("error", "edge.steps", ew, "Edge 'steps' must be an array ([] when empty).")
                if not isinstance(edge.get("id"), str):
                    r.add("error", "edge.id", ew, "Edge needs a string 'id'.")

    if spec is None:
        if specs["action"]:
            r.add("error", "action.unknown", where,
                  f"Unknown action ordinal {a}: \"Step '<id>' has no valid action in the flow definition.\" at runtime. See docs/actions/README.md.")
        return

    check_availability(spec, where, r, features)
    if isinstance(spec.get("terminating"), bool) and isinstance(term, bool) and term != spec["terminating"]:
        r.add("error" if spec["terminating"] else "lint", "action.terminating", where,
              f"'terminating' must be {str(spec['terminating']).lower()} for {spec.get('caption', spec.get('name'))}.")
    if spec.get("group") and not has_edges:
        r.add("error", "action.edges-required", where, f"{spec.get('caption')} is a group step and needs 'edges'.")
    if not spec.get("group") and has_edges:
        r.add("lint", "action.edges-unexpected", where, f"{spec.get('caption')} is not a group step; its 'edges' are never executed.")
    fixed = ((spec.get("edges") or {}).get("fixed") or []) if spec.get("group") else []
    if has_edges and fixed:
        values = {e.get("value") for e in edges if isinstance(e, dict)}
        for fe in fixed:
            if fe.get("value") not in values:
                r.add("lint", "action.edge-missing", where,
                      f"Expected an edge with value '{fe.get('value')}' ({fe.get('description', '')}).")
    check_config_rules(spec, step.get("configuration"), where, r, flow_trigger)


def check_availability(spec, where, r, features=()):
    av = spec.get("availability", "ga")
    caption = spec.get("caption", spec.get("name"))
    feature = spec.get("feature")
    if av == "dark-launched" and feature:
        if feature not in features:
            r.add("warning", "step.dark-launched", where,
                  f"{caption} is early access: it needs the AutoFlow feature '{feature}' enabled for the environment, "
                  f"otherwise it is hidden in the editor and publish refuses it. Use it only when the user confirmed "
                  f"'{feature}' is enabled, then validate with --features {feature}.")
    elif av not in ("ga", None):
        r.add("warning", "step.availability", where, f"{caption} availability is '{av}'.")


def check_config_rules(spec, config, where, r, flow_trigger=None):
    if not isinstance(config, dict):
        return
    seen_rules = set()
    for rule in spec.get("rules") or []:
        m = rule.get("machine")
        if not m:
            continue
        sev = rule.get("severity", "error")
        if sev == "info":
            continue
        rid = rule.get("id") or f"{spec.get('name')}.rule"
        msg = rule.get("message") or ""
        if not msg or msg.startswith("("):  # specs use "(no message …)" for silent checks
            msg = rule.get("check") or rid
        if m.get("type") == "triggerNotIn":
            if flow_trigger in (m.get("triggers") or []):
                r.add(sev, rid, where, f"[{rule.get('stage', '')}] {msg}")
            continue
        key = m.get("key")
        ok = run_machine(m, config)
        if ok is False and (rid, key) not in seen_rules:
            seen_rules.add((rid, key))
            stage = rule.get("stage", "")
            r.add(sev, rid, f"{where}.configuration" + (f".{key}" if key else ""), f"[{stage}] {msg}")
    # declared configuration keys: type / enum
    for c in spec.get("configuration") or []:
        k = c.get("key")
        if not k or "*" in k:
            continue
        present, val = get_path(config, k)
        if not present or val is None or val == "":
            continue
        t = c.get("type")
        if t in ("string", "integer", "decimal", "number", "boolean", "object", "array") and not type_ok(val, t):
            # integers stored as strings etc. are a real-world source of breakage
            r.add("lint", f"{spec.get('name')}.type", f"{where}.configuration.{k}", f"'{k}' should be of type {t}.")
        enum = c.get("enum")
        if isinstance(enum, list) and enum and not isinstance(val, (dict, list)) and val not in enum:
            # allow string/int equivalence ("1" vs 1)
            if str(val) not in {str(e) for e in enum}:
                r.add("lint", f"{spec.get('name')}.enum", f"{where}.configuration.{k}", f"'{k}' should be one of {enum}.")


def run_machine(m, config):
    """Return True (passes), False (fails) or None (not applicable / unknown check)."""
    t = m.get("type")
    key = m.get("key")
    present, val = get_path(config, key) if key else (False, None)
    if t == "required":
        return present and not is_empty(val)
    if t == "requiredIf":
        p2, v2 = get_path(config, m.get("ifKey", ""))
        if p2 and v2 == m.get("equals"):
            return present and not is_empty(val)
        return None
    if t == "requiredUnless":
        p2, v2 = get_path(config, m.get("ifKey", ""))
        if p2 and v2 == m.get("equals"):
            return None
        return present and not is_empty(val)
    if not present or val is None or val == "":
        return None
    if t == "type":
        return type_ok(val, m.get("valueType"))
    if t == "enum":
        vals = m.get("values") or []
        return val in vals or str(val) in {str(v) for v in vals}
    if t == "range":
        if not isinstance(val, (int, float)) or isinstance(val, bool):
            try:
                val = float(val)
            except (TypeError, ValueError):
                return None  # placeholders like {{x_y}} are resolved at runtime
        if m.get("min") is not None and val < m["min"]:
            return False
        if m.get("max") is not None and val > m["max"]:
            return False
        return True
    if t == "maxLength":
        return not isinstance(val, str) or len(val) <= m.get("max", 10 ** 9)
    if t == "regex":
        return not isinstance(val, str) or re.fullmatch(m.get("pattern", ".*"), val) is not None
    return None


# --------------------------------------------------------------------------- main

def validate(doc, specs, strict_outputs=True, features=()):
    r = Report()
    if check_root(doc, r):
        check_steps(doc, specs, r, strict_outputs, features)
    return r


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--strict", action="store_true", help="treat warnings as failures")
    ap.add_argument("--no-lint", action="store_true", help="hide lint findings")
    ap.add_argument("--features", default="",
                    help="comma-separated dark-launched features enabled for the environment (e.g. tasks)")
    args = ap.parse_args(argv)

    specs = load_specs()
    results = {}
    exit_code = 0
    for f in args.files:
        try:
            doc = json.loads(f.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as e:
            results[str(f)] = [{"severity": "error", "rule": "json.parse", "where": "$", "message": str(e)}]
            exit_code = max(exit_code, 2)
            continue
        rep = validate(doc, specs, features={f.strip() for f in args.features.split(",") if f.strip()})
        items = [i for i in rep.items if not (args.no_lint and i["severity"] == "lint")]
        results[str(f)] = items
        if rep.count("error") or (args.strict and rep.count("warning")):
            exit_code = max(exit_code, 1)

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        for f, items in results.items():
            errs = sum(1 for i in items if i["severity"] == "error")
            warns = sum(1 for i in items if i["severity"] == "warning")
            lints = sum(1 for i in items if i["severity"] == "lint")
            print(f"{f}: {errs} error(s), {warns} warning(s), {lints} lint")
            for i in items:
                print(f"  {i['severity'].upper():7} {i['rule']}  {i['where']}\n          {i['message']}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
