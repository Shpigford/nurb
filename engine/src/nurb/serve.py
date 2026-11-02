"""The one process that owns the database, behind one port.

Everything else talks to it: an agent's tools arrive at `/mcp`, and a viewer fetches geometry from `/glb`. A file lock makes "one process" true rather than hoped for, and `serve.json` is how the others find the port and the token.

Every route rejects non-loopback Host headers so DNS rebinding cannot expose local state. The MCP endpoint also requires a bearer token to keep a page in the user's own browser from driving their tools.
"""

import asyncio
import base64
import contextlib
import datetime
import json
import math
import os
import pathlib
import secrets
import signal
import sqlite3
import sys
import tempfile
import threading
import time
import urllib.parse

from . import db, edit, engine_run, materialize, mcp_server, spec

STATE = "serve.json"
LOCK = "serve.lock"
CONNECT = "connect.json"

# Where the serve listens unless something else already holds the port.
DEFAULT_PORT = 7373

# What the download button can hand over.
EXPORTS = {
    "3mf": "model/3mf",
    "stl": "model/stl",
    "step": "application/step",
    "glb": "model/gltf-binary",
}

# What a print estimate assumes when nobody has said otherwise. Named here rather than
# in the page, so what it says cannot drift from what was sliced.
LAYER, MATERIAL = "0.20", "PLA"

# The page itself: Vite writes it here from packages/workbench, and the wheel carries
# it. It is not in git, so a checkout that has never run npm has no page to serve.
WORKBENCH = pathlib.Path(__file__).parent / "workbench"
NO_BUNDLE = "the workbench is not built; run: npm install && npm run build --workspace packages/workbench"


# The desktop webview's own three origins: tauri://localhost on macOS and Linux,
# http://tauri.localhost on Windows, and the Vite dev server. Never "*": a page on
# the web must stay unable to read this.
DESKTOP_ORIGINS = ["tauri://localhost", "http://tauri.localhost", "http://localhost:1420"]

# The methods a page may send cross-origin without asking first.
READ_METHODS = {"GET", "HEAD", "OPTIONS"}


def _may_write(origin):
    """Whether a page at `origin` may drive a write."""
    if origin in DESKTOP_ORIGINS:
        return True
    where = urllib.parse.urlsplit(origin)
    # The workbench itself, open in a browser on the loopback port.
    return where.scheme == "http" and where.hostname in ("127.0.0.1", "localhost")


def _origin(scope):
    return next(
        (value.decode("latin-1") for name, value in scope["headers"] if name == b"origin"),
        "",
    )


