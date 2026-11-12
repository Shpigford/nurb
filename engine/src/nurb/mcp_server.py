"""The tool contract, served.

`tools.json` is the contract; this module is its only implementation. Everything here
is synchronous and takes a connection, so the same dispatcher answers a stdio session
and an HTTP mount without knowing which it is.
"""

import ast
import base64
import io
import json
import math
import pathlib
import random
import re
import threading
import time
import tomllib

import anyio
import jsonschema
import mcp_types as types
from jsonschema import exceptions as schema_exceptions
from mcp.server import Server
from mcp.shared.exceptions import MCPError
from mcp_types import INVALID_PARAMS

from . import __version__, db, engine_run, labels, raster, spec as spec_module

TOOLS_FILE = pathlib.Path(__file__).with_name("tools.json")

# A project born without a name gets a quirky one from the shop floor instead of
# "Untitled", and wears it until someone renames it.
ADJECTIVES = """Brave Quirky Sleepy Plucky Dapper Wobbly Cheeky Jolly Nimble Snug Feisty
Bashful Zesty Sturdy Peppy Curious Gentle Rowdy Tidy Hasty Lofty Chunky Breezy Mellow
Jaunty Sassy Humble Giddy Cozy Bold""".split()
TERMS = [
    "Raft", "Skirt", "Brim", "Purge Line", "Benchy", "Nozzle", "Hotend", "Spool",
    "Filament", "Infill", "Overhang", "Bridge", "Seam", "Perimeter", "Chamfer",
    "Fillet", "Gantry", "Extruder", "Z-Hop", "Retraction", "First Layer", "Support",
    "Elephant Foot", "Stringing", "Blob", "Ooze", "Toolhead", "Slicer",
    "Calibration Cube", "Top Layer", "Wipe Tower", "Heatbed",
]

# Head and tail both matter in a build result: the first failure is at one end and the
# totals are at the other, and the marker says how to get at the middle.
RESULT_MAX_CHARS = 30000
HEAD_CHARS = 20000
TAIL_CHARS = 10000

# 1,000 under a connector's 150,000 so a result at the cap still fits inside the
# JSON-RPC envelope.
MCP_MAX_CHARS = 149000
# CONTRACT 2's ceiling: get_project carries every part's source at once.
PROJECT_MAX_CHARS = MCP_MAX_CHARS
SOURCE_PAGE_CHARS = 100000

# Leave room after CAD work for SQLite writes and result shaping.
# The engine gets the time actually left after materialization, not a fresh 240 seconds.
TOOL_TIMEOUT_SECONDS = 240
TOOL_SAFETY_SECONDS = 15
BUILD_TOOLS = {"write_part_source", "edit_part_source", "write_shared_source", "edit_shared_source", "run_build"}

DEFAULT_FINDINGS = 5
MAX_FINDINGS = 20

# Tools the contract names and a later phase implements. Empty: every tool the
# contract declares is implemented here.
LATER = {}


class Refused(Exception):
    """What the model is told when a tool cannot do what was asked."""


def load_tools():
    return [
        types.Tool.model_validate(entry)
        for entry in json.loads(TOOLS_FILE.read_text(encoding="utf-8"))
    ]


TOOLS = load_tools()
BY_NAME = {tool.name: tool for tool in TOOLS}


def _text(payload):
    # allow_nan=False: Infinity and NaN are not JSON, and a client that parses
    # strictly would see the whole result as malformed rather than one bad number.
    return json.dumps(payload, indent=1, allow_nan=False)


def _envelope_size(text, extra=(), is_error=False):
    result = types.CallToolResult(
        content=[types.TextContent(type="text", text=text), *extra], is_error=is_error
    )
    return len(result.model_dump_json(by_alias=True, exclude_none=True))


def _bounded_json(payload, recovery, cap):
    """A successful result is always JSON, including its overflow response."""
    text = _text(payload)
    if len(text) <= cap:
        return text
    overflow = _text(
        {
            "truncated": True,
            "original_characters": len(text),
            "recovery": recovery,
        }
    )
    if len(overflow) <= cap:
        return overflow
    return "{}"


def _result(text, links, is_error, recovery, text_cap, image=None, payload=None):
    """Bound the serialized result: base64 image data is characters on the wire too.

    The text gives way first, then the links, and the picture last, because a picture
    the model cannot get back any other way is worth more than the words about it.
    """
    text_cap = min(text_cap, MCP_MAX_CHARS)
    while True:
        bounded = (
            _bounded_json(payload, recovery, text_cap)
            if payload is not None
            else _truncate(text, recovery, text_cap)
        )
        extra = ([image] if image is not None else []) + list(links)
        overflow = _envelope_size(bounded, extra, is_error) - MCP_MAX_CHARS
        if overflow <= 0:
            return types.CallToolResult(
                content=[types.TextContent(type="text", text=bounded), *extra],
                is_error=is_error,
            )
        text_cap = max(min(text_cap, len(bounded)) - max(overflow, 1), 0)
        if text_cap == 0:
            if links:
                links = ()
            elif image is not None:
                image = None


def _ok(payload, links=(), recovery=None, cap=None, image=None):
    text = _text(payload)
    if cap is None:
        cap = RESULT_MAX_CHARS if recovery is not None else MCP_MAX_CHARS
    return _result(
        text,
        links,
        False,
        recovery or "the result exceeded the MCP limit; narrow the request",
        cap,
        image=image,
        payload=payload,
    )


def _text_of(result):
    """The words of a result, for a transcript row that has to keep them."""
    return next((block.text for block in result.content if getattr(block, "text", None)), "")


def _error(message):
    return _result(
        str(message),
        (),
        True,
        "the error exceeded the MCP limit; correct the request and retry",
        MCP_MAX_CHARS,
    )


