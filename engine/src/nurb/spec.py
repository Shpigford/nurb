"""The pinned build spec: what it must contain, how an amendment merges into it."""

import copy
import json
import pathlib

import jsonschema

from . import db

TOOLS_FILE = pathlib.Path(__file__).with_name("tools.json")

PYTHON_KEYWORDS = frozenset(
    """False None True and as assert async await break class continue def del elif else
    except finally for from global if import in is lambda nonlocal not or pass raise
    return try while with yield""".split()
)


def _spec_schema():
    """The pin_spec schema without the fields that address the call rather than the spec."""
    for entry in json.loads(TOOLS_FILE.read_text(encoding="utf-8")):
        if entry["name"] == "pin_spec":
            schema = copy.deepcopy(entry["inputSchema"])
            for field in ("project_id", "note"):
                schema["properties"].pop(field, None)
            schema["required"] = [name for name in schema["required"] if name not in ("project_id", "note")]
            return schema
    raise RuntimeError("tools.json has no pin_spec")


SPEC_SCHEMA = _spec_schema()

KIND_CHECK = {
    "float": lambda value: isinstance(value, float),
    "int": lambda value: isinstance(value, int) and not isinstance(value, bool),
    "bool": lambda value: isinstance(value, bool),
    "str": lambda value: isinstance(value, str),
}


def _where(error):
    return "".join(
        f"[{step}]" if isinstance(step, int) else f".{step}" for step in error.absolute_path
    ).lstrip(".")


def errors(spec):
    """Everything wrong with a spec, schema first, then what the schema cannot say."""
    found = []
    validator = jsonschema.Draft202012Validator(SPEC_SCHEMA)
    for error in sorted(validator.iter_errors(spec), key=lambda e: list(e.absolute_path)):
        where = _where(error)
        found.append(f"{where}: {error.message}" if where else error.message)
    if found:
        return found

    if spec.get("part_name") in PYTHON_KEYWORDS:
        found.append("part_name is a reserved Python keyword")
    params = spec.get("params") or []
    seen = set()
    for param in params:
        name = param.get("name")
        if name in seen:
            found.append(f'parameter name "{name}" is duplicated')
        seen.add(name)
    for i, param in enumerate(params, start=1):
        name = param.get("name")
        if name in PYTHON_KEYWORDS:
            found.append(f"parameter {i} name is a reserved Python keyword")
        elif name == "draft":
            found.append(f"parameter {i} name is reserved by the nurb runtime")
        kind = param.get("kind")
        check = KIND_CHECK.get(kind)
        if check and not check(param.get("default")):
            found.append(f'parameter "{name}" default does not match kind "{kind}"')
    return found


def _replace_by_key(existing, incoming, key):
    """Incoming items replace matching ones in place; the rest land at the end."""
    merged = list(existing)
    by_key = {item.get(key): i for i, item in enumerate(merged)}
    for item in incoming:
        at = by_key.get(item.get(key))
        if at is None:
            by_key[item.get(key)] = len(merged)
            merged.append(item)
        else:
            merged[at] = item
    return merged


def merge(base, input):
    """The amended spec: named entries replaced, new ones appended, notes accumulated."""
    merged = copy.deepcopy(base)
    if input.get("summary"):
        merged["summary"] = input["summary"]
    for field, key in (("params", "name"), ("dimensions", "name"), ("acceptance", "check")):
        incoming = input.get(field) or []
        if incoming:
            merged[field] = _replace_by_key(merged.get(field) or [], copy.deepcopy(incoming), key)
    drop = set(input.get("remove_params") or [])
    if drop:
        merged["params"] = [p for p in (merged.get("params") or []) if p.get("name") not in drop]
    notes = input.get("notes") or []
    if notes:
        conventions = merged.setdefault("conventions", {})
        conventions["notes"] = list(conventions.get("notes") or []) + list(notes)
    return merged


def current(conn, project_id, part_name=None):
    """The newest pinned spec for the project, or for one part of it."""
    rows = conn.execute(
        "SELECT spec FROM pinned_specs WHERE project_id = ? ORDER BY created_at DESC, rowid DESC",
        (project_id,),
    ).fetchall()
    for row in rows:
        spec = json.loads(row["spec"])
        if part_name is None or spec.get("part_name") == part_name:
            return spec
    return None


def pin(conn, project_id, spec):
    spec_id = db.new_id()
    with db.transaction(conn):
        conn.execute(
            "INSERT INTO pinned_specs (id, project_id, spec, created_at) VALUES (?, ?, ?, ?)",
            (spec_id, project_id, json.dumps(spec), db.now()),
        )
    db.changed("project", spec_id, project_id)
    return spec_id