class SameOrigin:
    """Refuse a write, or a socket, opened by a page on some other origin.

    CORS gates reads, not writes: a simple POST of text/plain runs the handler and only
    the answer is withheld, so /api/import and /api/open would be any web page's to
    call. It gates no socket at all, so without this /ws would stream one user's
    projects to whatever tab is open. Requests with no Origin, like curl and the stdio
    proxy, come from no page.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            origin = _origin(scope)
            if origin and not _may_write(origin):
                # Before accept, so uvicorn answers the handshake with 403.
                await send({"type": "websocket.close", "code": 1008})
                return
        if scope["type"] == "http" and scope["method"] not in READ_METHODS:
            origin = _origin(scope)
            if origin and not _may_write(origin):
                said = b"this page may not change the workbench"
                await send(
                    {
                        "type": "http.response.start",
                        "status": 403,
                        "headers": [
                            (b"content-type", b"text/plain; charset=utf-8"),
                            (b"content-length", str(len(said)).encode()),
                        ],
                    }
                )
                await send({"type": "http.response.body", "body": said})
                return
        await self.app(scope, receive, send)


class AlreadyServing(Exception):
    """Another engine process holds the database. It answers at `url`."""

    def __init__(self, url):
        super().__init__(f"the nurb engine is already running at {url}")
        self.url = url


def state_file():
    return db.home() / STATE


def read_state():
    """What the running serve published, or None. A stale file outlives a crash, so a
    reader confirms with GET /health and the pid before believing it."""
    try:
        return json.loads(state_file().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _take_lock(home):
    import fcntl

    fd = os.open(home / LOCK, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(fd)
        return None
    return fd


def _published_url():
    """The lock holder's URL. It writes the file just after taking the lock, so a
    second serve that arrives in that gap waits rather than reporting nothing. A
    dead holder's file may still exist while its replacement starts, so only a live
    pid-matching health response is publishable."""
    deadline = time.monotonic() + 2.0
    while True:
        state = read_state()
        if state and state.get("url") and _state_alive(state):
            return state["url"]
        if time.monotonic() >= deadline:
            raise SystemExit(
                f"  another process holds {db.home() / LOCK} but published no port.\n"
                f"  Check {db.home() / 'serve.log'}, or kill it and start again."
            )
        time.sleep(0.05)


def _state_alive(state):
    """Probe the loopback URL without honoring ambient proxy variables."""
    import urllib.request

    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(f"{state['url']}/health", timeout=0.5) as response:
            return response.status == 200 and json.load(response).get("pid") == state["pid"]
    except Exception:
        return False


def _is_free(port):
    """Whether the serve could bind this port."""
    import socket

    with socket.socket() as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def _pick_port(asked, remembered=None):
    """The port asked for, else the one this home used last, else the next free one.

    A connect command a user pasted into an agent names a port, so moving after a
    restart breaks it. The remembered port is tried first and only walked past when
    something else holds it.
    """
    if asked is not None:
        return asked
    if remembered and _is_free(remembered):
        return remembered
    for port in range(DEFAULT_PORT, DEFAULT_PORT + 40):
        if _is_free(port):
            return port
    raise SystemExit(f"  no free port between {DEFAULT_PORT} and {DEFAULT_PORT + 39}")


def read_connect(home):
    """The token and port this home hands an agent, minted on the first serve.

    serve.json says where the live process is and dies with it. This outlives it, so
    a command copied into an agent yesterday still connects today.
    """
    try:
        saved = json.loads((home / CONNECT).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        saved = {}
    token = saved.get("token")
    port = saved.get("port")
    return {
        "token": token if isinstance(token, str) and token else secrets.token_urlsafe(24),
        "port": port if type(port) is int and 0 < port < 65536 else None,
    }


def _write_connect(home, token, port):
    tmp = home / (CONNECT + ".tmp")
    tmp.write_text(json.dumps({"token": token, "port": port}), encoding="utf-8")
    os.chmod(tmp, 0o600)  # it carries the token
    os.replace(tmp, home / CONNECT)


def _publish(home, payload):
    tmp = home / (STATE + ".tmp")
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    os.chmod(tmp, 0o600)  # it carries the token
    os.replace(tmp, home / STATE)


class _Bearer:
    """Guards one ASGI app with the token from serve.json."""

    def __init__(self, app, token):
        self.app = app
        self.token = token

    async def __call__(self, scope, receive, send):
        from starlette.responses import PlainTextResponse

        # Bytes on both sides: compare_digest refuses non-ASCII str, and a stranger's
        # header is not the thing that should crash the guard.
        header = dict(scope["headers"]).get(b"authorization", b"")
        offered = header[7:] if header[:7].lower() == b"bearer " else b""
        if not secrets.compare_digest(offered, self.token.encode()):
            await PlainTextResponse("bad token", status_code=401)(scope, receive, send)
            return
        await self.app(scope, receive, send)


def _glb_url(project_id, name, run):
    return f"/glb/{project_id}/{name}.glb?run={run['id']}"


def _render_url(project_id, name, run):
    return f"/render/{project_id}/{name}.png?run={run['id']}"


def _thumbnail_url(project_id, name, run):
    return f"/thumbnail/{project_id}/{name}.png?run={run['id']}"


# Run id to the library card's picture. A run's geometry never changes, so neither
# does its picture, and a library that redraws on every build asks for each again.
THUMBNAILS = {}


def _thumbnail_glb(conn, project_id, name, run_id):
    """The GLB of one successful run of this part, or None."""
    row = conn.execute(
        "SELECT build_runs.glb FROM build_runs"
        " JOIN part_revisions ON part_revisions.id = build_runs.revision_id"
        " JOIN parts ON parts.id = part_revisions.part_id"
        " WHERE build_runs.id = ? AND parts.project_id = ? AND parts.name = ? AND build_runs.status = 'ok'",
        (run_id, project_id, name),
    ).fetchone()
    return row["glb"] if row else None


def _elapsed(started, finished):
    if not started or not finished:
        return None
    started = datetime.datetime.fromisoformat(started)
    return (datetime.datetime.fromisoformat(finished) - started).total_seconds()


def _revision_ordinal(conn, revision_id):
    """Which revision of its part this is, counting from one. There is no ordinal
    column; the order is the order they were written."""
    row = conn.execute(
        "SELECT part_id, created_at FROM part_revisions WHERE id = ?", (revision_id,)
    ).fetchone()
    if row is None:
        return None
    return conn.execute(
        "SELECT COUNT(*) FROM part_revisions WHERE part_id = ? AND created_at <= ?",
        (row["part_id"], row["created_at"]),
    ).fetchone()[0]


def _build_stats(stats):
    named = {
        "size_mm": stats.get("bbox"),
        "volume_mm3": stats.get("volume"),
        "build_s": (stats["ms"] / 1000) if stats.get("ms") is not None else None,
        "render_error": stats.get("render_error"),
    }
    return {key: value for key, value in named.items() if value is not None}


def _build_event(conn, run, project_id, part_name, summary):
    """One build as the transcript draws it, from the stored row."""
    findings = json.loads(run["findings"])
    ok = run["status"] == "ok"
    failed = any(finding.get("severity") == "fail" for finding in findings)
    elapsed = _elapsed(run["started_at"], run["finished_at"])
    return {
        "id": run["id"],
        "part_name": part_name,
        "status": ("failed" if failed else "passed") if ok else "error",
        "started_at": run["started_at"],
        "elapsed_s": elapsed,
        "revision": _revision_ordinal(conn, run["revision_id"]),
        "steps": [
            {
                "id": run["id"],
                "verb": "build",
                "object": part_name,
                "status": "done" if ok else "failed",
                "started_at": run["started_at"],
                "elapsed_s": elapsed,
                "output": summary,
            }
        ],
        # The card lists findings; the face is geometry only the viewer uses.
        "findings": [{k: v for k, v in f.items() if k != "face"} for f in findings],
        "stats": _build_stats(json.loads(run["stats"])),
        "error": run["error"],
        "glb_url": _glb_url(project_id, part_name, run) if ok else None,
        "render_url": _render_url(project_id, part_name, run) if ok else None,
    }


def _step_payload(conn, row, payload):
    tool = payload.get("tool") or ""
    summary = payload.get("summary")
    if tool == "create_project":
        project = db.get_project(conn, row["project_id"])
        verb, what = "create", (project["name"] if project else summary)
    elif tool == "write_part_source":
        verb, what = "write", (payload.get("part_name") or payload.get("subject") or summary)
    else:
        verb, *rest = tool.split("_")
        what = payload.get("subject") or summary or " ".join(rest)
    return {
        "type": "step",
        "step": {
            "id": row["id"],
            "verb": verb,
            "object": what,
            "status": payload.get("status") or "done",
            "started_at": row["created_at"],
            "elapsed_s": payload.get("elapsed_s") or 0,
            "output": summary,
        },
    }


def _message_payload(conn, row, payload):
    run_id = payload.get("run_id")
    if run_id:
        run = conn.execute("SELECT * FROM build_runs WHERE id = ?", (run_id,)).fetchone()
        if run is not None:
            build = _build_event(
                conn, run, row["project_id"], payload.get("part_name"), payload.get("summary")
            )
            return {"type": "build", "build": build}
    if payload.get("type") == "spec_pinned":
        return {"type": "spec", "spec": payload.get("spec")}
    name = payload.get("measurement")
    if name:
        current = conn.execute(
            "SELECT * FROM measurements WHERE project_id = ? AND name = ?",
            (row["project_id"], name),
        ).fetchone()
        return {
            "type": "measurement",
            "measurement": {
                "name": name,
                "value_mm": float(current["value"]) if current else None,
                "how": current["how"] if current else None,
                "provisional": bool(current["provisional"]) if current else False,
                "previous_value_mm": payload.get("previous_value_mm"),
                "stale_parts": payload.get("stale_parts") or [],
            },
        }
    if not payload.get("tool"):
        # A plain turn from the chat column carries no card.
        return None
    return _step_payload(conn, row, payload)


def _shaped(conn, row, payload):
    """The card shape, naming the tool behind it so a live step can find its row."""
    shaped = _message_payload(conn, row, payload)
    if shaped is not None and payload.get("tool"):
        shaped["tool"] = payload["tool"]
    return shaped


def _message(conn, row):
    """A stored message in the shape @nurb/ui renders."""
    payload = json.loads(row["payload"] or "{}")
    return {
        "id": row["id"],
        "role": row["role"],
        "content": row["content"],
        "sequence_number": row["sequence_number"],
        "created_at": row["created_at"],
        "part": row["part"],
        "files": payload.get("files") or [],
        "payload": _shaped(conn, row, payload),
    }


class _Refused(Exception):
    """What the page gets instead of an answer: a status and a sentence."""

    def __init__(self, status, said):
        super().__init__(said)
        self.status = status
        self.said = said


def _part_row(conn, part_id):
    row = conn.execute(
        "SELECT * FROM parts WHERE id = ? AND kind = 'part'", (part_id,)
    ).fetchone()
    if row is None:
        raise _Refused(404, "no such part")
    return row


def _printers():
    """The machines standing in the workshop, the default first."""
    from . import checks, workshop

    # A hand-written key that no shipped profile matches has no bed, and a printer
    # without a bed is a row the page cannot draw or check against.
    have = checks.profiles()
    return [name for name in workshop.workshop_printers() if name in have]


def _printer(printer_toml):
    """The machine this project prints on, as the page draws it.

    A project that never named one prints on the workshop default, which is what
    the rules and the slicer already resolve to, so the header must say the same.
    """
    from . import checks, workshop

    name = mcp_server._printer_profile(printer_toml) or workshop.default_printer()
    if not name:
        return None
    return {"name": name, "bed": checks.profiles().get(name, {}).get("bed")}


def _catalogue_entry(name, block):
    return {
        "name": name,
        "label": block.get("label") or name,
        "brand": block.get("brand") or "",
        "bed": block.get("bed"),
    }


def _slicer_found():
    """The installed slicer, for the page that would otherwise offer a dead button."""
    from . import slicing

    exe = slicing.app()
    if exe is None:
        return None
    path = " ".join(str(v) for v in exe) if isinstance(exe, tuple) else str(exe)
    return {"name": slicing.label(exe), "path": path}


def _workshop():
    """Everything the printer panel draws: what is here, what could be, what slices."""
    from . import checks, workshop

    have = checks.profiles()
    default = workshop.default_printer()
    mine = []
    for name in workshop.workshop_printers():
        # Same reason as _printers(): an unknown key would draw a printer with no bed.
        if name not in have:
            continue
        entry = _catalogue_entry(name, have[name])
        entry["default"] = name == default
        mine.append(entry)
    return {
        "printers": mine,
        # File order, which is grouped by brand, because the picker reads that way.
        "catalogue": [_catalogue_entry(name, block) for name, block in have.items()],
        "slicer": _slicer_found(),
    }


def _params_of(conn, part):
    """The part's parameter rows, from the newest build that reported any.

    A build that raised before the signature was read stores none, so without the
    fallback one failed edit takes the whole parameter panel away and every later
    slider move is refused with "build it once first" about a part built all day.
    """
    run = db.latest_run(conn, part["id"])
    params = json.loads(run["params"]) if run is not None else []
    if params or run is None:
        return params
    row = conn.execute(
        "SELECT b.params FROM build_runs b JOIN part_revisions r ON r.id = b.revision_id"
        " WHERE r.part_id = ? AND b.params != '[]' ORDER BY b.started_at DESC LIMIT 1",
        (part["id"],),
    ).fetchone()
    return json.loads(row["params"]) if row is not None else []


def _kinds(conn, part):
    """Parameter name -> kind, from the part's newest build."""
    return {p["name"]: p.get("kind") for p in _params_of(conn, part)}