def _truncate(text, recovery, cap=RESULT_MAX_CHARS):
    """Head and tail, keeping the marker's own length inside the cap."""
    if len(text) <= cap:
        return text
    # len(text) is an upper bound on the dropped count, so room reserved against it is
    # never less than the marker finally written needs.
    placeholder = f"\n... [{len(text)} characters truncated; {recovery}] ...\n"
    if len(placeholder) >= cap:
        return placeholder[:cap]
    room = cap - len(placeholder)
    head = text[: room * HEAD_CHARS // (HEAD_CHARS + TAIL_CHARS)]
    tail = text[len(text) - (room - len(head)) :] if room > len(head) else ""
    dropped = len(text) - len(head) - len(tail)
    marker = f"\n... [{dropped} characters truncated; {recovery}] ...\n"
    # The dropped count can have fewer digits than len(text), so the final marker can
    # leave a little spare room. It can never make the result exceed the cap.
    return f"{head}{marker}{tail}"


def _bound_error(payload, recovery, cap=RESULT_MAX_CHARS):
    """Keep a JSON result useful when one stored build error is enormous."""
    error = payload.get("error")
    if not isinstance(error, str) or len(_text(payload)) <= cap:
        return payload

    bounded = dict(payload)
    low, high = 0, min(len(error), cap)
    while low < high:
        candidate = (low + high + 1) // 2
        bounded["error"] = _truncate(error, recovery, candidate)
        if len(_text(bounded)) <= cap:
            low = candidate
        else:
            high = candidate - 1
    bounded["error"] = _truncate(error, recovery, low)
    return bounded


def _schema_error(tool, arguments):
    """The first argument problem, named by the field it is in."""
    validator = jsonschema.Draft202012Validator(tool.input_schema)
    error = schema_exceptions.best_match(validator.iter_errors(arguments))
    if error is None:
        return None
    where = "".join(
        f"[{step}]" if isinstance(step, int) else f".{step}" for step in error.absolute_path
    ).lstrip(".")
    if error.validator == "maxLength":
        message = f"is longer than the maximum {error.validator_value} characters"
        return f"{where}: {message}" if where else message
    return f"{where}: {error.message}" if where else error.message


def _project(conn, project_id):
    row = db.get_project(conn, project_id)
    if row is None:
        raise Refused(f"no project {project_id}; call list_projects")
    return row


# A part the person has started describing and nothing has written yet.
DRAFT_NOTE = (
    "This part has no source yet: the person has only described it. Write it with "
    "write_part_source under a name that says what it is, and this part takes that name."
)


def _part(conn, project_id, name):
    """The project's part by name, or None. Modules are not parts to a tool."""
    for row in db.parts_of(conn, project_id):
        if row["name"] == name and row["kind"] == "part":
            return row
    return None


def _record(conn, project_id, tool, note, summary, extra=None):
    """One line in the transcript. `extra` is what the page needs to draw the card and
    the model never sees, so it stays out of the tool result."""
    payload = {"tool": tool, "summary": summary, **(extra or {})}
    # Tagged with the part it acted on, so that part's conversation shows the step in
    # the order it happened rather than never.
    db.add_message(conn, project_id, "assistant", note, payload, part=payload.get("part_name"))


RENDER_URI = re.compile(r"^nurb://render/([0-9a-f]{32})/([a-z][a-z0-9_]*)/(iso|back|top|under)$")

RENDER_TEMPLATE = types.ResourceTemplate(
    uri_template="nurb://render/{project_id}/{part}/{view}",
    name="part render",
    mime_type="image/png",
)


def _image(png):
    return types.ImageContent(
        type="image", data=base64.b64encode(png).decode("ascii"), mime_type="image/png"
    )


def _render_link(project_id, name):
    return types.ResourceLink(
        type="resource_link",
        name=f"{name}.iso.png",
        uri=f"nurb://render/{project_id}/{name}/iso",
        mime_type="image/png",
        description="full-size iso render; the other views are back, top and under",
    )


def _build(conn, project_id, part_row, base_url, deadline):
    """Build one part and shape the run into what the model reads back."""
    run_id, result = engine_run.run_build(conn, part_row["id"], deadline=deadline)
    findings = [{k: v for k, v in f.items() if k != "face"} for f in result["findings"]]
    status = "ok" if result["glb_bytes"] is not None else "error"
    payload = {
        "status": status,
        "passed": status == "ok" and not any(f["severity"] == "fail" for f in findings),
        "error": result.get("traceback") or result["error"],
        "findings": findings,
        "stats": result["stats"],
        "inspect": "\n".join(result["inspect"]) if result["inspect"] else None,
        "total_findings": len(findings),
    }
    links, image = [], None
    if result["glb_bytes"] is not None:
        payload.update(_labels_of(conn, part_row["id"], {"id": run_id, "glb": result["glb_bytes"]}))
        payload["views"] = raster.CAPTIONS
        payload["look_note"] = raster.LOOK_NOTE
        links.append(_render_link(project_id, part_row["name"]))
        if result.get("render") is not None:
            image = _image(result["render"])
    return (
        run_id,
        {k: v for k, v in payload.items() if v is not None},
        links,
        image,
        bool(result.get("timed_out")),
    )


LABELS_NOTE = (
    "Labels are the person's names for spots on this part. Use those names when you talk "
    "about those places, and read a label's point and facing to find the place in the source."
)
OFF_NOTE = (
    "The part moved away from these labels, so they no longer mark what they named: {names}. "
    "If the place still exists, move the label onto it with set_label; if the edit removed "
    "it, tell the person."
)


def _labels_of(conn, part_id, run):
    """What a result says about the part's labels: nothing when it has none."""
    rows = db.labels_of(conn, part_id)
    if not rows:
        return {}
    placed = labels.placed(rows, run)
    out = {"labels": placed, "labels_note": LABELS_NOTE}
    off = [entry["name"] for entry in placed if entry.get("on_part") is False]
    if off:
        out["labels_off_note"] = OFF_NOTE.format(names=", ".join(off))
    return out


def place_label(conn, part_id, name, point):
    """Snap a point onto the part's newest geometry and keep it under `name`."""
    run = db.latest_ok_run(conn, part_id)
    if run is None:
        raise ValueError("the part has not built yet, so there is no surface to label")
    at, normal = labels.snap(run, point)
    db.set_label(conn, part_id, name, at, normal)
    return at, normal


def set_label(conn, args, base_url):
    project = _project(conn, args["project_id"])
    row = _part(conn, project["id"], args["part_name"])
    if row is None:
        raise Refused(f"no part called {args['part_name']} in this project")
    try:
        at, normal = place_label(conn, row["id"], args["name"], args["point"])
    except ValueError as exc:
        raise Refused(str(exc)) from None
    moved = math.dist(at, args["point"])
    _record(
        conn,
        project["id"],
        "set_label",
        args.get("note"),
        f"labelled {args['name'].strip()} on {row['name']}",
        {"part_name": row["name"]},
    )
    return _ok(
        {
            "name": args["name"].strip(),
            "point": at,
            "facing": labels.facing(normal),
            # The point lands on the nearest surface; a large move means the spot asked
            # for was not on the part, and the label may be somewhere else than meant.
            "moved_to_surface_mm": round(moved, 2),
        }
    )


def delete_label(conn, args, base_url):
    project = _project(conn, args["project_id"])
    row = _part(conn, project["id"], args["part_name"])
    if row is None:
        raise Refused(f"no part called {args['part_name']} in this project")
    try:
        db.delete_label(conn, row["id"], args["name"])
    except ValueError as exc:
        raise Refused(str(exc)) from None
    _record(
        conn,
        project["id"],
        "delete_label",
        args.get("note"),
        f"removed the label {args['name']} from {row['name']}",
        {"part_name": row["name"]},
    )
    return _ok({"deleted": args["name"]})


def _build_result(conn, project_id, part_row, base_url, tool, note, deadline, extra=None):
    run_id, payload, links, image, timed_out = _build(
        conn, project_id, part_row, base_url, deadline
    )
    summary = f"{part_row['name']} built: {payload['status']}, {payload['total_findings']} findings"
    _record(
        conn, project_id, tool, note, summary, {"run_id": run_id, "part_name": part_row["name"]}
    )
    if timed_out:
        return _error(payload["error"])
    repeats = part_repeats(conn, project_id, part_row["name"])
    if repeats:
        payload["repeats"] = repeats
        payload["repeats_note"] = (
            "This part says the same thing as a sibling. If they would both have to change "
            "together, lift it into a shared file with write_shared_source, give its numbers "
            "plain-word comments so they become settings, and import it from both parts. "
            "If they only happen to match, leave them."
        )
    body = _bound_error(
        {**(extra or {}), **payload},
        "use read_findings for the stored build error",
    )
    return _ok(body, links, "use read_findings for the full result", image=image)


def part_repeats(conn, project_id, name):
    """What this part repeats from its siblings, in the words a build result uses."""
    from . import shared

    sources = {
        row["name"]: row["source"]
        for row in db.parts_of(conn, project_id)
        if row["kind"] == "part" and row["source"] is not None
    }
    if len(sources) < 2 or name not in sources:
        return []
    found = []
    for run in shared.repeats(sources, limit=50):
        if name not in run["parts"]:
            continue
        lines = [f"{start}-{end}" for part, start, end in run["sites"] if part == name]
        found.append(
            {
                "with": [other for other in run["parts"] if other != name],
                "statements": run["statements"],
                "lines_here": lines,
                "source": run["source"],
            }
        )
    return found[:3]


def list_projects(conn, args, base_url):
    rows = conn.execute(
        "SELECT p.id, p.name, p.created_at, p.folder,"
        " (SELECT COUNT(*) FROM parts WHERE project_id = p.id AND kind = 'part') AS parts,"
        " (SELECT MAX(b.started_at) FROM build_runs b"
        "  JOIN part_revisions r ON r.id = b.revision_id"
        "  JOIN parts pa ON pa.id = r.part_id WHERE pa.project_id = p.id) AS last_built_at"
        " FROM projects p ORDER BY p.created_at"
    ).fetchall()
    return _ok({"projects": [{**dict(row), "folder": bool(row["folder"])} for row in rows]})


def _printer_profile(printer_toml):
    if not printer_toml:
        return None
    try:
        return tomllib.loads(printer_toml).get("profile")
    except tomllib.TOMLDecodeError:
        return None


def _last_build(conn, part_row):
    """The build of the source this part is holding right now, or None."""
    run = db.latest_run(conn, part_row["id"], part_row["current_revision_id"])
    if run is None:
        return None
    findings = json.loads(run["findings"])
    fails = [f for f in findings if f.get("severity") == "fail"]
    return {
        "status": run["status"],
        "passed": run["status"] == "ok" and not fails,
        "started_at": run["started_at"],
        "findings": len(findings),
        "fails": len(fails),
    }


def _system_summary(conn, project_id, rows):
    """The project's shared files as a model should meet them: what each offers, who
    uses it, and the instruction to build on it. None when the project shares nothing."""
    from . import shared

    files = [row for row in rows if row["kind"] == "module"]
    if not files:
        return None
    return {
        "note": "This project is a system. Build new parts on its shared files: import their "
        "pieces and settings instead of re-deriving the geometry, and change a shared file "
        "with edit_shared_source when the whole family should move.",
        "shared_files": [
            {
                "name": row["name"],
                "settings": [setting["name"] for setting in shared.settings(row["source"])],
                "pieces": shared.pieces(row["source"]),
                "used_by": len(importers(conn, project_id, row["id"])),
            }
            for row in files
        ],
    }


def get_project(conn, args, base_url):
    project = _project(conn, args["project_id"])
    if ("source_offset" in args or "source_limit" in args) and "part_name" not in args:
        raise Refused("source_offset and source_limit require part_name")
    rows = list(db.parts_of(conn, project["id"]))
    part_name = args.get("part_name")
    pinned = spec_module.current(conn, project["id"], part_name)
    if part_name is not None:
        rows = [row for row in rows if row["name"] == part_name]
        if not rows:
            raise Refused(f"no part or module called {part_name} in this project")

    parts = [
        {
            "name": row["name"],
            # What the person calls it, when they named it; say this one to them.
            "title": row["title"],
            "kind": row["kind"],
            "source": row["source"],
            "last_build": _last_build(conn, row),
            **(_labels_of(conn, row["id"], db.latest_ok_run(conn, row["id"])) if row["kind"] == "part" else {}),
            **(
                {"note": DRAFT_NOTE}
                if row["kind"] == "part" and row["source"] is None
                else {}
            ),
        }
        for row in rows
    ]
    payload = {
        "id": project["id"],
        "name": project["name"],
        # First, so a new part starts from the family's system instead of rediscovering it.
        "system": _system_summary(conn, project["id"], rows),
        "printer": _printer_profile(project["printer_toml"]),
        "spec": pinned,
        "measurements": [_measurement(row) for row in db.measurements_of(conn, project["id"])],
        "parts": parts,
    }
    if part_name is not None:
        offset = int(args.get("source_offset") or 0)
        limit = int(args.get("source_limit") or SOURCE_PAGE_CHARS)
        sources = [part["source"] or "" for part in parts]
        for part, source in zip(parts, sources):
            part["source_offset"] = offset
            part["source_length"] = len(source)
        end = min(offset + limit, max(map(len, sources)))
        # A Python character can occupy twelve JSON characters as a surrogate pair.
        # Fit every same-named module's page by its actual serialized size, not an
        # ASCII guess. Root and parts/ modules may deliberately share a basename.
        low, high = offset, end
        while low < high:
            midpoint = (low + high + 1) // 2
            for part, source in zip(parts, sources):
                part["source"] = source[offset:midpoint]
                if midpoint < len(source):
                    part["next_source_offset"] = midpoint
                else:
                    part.pop("next_source_offset", None)
            if _envelope_size(_text(payload)) <= PROJECT_MAX_CHARS:
                low = midpoint
            else:
                high = midpoint - 1
        for part, source in zip(parts, sources):
            part["source"] = source[offset:low]
            if low < len(source):
                part["next_source_offset"] = low
            else:
                part.pop("next_source_offset", None)
    elif _envelope_size(_text(payload)) > PROJECT_MAX_CHARS:
        for part in parts:
            part.pop("source")
        payload["sources_omitted"] = True
        payload["note"] = "sources omitted to fit the result; call get_project with part_name to read one source"

    return _ok(
        payload,
        recovery="call get_project with part_name, source_offset, and source_limit",
        cap=PROJECT_MAX_CHARS,
    )


def _placeholder_name(conn):
    taken = {row["name"] for row in conn.execute("SELECT name FROM projects")}
    for _ in range(10):
        candidate = f"{random.choice(ADJECTIVES)} {random.choice(TERMS)}"
        if candidate not in taken:
            return candidate
    return f"{random.choice(ADJECTIVES)} {random.choice(TERMS)} {len(taken) + 1}"


def create_project(conn, args, base_url):
    name = (args.get("name") or "").strip() or _placeholder_name(conn)
    if len(name) > db.NAME_LIMIT:
        raise Refused(f"name can be at most {db.NAME_LIMIT} characters")
    project_id = db.create_project(conn, name)
    _record(conn, project_id, "create_project", args.get("note"), f"created project {name}")
    return _ok({"id": project_id, "name": name})


def _measurement(row):
    payload = {
        "name": row["name"],
        "how": row["how"],
        "provisional": bool(row["provisional"]),
    }
    if row["unit"] == "mm":
        payload["value_mm"] = float(row["value"])
    else:
        payload.update(
            {
                "value": float(row["value"]),
                "unit": row["unit"],
                "conversion": "Convert this value to millimetres, then call record_measurement with this exact name and value_mm to replace the stored unit.",
            }
        )
    return payload


def _uses(source):
    return db.measurement_names(source)


def _module_imports(source, module_names, current_module=None):
    """Project modules imported by one source, without executing user code."""
    try:
        tree = ast.parse(source or "")
    except SyntaxError:
        return []
    imported = []

    def add(name):
        dependency = module_names.get(name)
        if dependency is not None:
            imported.append(dependency)

    def from_name(node):
        if not node.level:
            return node.module
        if current_module is None:
            return None
        package = current_module.split(".")[:-1]
        if node.level > len(package):
            return None
        base = package[: len(package) - node.level + 1]
        if node.module:
            base.extend(node.module.split("."))
        return ".".join(base)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = from_name(node)
            if not module:
                continue
            add(module)
            for alias in node.names:
                add(f"{module}.{alias.name}")
    return list(dict.fromkeys(imported))


def _measurement_uses(rows, project_files=()):
    """Direct and transitive measurement reads for every project part."""
    modules = {}
    sources = {row["id"]: row["source"] for row in rows}
    current_modules = {}
    for row in rows:
        if row["kind"] == "module":
            modules[row["name"]] = row["id"]
        elif row["kind"] == db.PARTS_MODULE_KIND:
            modules[f"parts.{row['name']}"] = row["id"]
            current_modules[row["id"]] = f"parts.{row['name']}"
    for file in project_files:
        path = pathlib.PurePosixPath(file["path"])
        if path.suffix != ".py" or not all(
            part.isidentifier() for part in path.with_suffix("").parts
        ):
            continue
        pieces = list(path.with_suffix("").parts)
        imported_as = ".".join(pieces[:-1] if pieces[-1] == "__init__" else pieces)
        if not imported_as:
            continue
        key = f"project_file:{file['path']}"
        modules[imported_as] = key
        sources[key] = file["content"]
        current_modules[key] = ".".join(pieces)
    direct = {key: _uses(source) for key, source in sources.items()}
    imports = {
        key: _module_imports(source, modules, current_modules.get(key))
        for key, source in sources.items()
    }

    def walk(name, seen):
        if name in seen:
            return []
        found = list(direct[name])
        for dependency in imports[name]:
            found.extend(walk(dependency, {*seen, name}))
        return list(dict.fromkeys(found))

    return {row["id"]: walk(row["id"], set()) for row in rows}


def read_measurements(conn, args, base_url):
    project = _project(conn, args["project_id"])
    rows = list(db.parts_of(conn, project["id"]))
    uses = _measurement_uses(rows, db.project_files_of(conn, project["id"]))
    return _ok(
        {
            "measurements": [_measurement(row) for row in db.measurements_of(conn, project["id"])],
            "parts": [
                {"name": row["name"], "uses": uses[row["id"]]}
                for row in rows
                if row["kind"] == "part"
            ],
        }
    )


def _normalize(name):
    # Case is kept: a part reads a measurement by the exact name, so lowercasing an
    # imported `Rail_Width` here would break the `measured("Rail_Width")` that reads it.
    out = re.sub(r"[^A-Za-z0-9_-]+", "_", str(name).strip())
    return out.strip("_")


def _stale_parts(conn, project_id, name, changed_at):
    """Parts that read this measurement and were last built before it changed."""
    stale = []
    rows = list(db.parts_of(conn, project_id))
    uses = _measurement_uses(rows, db.project_files_of(conn, project_id))
    for row in rows:
        if row["kind"] != "part" or name not in uses[row["id"]]:
            continue
        run = db.latest_run(conn, row["id"])
        if run is not None and run["started_at"] < changed_at:
            stale.append(row["name"])
    return stale


def _measurement_stale(conn, project_id, part_row, built_at):
    """Whether a measurement this part reads changed after its build."""
    rows = list(db.parts_of(conn, project_id))
    uses = _measurement_uses(rows, db.project_files_of(conn, project_id))[part_row["id"]]
    changed = {
        measurement["name"]: measurement["value_changed_at"]
        for measurement in db.measurements_of(conn, project_id)
    }
    return any(changed.get(name, "") > built_at for name in uses)


def record_measurement(conn, args, base_url):
    project = _project(conn, args["project_id"])
    requested_name = str(args["name"]).strip()
    before = conn.execute(
        "SELECT name, value, unit FROM measurements WHERE project_id = ? AND name = ?",
        (project["id"], requested_name),
    ).fetchone()
    name = requested_name if before is not None else _normalize(requested_name)
    if not name:
        raise Refused("name is required")
    value = float(args["value_mm"])
    if not math.isfinite(value):
        raise Refused("value_mm must be a finite number")
    how = args["how"].strip()
    if not how:
        raise Refused("how is required: say where the number came from")

    if before is None and name != requested_name:
        before = conn.execute(
            "SELECT name, value, unit FROM measurements WHERE project_id = ? AND name = ?",
            (project["id"], name),
        ).fetchone()
    db.set_measurement(
        conn,
        project["id"],
        name,
        value,
        how,
        provisional=args["provisional"],
    )
    if before is not None and before["unit"] != "mm":
        # Changing units changes the physical interpretation even when the two raw
        # numbers happen to match, so it must date staleness as a value change.
        with db.transaction(conn):
            conn.execute(
                "UPDATE measurements SET value_changed_at = ? WHERE project_id = ? AND name = ?",
                (db.now(), project["id"], name),
            )
    row = conn.execute(
        "SELECT * FROM measurements WHERE project_id = ? AND name = ?", (project["id"], name)
    ).fetchone()

    changed = (
        before is None
        or before["value"] != row["value"]
        or before["unit"] != row["unit"]
    )
    payload = {"measurement": _measurement(row)}
    if before is not None:
        if before["unit"] == "mm":
            payload["previous_value_mm"] = float(before["value"])
        else:
            payload["previous_measurement"] = {
                "value": float(before["value"]),
                "unit": before["unit"],
            }
    payload["stale_parts"] = (
        _stale_parts(conn, project["id"], name, row["value_changed_at"]) if changed else []
    )
    _record(
        conn,
        project["id"],
        "record_measurement",
        args.get("note"),
        f"recorded {name} = {float(row['value'])} mm",
        {
            "measurement": name,
            "previous_value_mm": payload.get("previous_value_mm"),
            "stale_parts": payload["stale_parts"],
        },
    )
    return _ok(payload)


def write_part_source(conn, args, base_url, deadline=None):
    if deadline is None:
        deadline = time.monotonic() + TOOL_TIMEOUT_SECONDS - TOOL_SAFETY_SECONDS
    project = _project(conn, args["project_id"])
    name, source = args["part_name"], args["source"]
    row = _part(conn, project["id"], name)
    if row is not None and row["source"] is None and db.DRAFT_NAMES.match(name):
        raise Refused(f"{name} is a placeholder; write the part under a name that says what it is")
    if row is None:
        if any(other["name"] == name for other in db.parts_of(conn, project["id"])):
            raise Refused(f"{name} is a module in this project; pick another name")
        # The part the person started describing is already in the library, so the
        # first write names it rather than adding a second card beside it.
        draft = db.draft_of(conn, project["id"])
        if draft is not None:
            db.adopt_draft(conn, draft["id"], name, source, note=args.get("note"))
        else:
            db.create_part(conn, project["id"], name, source)
    elif row["source"] == source:
        _record(
            conn,
            project["id"],
            "write_part_source",
            args.get("note"),
            f"{name} unchanged",
            {"part_name": name},
        )
        return _ok({"changed": False, "note": "source unchanged from the current revision"})
    else:
        db.add_revision(conn, row["id"], source, card_md=row["card_md"], note=args.get("note"))
    row = _part(conn, project["id"], name)
    return _build_result(
        conn,
        project["id"],
        row,
        base_url,
        "write_part_source",
        args.get("note"),
        deadline,
        {"changed": True},
    )


def edit_part_source(conn, args, base_url, deadline=None):
    if deadline is None:
        deadline = time.monotonic() + TOOL_TIMEOUT_SECONDS - TOOL_SAFETY_SECONDS
    project = _project(conn, args["project_id"])
    name, old = args["part_name"], args["old_string"]
    row = _part(conn, project["id"], name)
    if row is None or row["source"] is None:
        raise Refused(f"no source yet for {name}; call write_part_source first")
    if not old:
        raise Refused("old_string is required")
    count = row["source"].count(old)
    if count == 0:
        raise Refused("old_string not found in the current source")
    if count > 1:
        raise Refused(f"old_string matches {count} places; include more surrounding lines")

    # A plain replace, never re.sub: backslashes and \0 are ordinary text in Python source.
    db.add_revision(
        conn,
        row["id"],
        row["source"].replace(old, args["new_string"], 1),
        card_md=row["card_md"],
        note=args.get("note"),
    )
    row = _part(conn, project["id"], name)
    return _build_result(
        conn,
        project["id"],
        row,
        base_url,
        "edit_part_source",
        args.get("note"),
        deadline,
        {"changed": True},
    )


def importers(conn, project_id, module_id):
    """The project's parts that import a shared file, directly or through another one."""
    rows = list(db.parts_of(conn, project_id))
    modules, current = {}, {}
    for row in rows:
        if row["kind"] == "module":
            modules[row["name"]] = row["id"]
        elif row["kind"] == db.PARTS_MODULE_KIND:
            modules[f"parts.{row['name']}"] = row["id"]
            current[row["id"]] = f"parts.{row['name']}"
    imports = {row["id"]: _module_imports(row["source"], modules, current.get(row["id"])) for row in rows}

    def reaches(key, seen):
        if key in seen:
            return False
        return any(dep == module_id or reaches(dep, {*seen, key}) for dep in imports.get(key, ()))

    return [row for row in rows if row["kind"] == "part" and reaches(row["id"], set())]


def _shared(conn, project_id, name):
    """The project's shared file by name, or None."""
    for row in db.parts_of(conn, project_id):
        if row["name"] == name and row["kind"] == "module":
            return row
    return None


def _save_shared(conn, project, name, source, note, tool, base_url, deadline):
    """Save a shared file, build the first part that imports it now so a break shows
    at once, and queue the rest for the background builder."""
    try:
        compile(source, f"{name}.py", "exec")
    except SyntaxError as exc:
        raise Refused(f"{name}.py does not parse: line {exc.lineno}: {exc.msg}") from None
    row = _shared(conn, project["id"], name)
    if row is None:
        if _part(conn, project["id"], name) is not None:
            raise Refused(f"{name} is a part in this project; pick another name for the shared file")
        db.create_part(conn, project["id"], name, source, kind="module")
    elif row["source"] == source:
        return _ok({"changed": False, "note": "source unchanged from the current revision"})
    else:
        db.add_revision(conn, row["id"], source, note=note)
    row = _shared(conn, project["id"], name)
    using = importers(conn, project["id"], row["id"])
    if not using:
        _record(conn, project["id"], tool, note, f"{name}.py saved; no part imports it yet", {"shared_file": name})
        return _ok({"changed": True, "importers": [], "note": f"no part imports {name} yet; import it from a part, then build that part"})
    first, rest = using[0], using[1:]
    engine_run.want_rebuild([other["id"] for other in rest], project["id"])
    extra = {
        "changed": True,
        "importers": [other["name"] for other in using],
        "note": f"built {first['name']} now; {len(rest)} more parts that import {name} are rebuilding in the background",
    }
    return _build_result(conn, project["id"], first, base_url, tool, note, deadline, extra)


def write_shared_source(conn, args, base_url, deadline=None):
    if deadline is None:
        deadline = time.monotonic() + TOOL_TIMEOUT_SECONDS - TOOL_SAFETY_SECONDS
    project = _project(conn, args["project_id"])
    return _save_shared(
        conn, project, args["name"], args["source"], args.get("note"), "write_shared_source", base_url, deadline
    )


def edit_shared_source(conn, args, base_url, deadline=None):
    if deadline is None:
        deadline = time.monotonic() + TOOL_TIMEOUT_SECONDS - TOOL_SAFETY_SECONDS
    project = _project(conn, args["project_id"])
    name, old = args["name"], args["old_string"]
    row = _shared(conn, project["id"], name)
    if row is None or row["source"] is None:
        raise Refused(f"no shared file called {name}; call write_shared_source first")
    if not old:
        raise Refused("old_string is required")
    count = row["source"].count(old)
    if count == 0:
        raise Refused("old_string not found in the current source")
    if count > 1:
        raise Refused(f"old_string matches {count} places; include more surrounding lines")
    source = row["source"].replace(old, args["new_string"], 1)
    return _save_shared(conn, project, name, source, args.get("note"), "edit_shared_source", base_url, deadline)


def run_build(conn, args, base_url, deadline=None):
    if deadline is None:
        deadline = time.monotonic() + TOOL_TIMEOUT_SECONDS - TOOL_SAFETY_SECONDS
    project = _project(conn, args["project_id"])
    row = _part(conn, project["id"], args["part_name"])
    if row is None:
        raise Refused(
            f"no part called {args['part_name']} in this project; call write_part_source first"
        )
    return _build_result(
        conn, project["id"], row, base_url, "run_build", args.get("note"), deadline
    )


def read_findings(conn, args, base_url):
    project = _project(conn, args["project_id"])
    row = _part(conn, project["id"], args["part_name"])
    if row is None:
        raise Refused(
            f"no part called {args['part_name']} in this project; call write_part_source first"
        )
    run = db.latest_run(conn, row["id"], row["current_revision_id"])
    if run is None:
        return _ok({"note": "no builds yet; call run_build first"})

    offset = max(int(args.get("offset") or 0), 0)
    limit = min(int(args.get("limit") or DEFAULT_FINDINGS), MAX_FINDINGS)
    findings = [{k: v for k, v in f.items() if k != "face"} for f in json.loads(run["findings"])]
    page = findings[offset : offset + limit]
    inspect = json.loads(run["inspect_report"])
    payload = {
        "status": run["status"],
        "error": run["error"],
        "findings": page,
        "stats": json.loads(run["stats"]),
        "inspect": "\n".join(inspect) if inspect and offset == 0 else None,
        "offset": offset,
        "total_findings": len(findings),
        "next_offset": offset + len(page) if offset + len(page) < len(findings) else None,
    }
    body = _bound_error(
        {k: v for k, v in payload.items() if v is not None},
        "middle of stored build error omitted to fit the result limit",
    )
    return _ok(body, recovery="lower limit or raise offset")


def _render_of(conn, run):
    """The run's composite, rendered and stored now if the row predates it."""
    if run["render"] is not None:
        return run["render"]
    render = raster.composite(run["glb"])
    with db.transaction(conn):
        conn.execute("UPDATE build_runs SET render = ? WHERE id = ?", (render, run["id"]))
    return render


def look(conn, args, base_url):
    project = _project(conn, args["project_id"])
    name = args["part_name"]
    row = _part(conn, project["id"], name)
    if row is None:
        raise Refused(f"no part called {name} in this project; call write_part_source first")
    run = db.latest_ok_run(conn, row["id"])
    if run is None:
        raise Refused(f"{name} has no successful build yet; call run_build first")
    payload = {
        "part_name": name,
        "built_at": run["started_at"],
        "stale": run["revision_id"] != row["current_revision_id"]
        or _measurement_stale(conn, project["id"], row, run["started_at"]),
        "views": raster.CAPTIONS,
        "look_note": raster.LOOK_NOTE,
    }
    # Read-only: looking at a part is not a step in the transcript.
    return _ok(payload, [_render_link(project["id"], name)], image=_image(_render_of(conn, run)))


def list_render_resources(conn):
    """Every view of every part that has something to show."""
    resources = []
    for project in conn.execute("SELECT id FROM projects ORDER BY created_at").fetchall():
        for row in db.parts_of(conn, project["id"]):
            if row["kind"] != "part" or db.latest_ok_run(conn, row["id"]) is None:
                continue
            for view in raster.VIEWS:
                resources.append(
                    types.Resource(
                        uri=f"nurb://render/{project['id']}/{row['name']}/{view}",
                        name=f"{row['name']}.{view}.png",
                        mime_type="image/png",
                        description=raster.CAPTIONS[view],
                    )
                )
    return resources


def read_render_resource(conn, uri):
    """One full-size view. A raise here is the protocol's own error, which is right.

    Only `MCPError` crosses the wire with its sentence; the SDK logs any other
    exception and answers a bare "Internal server error".
    """
    match = RENDER_URI.match(str(uri))
    if match is None:
        raise MCPError(INVALID_PARAMS, f"not a part render URI: {uri}")
    project_id, name, view = match.groups()
    if db.get_project(conn, project_id) is None:
        raise MCPError(INVALID_PARAMS, f"no project {project_id}")
    row = _part(conn, project_id, name)
    if row is None:
        raise MCPError(INVALID_PARAMS, f"no part called {name} in project {project_id}")
    run = db.latest_ok_run(conn, row["id"])
    if run is None:
        raise MCPError(INVALID_PARAMS, f"{name} has no successful build yet")
    png = raster.looks(run["glb"], [view])[view]
    return types.BlobResourceContents(
        uri=str(uri), mime_type="image/png", blob=base64.b64encode(png).decode("ascii")
    )


def read_guide(conn, args, base_url):
    """The guide goes back as raw markdown: it is prose to read, not a payload to parse."""
    from . import guide

    return types.CallToolResult(
        content=[types.TextContent(type="text", text=guide.text())], is_error=False
    )


def _spec_input(args):
    """The spec fields of a call: everything that is not the call's own addressing."""
    spec = {key: value for key, value in args.items() if key not in ("project_id", "note")}
    return spec_module.settle_numbers(spec)


def _reject(problems):
    return _error(
        "Spec rejected: " + "; ".join(problems[:5]) + ". Fix it and call the tool again."
    )


def _pin(conn, project_id, tool, args, spec, summary, note):
    spec_module.pin(conn, project_id, spec)
    db.add_message(
        conn,
        project_id,
        "assistant",
        args.get("note"),
        {
            "tool": tool,
            "summary": summary,
            "type": "spec_pinned",
            "spec": spec,
            "input": _spec_input(args),
        },
    )
    return _ok({"ok": True, "part_name": spec["part_name"], "spec": spec, "note": note})


def pin_spec(conn, args, base_url):
    project = _project(conn, args["project_id"])
    spec = _spec_input(args)
    problems = spec_module.errors(spec)
    if problems:
        return _reject(problems)
    part_name = spec["part_name"]
    return _pin(
        conn,
        project["id"],
        "pin_spec",
        args,
        spec,
        f"pinned spec for {part_name}",
        f"Spec pinned. Build {part_name} now: write the source; the save builds it.",
    )


def amend_spec(conn, args, base_url):
    project = _project(conn, args["project_id"])
    part_name = args["part_name"]
    base = spec_module.current(conn, project["id"], part_name)
    if base is None:
        raise Refused(f'No pinned spec for "{part_name}" to amend. pin_spec is for a new part.')
    merged = spec_module.merge(base, _spec_input(args))
    problems = spec_module.errors(merged)
    if problems:
        return _reject(problems)
    return _pin(
        conn,
        project["id"],
        "amend_spec",
        args,
        merged,
        f"amended spec for {part_name}",
        "Spec updated.",
    )


PHOTO_COUNT = 3
PHOTO_EDGE = 800
PHOTO_MIN_EDGE = 200
PHOTO_QUALITY = 80
PHOTO_NOTE = "Reference photos from this project, downscaled. Read them for shape and orientation only; a pixel is not a millimetre."


def _photo_jpeg(data, edge):
    """One attachment as a JPEG that fits inside `edge` on both sides, or None."""
    from PIL import Image, ImageOps

    try:
        with Image.open(io.BytesIO(data)) as image:
            image = ImageOps.exif_transpose(image)
            if image.mode in ("RGBA", "LA", "P"):
                image = image.convert("RGBA")
                flat = Image.new("RGB", image.size, (255, 255, 255))
                flat.paste(image, mask=image.split()[-1])
                image = flat
            else:
                image = image.convert("RGB")
            # thumbnail only shrinks, so a small photo is sent at its own size.
            image.thumbnail((edge, edge))
            buf = io.BytesIO()
            image.save(buf, "JPEG", quality=PHOTO_QUALITY, optimize=True)
            return buf.getvalue(), image.width, image.height
    except Exception:
        return None


NO_PHOTOS = (
    "there are no photos of the real thing yet. Carry on from what the person said; if a photo "
    "would settle a shape you cannot work out, ask them to attach one in the chat"
)


def _photo_rank(rows, query):
    """Name matches first, newest first within each group: the photo just attached."""
    tokens = [token for token in str(query).lower().split() if token]
    hits, rest = [], []
    for row in reversed(rows):
        stem = pathlib.PurePosixPath(row["name"]).with_suffix("").as_posix().lower()
        (hits if any(token in stem for token in tokens) else rest).append(row)
    return hits + rest


def find_photos(conn, args, base_url):
    project = _project(conn, args["project_id"])
    rows = list(db.attachments_of(conn, project["id"]))
    # Having no photos is the ordinary case, not a failure: the person describes the
    # thing in words, and a photo is something to ask for in the chat when it would help.
    if not rows:
        return _ok({"photos": [], "note": NO_PHOTOS})

    chosen = []
    for row in _photo_rank(rows, args["query"]):
        if len(chosen) >= PHOTO_COUNT:
            break
        if _photo_jpeg(row["bytes"], PHOTO_EDGE) is not None:
            chosen.append(row)
    if not chosen:
        return _ok({"photos": [], "note": "the attached photos could not be opened. " + NO_PHOTOS})

    edge = PHOTO_EDGE
    while True:
        photos, images = [], []
        for row in chosen:
            made = _photo_jpeg(row["bytes"], edge)
            if made is None:
                continue
            jpeg, width, height = made
            photos.append(
                {"name": row["name"], "width": width, "height": height, "mime": "image/jpeg"}
            )
            images.append(
                types.ImageContent(
                    type="image",
                    data=base64.b64encode(jpeg).decode("ascii"),
                    mime_type="image/jpeg",
                )
            )
        text = _text({"query": args["query"], "photos": photos, "note": PHOTO_NOTE})
        if _envelope_size(text, images) <= MCP_MAX_CHARS - 2000 or edge <= PHOTO_MIN_EDGE:
            break
        edge = max(edge // 2, PHOTO_MIN_EDGE)

    return types.CallToolResult(
        content=[types.TextContent(type="text", text=text), *images], is_error=False
    )


HANDLERS = {
    "list_projects": list_projects,
    "get_project": get_project,
    "create_project": create_project,
    "read_guide": read_guide,
    "pin_spec": pin_spec,
    "amend_spec": amend_spec,
    "find_photos": find_photos,
    "read_measurements": read_measurements,
    "record_measurement": record_measurement,
    "write_part_source": write_part_source,
    "edit_part_source": edit_part_source,
    "write_shared_source": write_shared_source,
    "edit_shared_source": edit_shared_source,
    "run_build": run_build,
    "read_findings": read_findings,
    "look": look,
    "set_label": set_label,
    "delete_label": delete_label,
}


def _sequence(conn, project_id):
    return conn.execute(
        "SELECT COALESCE(MAX(sequence_number), 0) FROM messages WHERE project_id = ?",
        (project_id,),
    ).fetchone()[0]


def dispatch(conn, name, arguments, base_url, deadline=None):
    """One tool call. Returns a result for every outcome, including its own failure."""
    tool = BY_NAME.get(name)
    if tool is None:
        return _error(f"unknown tool {name}")
    problem = _schema_error(tool, arguments)
    if problem:
        return _error(f"bad arguments for {name}: {problem}")
    if name in LATER:
        return _error(f"{name} is not available yet: Phase {LATER[name]} adds it")
    project_id = arguments.get("project_id")
    if not isinstance(project_id, str) or db.get_project(conn, project_id) is None:
        project_id = None
    before = _sequence(conn, project_id) if project_id else 0
    started = time.monotonic()
    try:
        # Saving under the old name would make a second part and leave the real one unchanged.
        renamed = project_id and db.renamed_to(conn, project_id, arguments.get("part_name"))
        if renamed:
            raise Refused(
                f"{arguments['part_name']} was just renamed to {renamed}; use {renamed} for that part. "
                "A new part needs a different name for now."
            )
        if name in BUILD_TOOLS:
            result = HANDLERS[name](conn, arguments, base_url, deadline=deadline)
        else:
            result = HANDLERS[name](conn, arguments, base_url)
    except Refused as exc:
        result = _error(str(exc))
    except Exception as exc:
        result = _error(f"{name} failed: {type(exc).__name__}: {exc}")
    # A tool that wrote its own line is already in the transcript; the rest would
    # otherwise leave the chat column with nothing to show for the call.
    if project_id and _sequence(conn, project_id) == before:
        db.add_message(
            conn,
            project_id,
            "event",
            None,
            {
                "tool": name,
                "status": "failed" if result.is_error else "done",
                "elapsed_s": round(time.monotonic() - started, 2),
                "subject": arguments.get("part_name") or arguments.get("name"),
                # A refusal is the one thing a failed step has to keep.
                "summary": _text_of(result)[:300] if result.is_error else None,
            },
        )
    return result


# What the agent reads once, at connect, before it has called anything.
INSTRUCTIONS = (
    "Call read_guide before writing any part: it carries the design rules and the "
    "vocabulary a part file gets, and a part written without it will be wrong. Every "
    "build result carries one composite picture of the part, so look at the picture "
    "before you report. The user is watching the workbench at {base_url}, so after a "
    "build name the part and say what changed rather than describing the geometry."
)


def make_server(conn, base_url, lock=None):
    """The MCP server for one database. `base_url` only addresses the GLB link."""
    guard = lock or threading.Lock()

    async def on_list_tools(ctx, params):
        return types.ListToolsResult(tools=TOOLS)

    async def on_call_tool(ctx, params):
        deadline = time.monotonic() + TOOL_TIMEOUT_SECONDS - TOOL_SAFETY_SECONDS

        def work():
            # A build takes seconds of OCCT, so it runs off the event loop, and the
            # lock keeps one connection to one thread at a time.
            remaining = max(deadline - time.monotonic(), 0.0)
            if not guard.acquire(timeout=remaining):
                return _error(
                    f"tool call exceeded the {TOOL_TIMEOUT_SECONDS:g} second deadline; retry"
                )
            try:
                return dispatch(
                    conn,
                    params.name,
                    params.arguments or {},
                    base_url,
                    deadline=deadline,
                )
            finally:
                guard.release()

        return await anyio.to_thread.run_sync(work)

    async def on_list_resources(ctx, params):
        def work():
            with guard:
                return types.ListResourcesResult(resources=list_render_resources(conn))

        return await anyio.to_thread.run_sync(work)

    async def on_list_resource_templates(ctx, params):
        def work():
            with guard:
                return types.ListResourceTemplatesResult(resource_templates=[RENDER_TEMPLATE])

        return await anyio.to_thread.run_sync(work)

    async def on_read_resource(ctx, params):
        def work():
            with guard:
                return types.ReadResourceResult(contents=[read_render_resource(conn, params.uri)])

        return await anyio.to_thread.run_sync(work)

    return Server(
        "nurb",
        version=__version__,
        instructions=INSTRUCTIONS.format(base_url=base_url),
        on_list_tools=on_list_tools,
        on_call_tool=on_call_tool,
        on_list_resources=on_list_resources,
        on_list_resource_templates=on_list_resource_templates,
        on_read_resource=on_read_resource,
    )