def _values(conn, part, values):
    """The page's slider values, typed the way the part's signature declares them."""
    if values in (None, {}):
        return {}
    if not isinstance(values, dict):
        raise _Refused(400, "values must be an object of parameter names to numbers")
    kinds = _kinds(conn, part)
    if not kinds:
        raise _Refused(400, f"build {part['name']} once before changing its parameters")
    typed = {}
    for name, value in values.items():
        kind = kinds.get(name)
        if kind is None:
            raise _Refused(400, f"{part['name']} has no parameter named {name}")
        if kind == "bool":
            # bool("false") is True, so a string here would build the wrong part and
            # say nothing about it.
            if not isinstance(value, bool):
                raise _Refused(400, f"{name} is on or off, not {value!r}")
            typed[name] = value
            continue
        if kind not in ("int", "float"):
            raise _Refused(400, f"{name} is not a number, so the sliders cannot set it")
        wants = "a whole number" if kind == "int" else "a number"
        try:
            number = int(value) if kind == "int" else float(value)
            # JSON carries NaN and Infinity, and an integer of any length at all. OCCT
            # meets a NaN by grinding until the build deadline kills it with the whole
            # page waiting behind the lock, and the value is then stored as an override
            # no JSON reader will take back. isfinite is inside the try because an int
            # too large to be a float overflows there rather than answering False.
            finite = math.isfinite(number)
        except (TypeError, ValueError, OverflowError):
            raise _Refused(400, f"{name} takes {wants}, not {value!r}") from None
        if not finite:
            raise _Refused(400, f"{name} takes {wants}, not {value!r}")
        typed[name] = number
    return typed


def _said(run, part_name):
    """The one line a refusal can carry about a failed build.

    A run's error is the user's own traceback when the part raised. That belongs on
    the build card, where there is room for it; a download or a load case gets the
    sentence at the end of it.
    """
    error = (run["error"] or "").strip()
    return error.splitlines()[-1].strip() if error else f"{part_name} does not build"


def _run_row(conn, run_id):
    return conn.execute("SELECT * FROM build_runs WHERE id = ?", (run_id,)).fetchone()


def _run_for(conn, part, values):
    """The newest run of the part as it stands now, built at exactly these values.

    The revision has to match too. An older revision's geometry is what the viewer
    keeps on screen and marks stale, but a file to print or a load case about it would
    be an answer about source the user has already replaced.
    """
    run = db.latest_ok_run(conn, part["id"])
    if (
        run is not None
        and run["revision_id"] == part["current_revision_id"]
        and json.loads(run["overrides"]) == values
    ):
        return run
    run_id, _ = engine_run.run_build(conn, part["id"], overrides=values or None)
    return _run_row(conn, run_id)


def _result(run, column):
    value = run[column]
    return json.loads(value) if value else None


def _part_build(conn, project_id, part, run):
    if run is None:
        return None
    findings = json.loads(run["findings"])
    ok = run["status"] == "ok"
    shown = run if ok else db.latest_ok_run(conn, part["id"])
    return {
        "id": run["id"],
        "status": run["status"],
        "passed": ok and not any(f.get("severity") == "fail" for f in findings),
        "started_at": run["started_at"],
        "finished_at": run["finished_at"],
        "error": run["error"],
        # With the face: the viewer glows the guilty triangles from it.
        "findings": findings,
        "stats": json.loads(run["stats"]),
        # Measured from this run's geometry, so it dies with it: a new build starts
        # without it rather than carrying the last shape's numbers.
        "slice": _result(run, "slice"),
        # A failed build keeps the last good geometry on screen, the way v1 dimmed the
        # mesh in place; the URLs point at that run while the status says why.
        "glb_url": _glb_url(project_id, part["name"], shown) if shown else None,
        "render_url": _render_url(project_id, part["name"], shown) if shown else None,
        "thumbnail_url": _thumbnail_url(project_id, part["name"], shown) if shown else None,
        "shown_revision": _revision_ordinal(conn, shown["revision_id"]) if shown else None,
        "stale": run["revision_id"] != part["current_revision_id"]
        or (shown is not None and shown["id"] != run["id"]),
    }


def _projects(conn):
    rows = conn.execute(
        "SELECT p.id, p.name, p.created_at, p.folder,"
        " (SELECT COUNT(*) FROM parts WHERE project_id = p.id AND kind = 'part') AS parts,"
        " (SELECT MAX(b.started_at) FROM build_runs b"
        "  JOIN part_revisions r ON r.id = b.revision_id"
        "  JOIN parts pa ON pa.id = r.part_id WHERE pa.project_id = p.id) AS last_built"
        " FROM projects p ORDER BY p.created_at"
    ).fetchall()
    return [{**dict(row), "folder": bool(row["folder"])} for row in rows]


def _part_entry(conn, project_id, part):
    """One part as a page draws it: its source, its sliders, and its last build."""
    # Without a revision_id: a crashed edit still shows the last picture, stale.
    run = db.latest_run(conn, part["id"])
    params = _params_of(conn, part)
    return {
        "id": part["id"],
        "name": part["name"],
        "title": part["title"],
        "kind": part["kind"],
        "revision_id": part["current_revision_id"],
        "revision": _revision_ordinal(conn, part["current_revision_id"]),
        "source": part["source"],
        "card_md": part["card_md"],
        "params": [
            {
                "name": p.get("name"),
                "kind": p.get("kind"),
                "default": p.get("default"),
                "description": p.get("doc"),
            }
            for p in params
        ],
        # What the sliders are standing on: the values that last build used.
        "overrides": json.loads(run["overrides"]) if run is not None else {},
        "build": _part_build(conn, project_id, part, run),
    }


def _all_parts(conn):
    """Every part in the store, which is what the library's one grid draws."""
    out = []
    for row in conn.execute("SELECT * FROM projects ORDER BY created_at").fetchall():
        for part in db.parts_of(conn, row["id"]):
            if part["kind"] != "part":
                continue
            out.append(
                {
                    **_part_entry(conn, row["id"], part),
                    "project_id": row["id"],
                    "project_name": row["name"],
                    "folder": bool(row["folder"]),
                }
            )
    return out


def _project(conn, project_id, part=None):
    """Everything one page draws, in one read: the project, its parts with their last
    build, and the transcript. Name a part to read only that part's side of the chat."""
    row = db.get_project(conn, project_id)
    if row is None:
        return None
    parts = [
        _part_entry(conn, project_id, entry)
        for entry in db.parts_of(conn, project_id)
        if entry["kind"] == "part"
    ]
    if part is None:
        messages = conn.execute(
            "SELECT * FROM messages WHERE project_id = ? ORDER BY sequence_number", (project_id,)
        ).fetchall()
    else:
        messages = conn.execute(
            "SELECT * FROM messages WHERE project_id = ? AND part = ? ORDER BY sequence_number",
            (project_id, part),
        ).fetchall()
    return {
        "id": row["id"],
        "name": row["name"],
        "folder": bool(row["folder"]),
        "created_at": row["created_at"],
        "printer": _printer(row["printer_toml"]),
        "printers": _printers(),
        "spec": spec.current(conn, project_id),
        "measurements": [
            {
                "name": m["name"],
                "value_mm": float(m["value"]),
                "unit": m["unit"],
                "how": m["how"],
                "provisional": bool(m["provisional"]),
                "value_changed_at": m["value_changed_at"],
            }
            for m in db.measurements_of(conn, project_id)
        ],
        "parts": parts,
        # The family's shared files and which parts import each, so the page can say
        # that one edit moves the set.
        "shared": [
            {"name": entry["name"], "used_by": [user["name"] for user in mcp_server.importers(conn, project_id, entry["id"])]}
            for entry in db.parts_of(conn, project_id)
            if entry["kind"] == "module"
        ],
        "messages": [_message(conn, message) for message in messages],
    }


def _grouped_repeats(runs, limit=5):
    """One row per set of parts: two parts that repeat three stretches are one thing to
    lift, not three, so the stretches add up and their sources are kept together."""
    groups = {}
    for run in runs:
        group = groups.setdefault(tuple(run["parts"]), {"parts": run["parts"], "statements": 0, "source": []})
        group["statements"] += run["statements"]
        group["source"].append(run["source"])
    out = sorted(groups.values(), key=lambda g: -g["statements"])[:limit]
    for group in out:
        group["source"] = "\n\n".join(group["source"])
    return out


def _system(conn, project_id):
    """The project as a system: its shared files with their settings and pieces, and
    its measurements, each with the parts that would rebuild if it changed."""
    from . import shared

    rows = list(db.parts_of(conn, project_id))
    parts = [row for row in rows if row["kind"] == "part"]
    files = []
    for row in rows:
        if row["kind"] != "module":
            continue
        files.append(
            {
                "name": row["name"],
                "used_by": [user["name"] for user in mcp_server.importers(conn, project_id, row["id"])],
                "settings": shared.settings(row["source"]),
                "pieces": [
                    {"name": piece, "used_by": [p["name"] for p in parts if shared.uses(p["source"], row["name"], piece)]}
                    for piece in shared.pieces(row["source"])
                ],
            }
        )
    reads = mcp_server._measurement_uses(rows, db.project_files_of(conn, project_id))
    names = {row["id"]: row["name"] for row in parts}
    return {
        "files": files,
        # What sibling parts say twice: the moment a system is waiting to be lifted.
        "repeats": _grouped_repeats(shared.repeats({row["name"]: row["source"] for row in parts}, limit=20)),
        "measurements": [
            {
                "name": m["name"],
                "value_mm": float(m["value"]),
                "how": m["how"],
                "provisional": bool(m["provisional"]),
                "used_by": [names[part_id] for part_id, used in reads.items() if part_id in names and m["name"] in used],
            }
            for m in db.measurements_of(conn, project_id)
        ],
    }


def _composite(conn, project_id, name):
    """The part's newest picture, rendered now if the run predates renders."""
    row = conn.execute(
        "SELECT id FROM parts WHERE project_id = ? AND name = ? AND kind = 'part'",
        (project_id, name),
    ).fetchone()
    if row is None:
        return None
    run = db.latest_ok_run(conn, row["id"])
    if run is None:
        return None
    try:
        return mcp_server._render_of(conn, run)
    except Exception:
        # A build can be ok and still have no picture: the rasterizer failed and the
        # run kept a render_error. Retrying it here answers "no render", not a 500.
        return None


def _routes(conn, lock, server, token, pid):
    import anyio
    from mcp.server.streamable_http_manager import StreamableHTTPASGIApp, StreamableHTTPSessionManager
    from mcp.server.transport_security import TransportSecuritySettings
    from starlette.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response
    from starlette.routing import Mount, Route, WebSocketRoute
    from starlette.staticfiles import StaticFiles
    from starlette.websockets import WebSocketDisconnect

    manager = StreamableHTTPSessionManager(
        app=server,
        stateless=True,
        json_response=True,
        security_settings=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=["127.0.0.1:*", "localhost:*"],
            allowed_origins=["http://127.0.0.1:*", "http://localhost:*"],
        ),
    )

    async def query(work):
        """One read, on the thread and under the lock the tools use, so a read never
        races a build that is halfway through writing its rows."""

        def go():
            with lock:
                return work(conn)

        return await anyio.to_thread.run_sync(go)

    one_slicer = threading.Lock()

    async def read(sql, args):
        return await query(lambda conn: conn.execute(sql, args).fetchall())

    def answering(handler):
        """Turn a route's refusal into the status and the sentence it named."""

        async def route(request):
            try:
                return await handler(request)
            except _Refused as refused:
                return JSONResponse({"error": refused.said}, status_code=refused.status)

        return route

    async def acted(work):
        """One write on the build thread. A work function with bytes to hand over
        returns its own Response; everything else is JSON."""
        payload = await query(work)
        return payload if isinstance(payload, Response) else JSONResponse(payload)

    def word(sent, key, said, most=None):
        """One string a route was sent. Anything else is the sentence it names."""
        value = sent.get(key)
        if value is not None and not isinstance(value, str):
            raise _Refused(400, said)
        value = (value or "").strip()
        if most is not None and len(value) > most:
            raise _Refused(400, f"{key} can be at most {most} characters")
        return value

    async def body_of(request):
        try:
            sent = await request.json()
        except ValueError:
            raise _Refused(400, "the request body must be JSON") from None
        if not isinstance(sent, dict):
            raise _Refused(400, "the request body must be a JSON object")
        return sent

    async def project_create(request):
        """A new empty project, named or not."""
        sent = await body_of(request)

        def work(conn):
            name = word(sent, "name", "name must be what to call the project", db.NAME_LIMIT) or mcp_server._placeholder_name(conn)
            folder = sent.get("folder", False)
            if not isinstance(folder, bool):
                raise _Refused(400, "folder must be true for a folder of parts, false for one part")
            return {"id": db.create_project(conn, name, folder=folder), "name": name, "folder": folder}

        return await acted(work)

    async def project_import(request):
        """Read a folder of parts on disk into the database."""
        sent = await body_of(request)

        def work(conn):
            from . import folder

            path = word(sent, "path", "path must be the folder to import")
            if not path:
                raise _Refused(400, "path must be the folder to import")
            # A typed path can be "~/parts", and a path that is not there at all
            # deserves that sentence rather than one about a missing parts/.
            folder_path = pathlib.Path(path).expanduser()
            if not folder_path.is_dir():
                raise _Refused(400, f"no folder at {folder_path}")
            try:
                project_id, parts = folder.import_folder(conn, folder_path)
            except ValueError as exc:
                raise _Refused(400, str(exc)) from None
            except OSError as exc:
                raise _Refused(400, f"cannot read {folder_path}: {exc.strerror}") from None
            return {"id": project_id, "name": db.get_project(conn, project_id)["name"], "parts": parts}

        return await acted(work)

    async def project_message(request):
        """One turn of the transcript, from whatever is driving the chat."""
        sent = await body_of(request)

        def work(conn):
            project_id = request.path_params["project_id"]
            role = word(sent, "role", "role must be user or assistant")
            content = word(sent, "content", "content must be what was said")
            if role not in ("user", "assistant"):
                raise _Refused(400, "role must be user or assistant")
            files = sent.get("files") or []
            if not isinstance(files, list) or not all(isinstance(name, str) for name in files):
                raise _Refused(400, "files must be the names of what was attached")
            # A photo alone is a legitimate message, so a file stands in for words.
            if not content and not files:
                raise _Refused(400, "content must be what was said")
            if db.get_project(conn, project_id) is None:
                raise _Refused(404, "no project")
            part = word(sent, "part", "part must be the name of a part in this project") or None
            if part is not None and conn.execute(
                "SELECT 1 FROM parts WHERE project_id = ? AND name = ? AND kind = 'part'",
                (project_id, part),
            ).fetchone() is None:
                raise _Refused(400, f"no part called {part} in this project")
            payload = {"files": files} if files else {}
            message_id = db.add_message(conn, project_id, role, content, payload, part=part)
            row = conn.execute("SELECT * FROM messages WHERE id = ?", (message_id,)).fetchone()
            return JSONResponse(_message(conn, row), status_code=201)

        return await acted(work)

    async def project_message_claim(request):
        """Give a new part the turns that described it before it had a name."""
        sent = await body_of(request)

        def work(conn):
            project_id = request.path_params["project_id"]
            part = word(sent, "part", "part must be the name of a part in this project")
            after = sent.get("after")
            if not isinstance(after, int) or isinstance(after, bool) or after < 0:
                raise _Refused(400, "after must be the last turn before the new part was started")
            if db.get_project(conn, project_id) is None:
                raise _Refused(404, "no project")
            if conn.execute(
                "SELECT 1 FROM parts WHERE project_id = ? AND name = ? AND kind = 'part'",
                (project_id, part),
            ).fetchone() is None:
                raise _Refused(400, f"no part called {part} in this project")
            return {"claimed": db.claim_messages(conn, project_id, part, after)}

        return await acted(work)

    async def project_attachment(request):
        """Keep a photo from the chat with the project, so the next conversation can see it."""
        sent = await body_of(request)

        def work(conn):
            project_id = request.path_params["project_id"]
            name = word(sent, "name", "name must be the photo's file name")
            mime = word(sent, "mime", "mime must be the photo's type")
            if not name or pathlib.PurePosixPath(name).name != name or name == "..":
                raise _Refused(400, "name must be a file name, not a path")
            if not mime.startswith("image/"):
                raise _Refused(400, "only photos are kept with a project")
            try:
                data = base64.b64decode(word(sent, "data", "data must be base64"), validate=True)
            except ValueError:
                raise _Refused(400, "data must be base64") from None
            if db.get_project(conn, project_id) is None:
                raise _Refused(404, "no project")
            db.add_attachment(conn, project_id, name, mime, data)
            return JSONResponse({"name": name}, status_code=201)

        return await acted(work)

    async def mesh_describe(request):
        """A mesh file attached to a chat, as its size in words and a four-view picture.

        Off the database lock: it reads a file, not the store, and a dense mesh takes
        seconds a build should not wait behind.
        """
        from . import scan

        sent = await body_of(request)
        path = word(sent, "path", "path must be the mesh file to describe")
        if not path:
            raise _Refused(400, "path must be the mesh file to describe")
        try:
            text, picture = await anyio.to_thread.run_sync(scan.describe, pathlib.Path(path).expanduser())
        except ValueError as exc:
            raise _Refused(400, str(exc)) from None
        return JSONResponse({"text": text, "png": base64.b64encode(picture).decode()})

    async def project_rename(request):
        """Call a project something else. The name is a label, so nothing on disk moves."""
        sent = await body_of(request)

        def work(conn):
            project_id = request.path_params["project_id"]
            name = word(sent, "name", "name must be what to call the project", db.NAME_LIMIT)
            if not name:
                raise _Refused(400, "name must be what to call the project")
            if db.get_project(conn, project_id) is None:
                raise _Refused(404, "no project")
            db.rename_project(conn, project_id, name)
            return next(row for row in _projects(conn) if row["id"] == project_id)

        return await acted(work)

    async def project_system(request):
        """The project's shared files, settings, pieces and measurements."""
        project_id = request.path_params["project_id"]

        def work(conn):
            if db.get_project(conn, project_id) is None:
                raise _Refused(404, "no project")
            return _system(conn, project_id)

        return await acted(work)

    async def project_setting(request):
        """Set one number in a shared file and rebuild every part that imports it."""
        sent = await body_of(request)
        project_id = request.path_params["project_id"]

        def work(conn):
            from . import shared

            file = word(sent, "file", "file must name the shared file")
            name = word(sent, "name", "name must name the setting")
            row = next(
                (r for r in db.parts_of(conn, project_id) if r["kind"] == "module" and r["name"] == file), None
            )
            if row is None:
                raise _Refused(404, f"no shared file called {file}")
            try:
                source = shared.set_setting(row["source"], name, sent.get("value"))
            except ValueError as exc:
                raise _Refused(400, str(exc)) from None
            if source != row["source"]:
                db.add_revision(conn, row["id"], source, note=f"Set {name} to {sent['value']} from the project panel")
                users = mcp_server.importers(conn, project_id, row["id"])
                engine_run.want_rebuild([user["id"] for user in users], project_id)
                db.add_message(
                    conn,
                    project_id,
                    "assistant",
                    f"Set {name} to {sent['value']} in {file}; {len(users)} parts rebuilding.",
                    {"tool": "apply_setting", "summary": f"{name} = {sent['value']} in {file}"},
                )
            return _system(conn, project_id)

        return await acted(work)

    async def project_measurement(request):
        """Correct a measurement's value from the app and rebuild the parts that read it."""
        sent = await body_of(request)
        project_id = request.path_params["project_id"]
        name = request.path_params["name"]

        def work(conn):
            row = conn.execute(
                "SELECT * FROM measurements WHERE project_id = ? AND name = ?", (project_id, name)
            ).fetchone()
            if row is None:
                raise _Refused(404, f"no measurement called {name}")
            value = sent.get("value_mm")
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise _Refused(400, "value_mm must be a number of millimetres")
            result = mcp_server.record_measurement(
                conn,
                {
                    "project_id": project_id,
                    "name": name,
                    "value_mm": value,
                    "how": row["how"],
                    "provisional": bool(row["provisional"]),
                    "note": "Corrected from the project panel",
                },
                "",
            )
            if result.is_error:
                raise _Refused(400, result.content[0].text)
            if float(row["value"]) != float(value):
                # Every part that reads it, built or not: the panel promised them all.
                rows = list(db.parts_of(conn, project_id))
                reads = mcp_server._measurement_uses(rows, db.project_files_of(conn, project_id))
                engine_run.want_rebuild(
                    [r["id"] for r in rows if r["kind"] == "part" and name in reads.get(r["id"], [])], project_id
                )
            return _system(conn, project_id)

        return await acted(work)

    async def part_rename(request):
        """Call a part something else, in the words a person typed."""
        sent = await body_of(request)

        def work(conn):
            part = _part_row(conn, request.path_params["part_id"])
            typed = word(sent, "name", "name must be what to call the part") or ""
            name = db.part_name_from(typed)
            try:
                db.rename_part(conn, part["id"], name, title=typed)
            except ValueError as exc:
                raise _Refused(400, str(exc)) from None
            return {"id": part["id"], "name": name, "title": typed.strip() or None, "was": part["name"]}

        return await acted(work)

    async def project_folder(request):
        """Promote a one-part container into a folder of parts, and name it."""
        sent = await body_of(request)

        def work(conn):
            project_id = request.path_params["project_id"]
            name = word(sent, "name", "name must be what to call the folder", db.NAME_LIMIT)
            if not name:
                raise _Refused(400, "name must be what to call the folder")
            if db.get_project(conn, project_id) is None:
                raise _Refused(404, "no project")
            db.promote_to_folder(conn, project_id, name)
            return next(row for row in _projects(conn) if row["id"] == project_id)

        return await acted(work)

    async def part_move(request):
        """Carry a part into another project, its history and its chat with it."""
        sent = await body_of(request)

        def work(conn):
            part_id = request.path_params["part_id"]
            project_id = word(sent, "project_id", "project_id must be the project to move the part into")
            if not project_id:
                raise _Refused(400, "project_id must be the project to move the part into")
            if conn.execute("SELECT 1 FROM parts WHERE id = ?", (part_id,)).fetchone() is None:
                raise _Refused(404, "no such part")
            if db.get_project(conn, project_id) is None:
                raise _Refused(404, "no project")
            try:
                db.move_part(conn, part_id, project_id)
            except ValueError as exc:
                raise _Refused(409, str(exc)) from None
            return {"id": part_id, "project_id": project_id}

        return await acted(work)

    async def part_delete(request):
        def work(conn):
            part_id = request.path_params["part_id"]
            try:
                project_id, whole = db.delete_part(conn, part_id)
            except ValueError:
                raise _Refused(404, "no such part") from None
            return {"deleted": part_id, "project_id": project_id, "project_deleted": whole}

        return await acted(work)

    async def project_delete(request):
        def work(conn):
            project_id = request.path_params["project_id"]
            if db.get_project(conn, project_id) is None:
                raise _Refused(404, "no project")
            db.delete_project(conn, project_id)
            return {"deleted": project_id}

        return await acted(work)

    async def part_params(request):
        """Build at the values on the sliders, without touching the source."""
        sent = await body_of(request)

        def work(conn):
            part = _part_row(conn, request.path_params["part_id"])
            values = _values(conn, part, sent.get("values"))
            run_id, _ = engine_run.run_build(conn, part["id"], overrides=values or None)
            run = _run_row(conn, run_id)
            return {"build": _part_build(conn, part["project_id"], part, run)}

        return await acted(work)

    async def part_apply(request):
        """Write the slider values into the signature, as a new revision."""
        sent = await body_of(request)

        def work(conn):
            part = _part_row(conn, request.path_params["part_id"])
            values = _values(conn, part, sent.get("values"))
            current = conn.execute(
                "SELECT source, card_md FROM part_revisions WHERE id = ?",
                (part["current_revision_id"],),
            ).fetchone()
            try:
                source, written, skipped = edit.apply_to_source(current["source"], values)
            except edit.EditError as exc:
                raise _Refused(400, str(exc)) from None
            skipped = [{"name": name, "why": why} for name, why in skipped]
            if not written:
                # Nothing moved off its default, so there is nothing to commit and
                # nothing to rebuild. A revision here would be a diff of nothing.
                run = db.latest_run(conn, part["id"])
                return {
                    "revision_id": part["current_revision_id"],
                    "revision": _revision_ordinal(conn, part["current_revision_id"]),
                    "written": [],
                    "skipped": skipped,
                    "build": _part_build(conn, part["project_id"], part, run),
                }
            # Spoken the way the sliders are labelled: the transcript is read by
            # whoever owns the printer, not by whoever reads the signature.
            spoken = ", ".join(name.replace("_", " ") for name in written)
            note = f"Applied {spoken} from the sliders"
            revision_id = db.add_revision(
                conn, part["id"], source, card_md=current["card_md"], note=note
            )
            run_id, _ = engine_run.run_build(conn, part["id"])
            run = _run_row(conn, run_id)
            part = _part_row(conn, part["id"])  # its current revision has moved
            build = _part_build(conn, part["project_id"], part, run)
            # The transcript draws this as a build, the same as one a tool ran.
            db.add_message(
                conn,
                part["project_id"],
                "assistant",
                f"{note} to {part['name']}.",
                {
                    "tool": "apply_params",
                    "summary": f"{part['name']} built: {run['status']}, "
                    f"{len(build['findings'])} findings",
                    "run_id": run_id,
                    "part_name": part["name"],
                },
            )
            return {
                "revision_id": revision_id,
                "revision": _revision_ordinal(conn, revision_id),
                "written": written,
                "skipped": skipped,
                "build": build,
            }

        return await acted(work)

    async def part_export(request):
        """The part as a file, built at the values the page is holding."""
        sent = await body_of(request)

        def work(conn):
            part = _part_row(conn, request.path_params["part_id"])
            fmt = str(sent.get("format") or "").lower()
            if fmt not in EXPORTS:
                raise _Refused(400, f"nurb exports {', '.join(EXPORTS)}, not {fmt!r}")
            values = _values(conn, part, sent.get("values"))
            note = None
            if fmt == "glb":
                # The viewer's geometry is already stored; only a different set of
                # values is worth a rebuild.
                run = _run_for(conn, part, values)
                if run["glb"] is None:
                    raise _Refused(409, _said(run, part["name"]))
                body = run["glb"]
            else:
                try:
                    body, _, note = engine_run.export_part(
                        conn, part["id"], fmt, overrides=values or None
                    )
                except ValueError as exc:
                    raise _Refused(409, str(exc)) from None
            headers = {
                "Content-Disposition": f'attachment; filename="{part["name"]}.{fmt}"',
                "Cache-Control": "no-store",
            }
            if note:
                # What the 3MF carries besides geometry, for the note under the button.
                # A header is one line, and a slicer's reason can run to several.
                headers["X-Nurb-Print-Settings"] = " ".join(note.split())
            return Response(body, media_type=EXPORTS[fmt], headers=headers)

        return await acted(work)

    async def part_slice(request):
        """What this print costs: the two numbers only a slicer knows.

        Anything other than a number is a state the page can act on rather than a
        crash, so it comes back as 200 with a `kind`. `choose` is the common one and
        is why `profiles` rides along: the answer to a machine nobody has named yet is
        a picker, not a sentence about a file the user has never opened.
        """

        def work(conn):
            import tempfile

            from . import checks, slicing

            part = _part_row(conn, request.path_params["part_id"])
            exe = slicing.app()
            if exe is None:
                # Not a fault and not the user's mistake: nurb reads these numbers out
                # of a slicer rather than re-deriving them, so without one there is no
                # answer to give. No retry fixes this and the page installs nothing.
                return {
                    "kind": "slicer",
                    "error": "no slicer found. print time comes out of "
                    f"{' or '.join(slicing.SLICERS)}, both free.",
                }
            # Its own folder: the shared scratch copy is the build worker's, and the
            # background builder can be writing it at this moment.
            with tempfile.TemporaryDirectory() as own:
                root = materialize.materialize(conn, part["project_id"], into=own)
                try:
                    wanted, profile = checks.slicer_name(root)
                except ValueError as exc:
                    return {"kind": "printer", "error": str(exc), "profiles": _printers()}
            if not wanted:
                return {"kind": "choose", "profiles": _printers()}
            bundle = slicing.vendors(exe)
            if bundle is None:
                # The app is here and its own profiles are not: a broken install.
                return {
                    "kind": "profile",
                    "error": f"found {slicing.label(exe)} but not its profile bundle",
                }
            try:
                machine = slicing.machine(bundle, wanted)
                process, filament = slicing.profiles_for(machine, LAYER, MATERIAL)
            except slicing.Unavailable as exc:
                # The machines ride along: what fixes this is choosing a different one,
                # not pressing the same button again.
                return {"kind": "profile", "error": str(exc), "profiles": _printers()}

            run = db.latest_ok_run(conn, part["id"])
            if run is None:
                return {"kind": "build", "error": f"{part['name']} has no build to slice"}
            overrides = json.loads(run["overrides"]) or None
            try:
                model, _, _ = engine_run.export_part(conn, part["id"], "stl", overrides=overrides)
            except ValueError as exc:
                return {"kind": "build", "error": str(exc)}
            return part["name"], run["id"], model, exe, machine, process, filament, profile

        prepared = await query(work)
        if isinstance(prepared, dict):
            return JSONResponse(prepared)
        name, run_id, model, exe, machine, process, filament, profile = prepared

        def sliced():
            from . import slicing

            # Outside the server lock, because a slicer can take minutes and every build
            # starts one; one at a time, because two would fight over the same cores.
            with one_slicer, tempfile.TemporaryDirectory() as scratch:
                stl = pathlib.Path(scratch) / f"{name}.stl"
                stl.write_bytes(model)
                try:
                    (seconds, grams), _ = slicing.run(
                        stl, pathlib.Path(scratch) / f"{name}.gcode", machine, process, filament, exe
                    )
                except slicing.Unavailable as exc:
                    return {"kind": "build", "error": str(exc)}
                except Exception as exc:
                    return {"kind": "build", "error": f"{type(exc).__name__}: {exc}"}
            return {
                "kind": "slice",
                "seconds": seconds,
                "spoken": slicing.spoken(seconds),
                "weight": slicing.weighed(grams),
                "grams": grams,
                # The machine alone on the row, because with two printers in the
                # workshop that is the one word that changes how the number reads.
                "profile": profile,
                "settings": f"{profile} / {process.stem} / {filament.stem} / {slicing.PLATE}",
            }

        payload = await anyio.to_thread.run_sync(sliced)
        if payload["kind"] != "slice":
            return JSONResponse(payload)

        def save(conn):
            try:
                db.set_run_result(conn, run_id, "slice", payload)
            except ValueError as exc:  # the part went away while its slicer ran
                return {"kind": "build", "error": str(exc)}
            return {**payload, "run_id": run_id}

        return await acted(save)

    async def printers_read(request):
        """The workshop: the machines here, everything that could be, and the slicer."""
        return JSONResponse(_workshop())

    async def printers_add(request):
        """Put a machine in the workshop. The first one becomes the default."""
        sent = await body_of(request)
        from . import workshop

        try:
            workshop.add_workshop_printer(word(sent, "profile", "profile must be a printer key"))
        except ValueError as exc:
            raise _Refused(400, str(exc)) from None
        db.changed("workshop", "workshop", None)
        return JSONResponse(_workshop())

    async def printers_remove(request):
        """Take a machine out. The next one standing inherits the default, and any
        project that named the removed one goes back to the workshop's answer, so
        no part keeps pricing itself on a machine that is no longer on the bench."""
        from . import mcp_server, workshop

        name = request.path_params["profile"]

        def work(conn):
            try:
                workshop.remove_workshop_printer(name)
            except ValueError as exc:
                raise _Refused(404, str(exc)) from None
            rows = conn.execute(
                "SELECT id, printer_toml FROM projects WHERE printer_toml IS NOT NULL"
            ).fetchall()
            for row in rows:
                if mcp_server._printer_profile(row["printer_toml"]) == name:
                    db.set_printer(conn, row["id"], None)
            db.changed("workshop", "workshop", None)
            return _workshop()

        return await acted(work)

    async def printers_default(request):
        """Name the machine every project uses unless it says otherwise."""
        sent = await body_of(request)
        from . import workshop

        try:
            workshop.set_default_printer(word(sent, "profile", "profile must be a printer key"))
        except ValueError as exc:
            raise _Refused(400, str(exc)) from None
        db.changed("workshop", "workshop", None)
        return JSONResponse(_workshop())

    async def project_printer(request):
        """Name the machine this project prints on, or clear it for the workshop's."""
        sent = await body_of(request)

        def work(conn):
            from . import checks

            project_id = request.path_params["project_id"]
            if db.get_project(conn, project_id) is None:
                raise _Refused(404, "no project")
            if sent.get("profile") is None:
                # Back to the workshop default, which is the answer for most projects.
                db.set_printer(conn, project_id, None)
                return {"printer": _printer(None)}
            name = str(sent.get("profile") or "")
            have = checks.profiles()
            if name not in have:
                raise _Refused(
                    400, f"no printer profile called {name!r}. Have: {', '.join(sorted(have))}"
                )
            printer_toml = f'profile = "{name}"\n'
            db.set_printer(conn, project_id, printer_toml)
            return {"printer": _printer(printer_toml)}

        return await acted(work)

    async def part_source(request):
        """Capture a part file written in a working folder as a new revision."""
        sent = await body_of(request)

        def work(conn):
            project_id = request.path_params["project_id"]
            if db.get_project(conn, project_id) is None:
                raise _Refused(404, "no project")
            source = sent.get("source")
            if not isinstance(source, str):
                raise _Refused(400, "source must be the part's source")
            args = {
                "project_id": project_id,
                "part_name": request.path_params["part_name"],
                "source": source,
                "note": word(sent, "note", "note must be a sentence about the change") or None,
            }
            try:
                result = mcp_server.write_part_source(conn, args, str(request.base_url).rstrip("/"))
            except mcp_server.Refused as exc:
                raise _Refused(400, str(exc)) from None
            if result.is_error:
                raise _Refused(400, mcp_server._text_of(result))
            return json.loads(mcp_server._text_of(result))

        return await acted(work)

    async def project_checkout(request):
        """Write a project out as a folder of part files, for a user who wants them."""
        sent = await body_of(request)

        def work(conn):
            from . import folder

            project_id = request.path_params["project_id"]
            if db.get_project(conn, project_id) is None:
                raise _Refused(404, "no project")
            where = sent.get("directory")
            if not isinstance(where, str) or not where.strip():
                raise _Refused(400, "directory must be where to write the project")
            target = pathlib.Path(where.strip()).expanduser()
            try:
                root = folder.checkout(conn, project_id, target)
            except ValueError as exc:
                raise _Refused(400, str(exc)) from None
            except OSError as exc:
                raise _Refused(400, f"cannot write {target}: {exc.strerror}") from None
            names = [row["name"] for row in db.parts_of(conn, project_id) if row["kind"] == "part"]
            return {"directory": str(root), "parts": names}

        return await acted(work)

    async def health(request):
        return JSONResponse({"ok": True, "pid": pid})

    async def glb(request):
        name = request.path_params["part"]
        if not db.PART_NAME.match(name):
            return PlainTextResponse("no geometry", status_code=404)
        rows = await read(
            "SELECT b.glb FROM build_runs b"
            " JOIN part_revisions r ON r.id = b.revision_id"
            " JOIN parts p ON p.id = r.part_id"
            " WHERE p.project_id = ? AND p.name = ? AND b.status = 'ok' AND b.glb IS NOT NULL"
            " ORDER BY b.started_at DESC LIMIT 1",
            (request.path_params["project_id"], name),
        )
        if not rows:
            return PlainTextResponse("no geometry", status_code=404)
        return Response(
            rows[0]["glb"],
            media_type="model/gltf-binary",
            # The URL does not name a revision, so what it points at changes on
            # every build. A cached copy would be last hour's part.
            headers={"Cache-Control": "no-store"},
        )

    async def render(request):
        name = request.path_params["part"]
        if not db.PART_NAME.match(name):
            return PlainTextResponse("no render", status_code=404)
        # Rendering an older run's picture takes a moment, so it goes to the thread
        # with every other read rather than blocking the loop.
        png = await query(lambda conn: _composite(conn, request.path_params["project_id"], name))
        if png is None:
            return PlainTextResponse("no render", status_code=404)
        return Response(png, media_type="image/png", headers={"Cache-Control": "no-store"})

    async def thumbnail(request):
        """The library card's picture: the part alone from the front-left corner, on
        nothing, so the card's own ground shows through. Rendered off the lock, because
        a library full of new builds asks for dozens at once."""
        from . import raster

        project_id, name = request.path_params["project_id"], request.path_params["part"]
        run_id = request.query_params.get("run", "")
        png = THUMBNAILS.get(run_id)
        if png is None:
            glb = await query(lambda conn: _thumbnail_glb(conn, project_id, name, run_id))
            if glb is None:
                return PlainTextResponse("no thumbnail", status_code=404)
            try:
                png = await anyio.to_thread.run_sync(lambda: raster.render(glb, width=640, height=480, view="iso"))
            except Exception:
                return PlainTextResponse("no thumbnail", status_code=404)
            if len(THUMBNAILS) > 1000:
                THUMBNAILS.clear()
            THUMBNAILS[run_id] = png
        return Response(png, media_type="image/png", headers={"Cache-Control": "max-age=31536000, immutable"})

    async def projects(request):
        return JSONResponse({"projects": await query(_projects)})

    async def parts(request):
        return JSONResponse({"parts": await query(_all_parts)})

    async def project(request):
        project_id = request.path_params["project_id"]
        part = request.query_params.get("part") or None
        payload = await query(lambda conn: _project(conn, project_id, part))
        if payload is None:
            return JSONResponse({"error": "no project"}, status_code=404)
        return JSONResponse(payload)

    async def index(request):
        page = WORKBENCH / "index.html"
        if not page.is_file():
            return PlainTextResponse(NO_BUNDLE, status_code=503)
        # The bundle is rebuilt in place, so a cached page would be the old app
        # asking for asset names that no longer exist.
        return HTMLResponse(page.read_bytes(), headers={"Cache-Control": "no-store"})

    sockets = set()
    running = {"loop": None}

    def deliver(event):
        for queue in list(sockets):
            queue.put_nowait(event)

    def fan_out(kind, row_id, project_id):
        """db's bus calls this from whichever thread did the write, and an
        asyncio.Queue is not thread-safe, so the hop onto the loop is the point."""
        loop = running["loop"]
        if loop is None:
            return
        loop.call_soon_threadsafe(deliver, {"kind": kind, "id": row_id, "project_id": project_id})

    @contextlib.asynccontextmanager
    async def events():
        running["loop"] = asyncio.get_running_loop()
        db.listeners.append(fan_out)
        try:
            yield
        finally:
            # A stale listener would outlive this serve and fire into a dead loop.
            db.listeners.remove(fan_out)
            running["loop"] = None

    async def ws(websocket):
        await websocket.accept()
        queue = asyncio.Queue()
        sockets.add(queue)
        try:
            async with anyio.create_task_group() as tasks:

                async def push():
                    while True:
                        event = await queue.get()
                        try:
                            await websocket.send_json(event)
                        except (WebSocketDisconnect, RuntimeError):
                            tasks.cancel_scope.cancel()
                            return

                async def watch():
                    # Nothing is expected from the page. The disconnect only arrives
                    # through receive(), so without this reader a sender waiting on
                    # the queue never learns the tab closed.
                    try:
                        while True:
                            await websocket.receive_text()
                    except (WebSocketDisconnect, RuntimeError):
                        pass
                    tasks.cancel_scope.cancel()

                tasks.start_soon(push)
                tasks.start_soon(watch)
        finally:
            sockets.discard(queue)

    routes = [
        # A Route, not a Mount: /mcp is one endpoint, and /mcp/ redirects to it.
        Route("/mcp", endpoint=_Bearer(StreamableHTTPASGIApp(manager), token)),
        Route("/health", endpoint=health),
        Route("/api/projects", endpoint=projects),
        Route("/api/projects", endpoint=answering(project_create), methods=["POST"]),
        Route("/api/import", endpoint=answering(project_import), methods=["POST"]),
        Route("/api/projects/{project_id}", endpoint=project),
        Route("/api/projects/{project_id}", endpoint=answering(project_rename), methods=["PATCH"]),
        Route("/api/projects/{project_id}", endpoint=answering(project_delete), methods=["DELETE"]),
        Route("/api/projects/{project_id}/folder", endpoint=answering(project_folder), methods=["POST"]),
        Route("/api/parts", endpoint=parts),
        Route("/api/parts/{part_id}/project", endpoint=answering(part_move), methods=["POST"]),
        Route("/api/parts/{part_id}", endpoint=answering(part_delete), methods=["DELETE"]),
        Route("/api/parts/{part_id}", endpoint=answering(part_rename), methods=["PATCH"]),
        Route("/api/projects/{project_id}/messages", endpoint=answering(project_message), methods=["POST"]),
        Route("/api/projects/{project_id}/messages/claim", endpoint=answering(project_message_claim), methods=["POST"]),
        Route("/api/projects/{project_id}/attachments", endpoint=answering(project_attachment), methods=["POST"]),
        Route("/api/mesh", endpoint=answering(mesh_describe), methods=["POST"]),
        Route("/api/projects/{project_id}/printer", endpoint=answering(project_printer), methods=["POST"]),
        Route("/api/projects/{project_id}/system", endpoint=answering(project_system)),
        Route("/api/projects/{project_id}/settings", endpoint=answering(project_setting), methods=["POST"]),
        Route("/api/projects/{project_id}/measurements/{name}", endpoint=answering(project_measurement), methods=["PATCH"]),
        Route("/api/printers", endpoint=answering(printers_read)),
        Route("/api/printers", endpoint=answering(printers_add), methods=["POST"]),
        Route("/api/printers/default", endpoint=answering(printers_default), methods=["POST"]),
        Route("/api/printers/{profile}", endpoint=answering(printers_remove), methods=["DELETE"]),
        Route("/api/projects/{project_id}/checkout", endpoint=answering(project_checkout), methods=["POST"]),
        Route("/api/projects/{project_id}/parts/{part_name}/source", endpoint=answering(part_source), methods=["POST"]),
        Route("/api/parts/{part_id}/params", endpoint=answering(part_params), methods=["POST"]),
        Route("/api/parts/{part_id}/apply", endpoint=answering(part_apply), methods=["POST"]),
        Route("/api/parts/{part_id}/export", endpoint=answering(part_export), methods=["POST"]),
        Route("/api/parts/{part_id}/slice", endpoint=answering(part_slice), methods=["POST"]),
        Route("/glb/{project_id}/{part}.glb", endpoint=glb),
        Route("/render/{project_id}/{part}.png", endpoint=render),
        Route("/thumbnail/{project_id}/{part}.png", endpoint=thumbnail),
        WebSocketRoute("/ws", endpoint=ws),
        Route("/", endpoint=index),
        # Last: a Mount matches everything under its prefix, and check_dir is off
        # because the bundle may not be built yet.
        Mount("/assets", app=StaticFiles(directory=WORKBENCH / "assets", check_dir=False)),
    ]
    return manager, routes, events


def next_unbuilt(conn, skip=()):
    """(part id, revision id) of the next part whose current source has never been
    built, projects in the order they arrived and parts by name, or None."""
    skip = list(skip)
    row = conn.execute(
        "SELECT parts.id, parts.current_revision_id FROM parts"
        " JOIN projects ON projects.id = parts.project_id"
        " WHERE parts.kind = 'part' AND parts.current_revision_id IS NOT NULL"
        " AND NOT EXISTS (SELECT 1 FROM build_runs WHERE build_runs.revision_id = parts.current_revision_id)"
        f" AND parts.current_revision_id NOT IN ({','.join('?' * len(skip))})"
        " ORDER BY projects.created_at, parts.name LIMIT 1",
        skip,
    ).fetchone()
    return (row["id"], row["current_revision_id"]) if row else None


def build_unbuilt(wake, stop):
    """Build every part that has never been built, one at a time, so a library an
    import just filled gets its pictures without anyone opening each part, then every
    part a shared file change queued.

    Its own connection, not the serve's lock: a cold kernel takes most of a minute,
    and the page's reads must not wait on it. The warm worker builds one part at a
    time anyway, so a build somebody asked for waits behind one of these at most. A
    failed build still leaves its run row, and `tried` covers a build that raised
    before writing one, so no revision is attempted twice, unless it raised because
    another writer held the database.
    """
    conn = db.connect()
    tried = set()
    try:
        while not stop.is_set():
            wake.wait()
            wake.clear()
            while not stop.is_set():
                # Never-built parts first, then the ones a shared file change left behind.
                next_part = next_unbuilt(conn, tried)
                if next_part:
                    part_id, revision_id = next_part
                    tried.add(revision_id)
                else:
                    part_id = engine_run.take_rebuild()
                    if part_id is None:
                        break
                    if conn.execute("SELECT 1 FROM parts WHERE id = ?", (part_id,)).fetchone() is None:
                        continue
                try:
                    engine_run.run_build(conn, part_id)
                except Exception as exc:
                    print(f"  background build of {part_id} failed: {exc}", flush=True)
                    # An import holding the write lock past the busy timeout is not
                    # the part's fault, so it gets another turn once the lock lifts.
                    if next_part and getattr(exc, "sqlite_errorcode", None) == sqlite3.SQLITE_BUSY:
                        tried.discard(revision_id)
    finally:
        conn.close()


def run(port=None):
    """Serve until interrupted. Raises AlreadyServing when another one holds the lock."""
    import uvicorn
    from starlette.applications import Starlette
    from starlette.middleware import Middleware
    from starlette.middleware.cors import CORSMiddleware
    from starlette.middleware.trustedhost import TrustedHostMiddleware

    home = db.home()
    home.mkdir(parents=True, exist_ok=True)
    fd = _take_lock(home)
    if fd is None:
        raise AlreadyServing(_published_url())
    # Holding the lock proves any published state belongs to a dead predecessor.
    # Remove it before initialization so a racing second serve cannot report it.
    (home / STATE).unlink(missing_ok=True)

    connect = read_connect(home)
    port = _pick_port(port, connect["port"])
    url = f"http://127.0.0.1:{port}"
    token = connect["token"]
    _write_connect(home, token, port)
    conn = db.connect(check_same_thread=False)
    lock = threading.Lock()
    server = mcp_server.make_server(conn, url, lock=lock)
    manager, routes, events = _routes(conn, lock, server, token, os.getpid())
    # Set once for whatever is already unbuilt, then again whenever a part lands.
    wake, stop = threading.Event(), threading.Event()
    wake.set()

    def on_change(kind, row_id, project_id):
        if kind in ("project", "part"):
            wake.set()

    db.listeners.append(on_change)
    threading.Thread(target=build_unbuilt, args=(wake, stop), daemon=True).start()

    @contextlib.asynccontextmanager
    async def lifespan(app):
        # Without manager.run() every request answers "Task group is not initialized".
        async with events(), manager.run():
            yield

    app = Starlette(
        routes=routes,
        lifespan=lifespan,
        middleware=[
            Middleware(
                TrustedHostMiddleware,
                allowed_hosts=["127.0.0.1", "localhost"],
                www_redirect=False,
            ),
            Middleware(
                CORSMiddleware,
                allow_origins=DESKTOP_ORIGINS,
                allow_methods=["*"],
                allow_headers=["*"],
                expose_headers=["Content-Disposition", "X-Nurb-Print-Settings"],
            ),
            Middleware(SameOrigin),
        ],
    )
    # uvicorn restores this handler after its shutdown and re-raises the signal, so
    # SIGTERM has to become an exception here or the finally below never runs.
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    _publish(home, {"port": port, "pid": os.getpid(), "token": token, "url": url})
    print(f"  serving {url}", flush=True)
    try:
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
    except KeyboardInterrupt:
        pass
    finally:
        # A stale file after a crash is fine; leaving one behind on a clean exit is
        # a client waiting 20 seconds on a port nobody is listening to.
        (home / STATE).unlink(missing_ok=True)
        stop.set()
        wake.set()
        conn.close()
        os.close(fd)
        print("  stopped", flush=True)


def main(port=None):
    """Serve, or print the URL of the one already serving this home."""
    try:
        run(port)
    except AlreadyServing as running:
        print(f"  {running.url}", flush=True)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m nurb.serve",
        description="Serve the workbench, the database and the agent tools on one port.",
    )
    parser.add_argument("--port", type=int, help=f"the port to listen on (default: {DEFAULT_PORT})")
    main(parser.parse_args().port)
