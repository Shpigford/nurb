"""One build, from rows to a stored result.

The engine only knows files, so a v2 build is: materialize the project, run the same
sequence `nurb dev` runs, and write what came back into build_runs.
"""

import atexit
import hashlib
import json
import multiprocessing
import pathlib
import threading
import time
import traceback
from dataclasses import replace

from . import builder, checks, db, materialize, probe, raster, registry

BUILD_TIMEOUT_SECONDS = 240


def _empty_result(error, *, timed_out=False):
    return {
        "glb_bytes": None,
        "render": None,
        "params": [],
        "findings": [],
        "stats": {},
        "inspect": [],
        "error": error,
        "timed_out": timed_out,
    }


def _user_traceback(exc, path):
    """Trim nurb's own frames so the trace starts in the user's part file."""
    tb = exc.__traceback__
    target = str(pathlib.Path(path).resolve())
    walk = tb
    while walk:
        if walk.tb_frame.f_code.co_filename == target:
            tb = walk
            break
        walk = walk.tb_next
    return "".join(traceback.format_exception(type(exc), exc, tb))


def _root_for(scratch_root, database_path, project_id):
    """The folder the engine builds from, written out fresh when rows are the truth."""
    if database_path is None:
        return pathlib.Path(scratch_root)
    connection = db.connect(database_path)
    try:
        return pathlib.Path(materialize.materialize(connection, project_id))
    finally:
        connection.close()


def _build_in_process(
    scratch_root,
    part_name,
    overrides=None,
    profile=None,
    tolerance=0.1,
    database_path=None,
    project_id=None,
):
    """Build one part out of a materialized folder. Never raises for a bad part.

    Exactly one of `glb_bytes` and `error` comes back set, so a caller never has to
    guess whether there is geometry to show.
    """
    if not str(part_name).isidentifier() or str(part_name).startswith("_"):
        raise ValueError(f"not a part name: {part_name!r}")
    root = _root_for(scratch_root, database_path, project_id)
    path = root / "parts" / f"{part_name}.py"
    result = _empty_result(None)

    try:
        shape, params, ms = builder.build(path, overrides=overrides)
        result["params"] = params
    except registry.Rejected as exc:
        result["error"] = str(exc)
        result["params"] = getattr(exc, "_nurb_params", [])
        return result
    except BaseException as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = _user_traceback(exc, path)
        result["params"] = getattr(exc, "_nurb_params", [])
        return result

    ctx, card_error = _context(root, path, profile, params)

    try:
        glb = builder.to_glb(shape, tolerance, up=ctx.up)
        stats = {
            **builder.stats(shape),
            "ms": round(ms, 1),
            "glb_hash": hashlib.blake2b(glb, digest_size=16).hexdigest(),
        }
        payloads = getattr(shape, "_nurb_payloads", None)
        if payloads:
            stats["payloads"] = [name for _, name in payloads]
        pose = getattr(shape, "_nurb_pose", None)
        if pose is not None:
            stats["pose"] = pose
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = _user_traceback(exc, path)
        return result
    result["glb_bytes"] = glb
    result["stats"] = stats

    try:
        found = checks.run(shape, ctx)
        rows = probe.finding_faces(shape, ctx, found) if found else []
        if any(row is not None for row in rows):
            shape.mesh(tolerance)  # checks.run destroys the GLB's tessellation
        result["findings"] = [
            {
                "rule": f.rule,
                "label": f.label,
                "severity": f.severity,
                "message": f.said,
                "where": list(f.where) if f.where else None,
                "face": [round(v, 2) for v in builder.face_triangles(row["face"])] if row is not None else None,
            }
            for f, row in zip(found, rows)
        ]
        try:
            result["inspect"] = probe.report(part_name, shape, ctx, found, limit=12)
        except Exception as exc:  # a measuring failure must not hide the build
            result["inspect"] = [f"  inspect failed: {type(exc).__name__}: {exc}"]
    except Exception as exc:
        result["findings"] = [
            {
                "rule": "check",
                "label": "the check itself failed",
                "severity": checks.FAIL,
                "message": f"{type(exc).__name__}: {exc}",
                "where": None,
                "face": None,
            }
        ]
    if card_error:
        result["findings"].insert(
            0,
            {
                "rule": "card",
                "label": "the card could not be read",
                "severity": checks.FAIL,
                "message": card_error,
                "where": None,
                "face": None,
            },
        )

    # Keep rendering in the killable worker. The same deadline now bounds geometry,
    # checks and the picture instead of letting rasterization run after the timer.
    try:
        result["render"] = raster.composite(result["glb_bytes"])
    except Exception as exc:
        result["stats"] = {
            **result["stats"],
            "render_error": f"{type(exc).__name__}: {exc}",
        }
    return result


def _context(root, path, profile, params=None):
    """The part's settings, as (ctx, error): the machine, then whatever its card says
    on top, and a card variant's own settings when the build landed exactly on it.

    A bad card is the check pass's finding to report, not a reason to refuse a
    download of geometry that built fine.
    """
    base = checks.Context()
    try:
        base = checks.printer(root, profile)
        # Copy the base because `_apply` mutates its Context as it reads a card and a
        # semantic error can arrive after an earlier setting landed.
        configs = checks.configurations(path, base=replace(base, accepted=dict(base.accepted)))
    except Exception as exc:
        return base, f"{type(exc).__name__}: {exc}"
    # The v1 watcher's rule: a variant is what the sliders show when every parameter
    # equals that variant's override, or its own default where the variant is silent.
    rows = {p["name"]: p for p in params or []}
    for _, overrides, variant_ctx in configs[1:]:
        if overrides and set(overrides) <= set(rows) and all(
            p["value"] == overrides.get(name, p["default"]) for name, p in rows.items()
        ):
            return variant_ctx, None
    return configs[0][2], None


def _solid(scratch_root, part_name, overrides, profile, database_path, project_id):
    """(root, shape, ctx) for the work that needs a shape rather than a picture.

    The shape never crosses the pipe, so anything made of one is made here.
    """
    if not str(part_name).isidentifier() or str(part_name).startswith("_"):
        raise ValueError(f"not a part name: {part_name!r}")
    root = _root_for(scratch_root, database_path, project_id)
    path = root / "parts" / f"{part_name}.py"
    # Always the polished build, whatever the page is showing: draft is a preview
    # economy, and a file somebody downloads is on its way to a slicer.
    shape, params, _ = builder.build(path, overrides=overrides)
    return root, shape, _context(root, path, profile, params)[0]


def _export_in_process(
    scratch_root,
    part_name,
    fmt,
    overrides=None,
    profile=None,
    tolerance=0.1,
    database_path=None,
    project_id=None,
):
    """One downloadable file, as (bytes, filename, note).

    `note` is the sentence about what a 3MF carries besides geometry: what was
    embedded, or what a bare file is missing, because a download that quietly lost its
    print settings teaches nobody.
    """
    import tempfile

    from build123d import Compound, export_step

    from . import slicing

    root, shape, ctx = _solid(
        scratch_root, part_name, overrides, profile, database_path, project_id
    )
    note = None
    # STEP is for CAD and keeps an assembly assembled; the print formats get the parts.
    plate = builder.print_set(shape, ctx.bed) if fmt in ("3mf", "stl") else [shape]
    laid_out = f"{len(plate)} parts laid out to print" if len(plate) > 1 else None
    with tempfile.TemporaryDirectory() as scratch:
        target = pathlib.Path(scratch) / f"{part_name}.{fmt}"
        if fmt == "3mf":
            builder.write_3mf(plate, target)
            kit, why = slicing.kit(root)
            if kit:
                machine, process, filament, exe = kit
                settings, notes = slicing.tuned(plate, ctx)
                try:
                    slicing.write_project(
                        target, target, machine, process, filament, exe, settings=settings
                    )
                    note = ", ".join(notes)
                except slicing.Unavailable as exc:
                    note = f"geometry only: {exc}"
            else:
                if "printer.toml" in why:
                    # The CLI's reason names a file; here the picker is on the page.
                    why = "choose a printer to embed tuned settings"
                note = f"geometry only: {why}"
            note = ", ".join(n for n in (laid_out, note) if n)
        elif fmt == "stl":
            builder.write_stl(plate[0] if len(plate) == 1 else Compound(children=plate), target)
        elif fmt == "step":
            export_step(shape, str(target))
        else:
            raise ValueError(f"nurb does not export {fmt!r}")
        return {"bytes": target.read_bytes(), "filename": target.name, "note": note}


OPS = {"build": _build_in_process, "export": _export_in_process}


def _worker_main(connection):
    """Keep OCCT warm while containing user exits, hangs and kernel crashes."""
    while True:
        try:
            request = connection.recv()
        except EOFError:
            return
        op = request.pop("op", "build")
        try:
            result = OPS[op](**request)
        except BaseException as exc:
            # A ValueError here is already a sentence for whoever asked; everything
            # else is a fault and says what kind it was.
            said = str(exc) if isinstance(exc, ValueError) else f"{type(exc).__name__}: {exc}"
            result = _empty_result(said if op != "build" else f"{type(exc).__name__}: {exc}")
            if op == "build" and request["scratch_root"] is not None:
                path = pathlib.Path(request["scratch_root"]) / "parts" / f"{request['part_name']}.py"
                result["traceback"] = _user_traceback(exc, path)
        try:
            connection.send(result)
        except (BrokenPipeError, EOFError, OSError):
            return


class _EngineWorker:
    def __init__(self):
        self.connection = None
        self.process = None

    def _start(self):
        context = multiprocessing.get_context("spawn")
        parent, child = context.Pipe()
        process = context.Process(target=_worker_main, args=(child,), daemon=True)
        process.start()
        child.close()
        self.connection = parent
        self.process = process

    def _stop(self):
        connection, process = self.connection, self.process
        self.connection = self.process = None
        if connection is not None:
            connection.close()
        if process is None:
            return
        if process.is_alive():
            process.terminate()
            process.join(1)
        if process.is_alive():
            process.kill()
        process.join()

    def run(self, request, timeout):
        if self.process is None or not self.process.is_alive():
            self._stop()
            self._start()
        try:
            self.connection.send(request)
            if not self.connection.poll(timeout):
                self._stop()
                return _empty_result(
                    f"build exceeded the {timeout:g} second deadline; simplify the part and try again",
                    timed_out=True,
                )
            return self.connection.recv()
        except (BrokenPipeError, EOFError, OSError):
            exitcode = self.process.exitcode if self.process is not None else None
            self._stop()
            return _empty_result(f"the CAD engine stopped during the build (exit code {exitcode})")


_WORKER = _EngineWorker()
_WORKER_LOCK = threading.Lock()

# Parts whose own source did not change but whose build is out of date, because a
# shared file they import did. The serve's background builder works through them.
_REBUILD = []
_REBUILD_LOCK = threading.Lock()


def want_rebuild(part_ids, project_id):
    """Queue parts for the background builder, and wake it."""
    with _REBUILD_LOCK:
        for part_id in part_ids:
            if part_id not in _REBUILD:
                _REBUILD.append(part_id)
    if part_ids:
        db.changed("part", part_ids[0], project_id)


def take_rebuild():
    """The next queued part id, or None."""
    with _REBUILD_LOCK:
        return _REBUILD.pop(0) if _REBUILD else None
atexit.register(_WORKER._stop)


def build(
    scratch_root,
    part_name,
    overrides=None,
    profile=None,
    tolerance=0.1,
    timeout=BUILD_TIMEOUT_SECONDS,
):
    """Build in a persistent isolated process, killing it when its deadline expires."""
    if not str(part_name).isidentifier() or str(part_name).startswith("_"):
        raise ValueError(f"not a part name: {part_name!r}")
    request = {
        "scratch_root": str(scratch_root),
        "part_name": part_name,
        "overrides": overrides,
        "profile": profile,
        "tolerance": tolerance,
    }
    with _WORKER_LOCK:
        return _WORKER.run(request, timeout)


def _part_row(conn, part_id):
    row = conn.execute("SELECT * FROM parts WHERE id = ?", (part_id,)).fetchone()
    if row is None:
        raise ValueError(f"no part {part_id!r}")
    if row["kind"] != "part":
        raise ValueError(f"{row['name']} is a module, not a part")
    if row["current_revision_id"] is None:
        raise ValueError(f"{row['name']} has no revision to build")
    return row


def part_identity(conn, part_id):
    """The three values the worker needs to find a part again: (database, project, name).

    Read it under whatever lock guards the store, then hand it to `export_geometry`
    with the lock let go.
    """
    row = _part_row(conn, part_id)
    database_path = str(conn.execute("PRAGMA database_list").fetchone()["file"])
    return database_path, row["project_id"], row["name"]


def export_geometry(
    identity, fmt, overrides=None, profile=None, timeout=BUILD_TIMEOUT_SECONDS, deadline=None
):
    """One part as a downloadable file: (bytes, filename, note).

    Takes a `part_identity` rather than a connection, because the worker opens the
    database itself and the round trip is the slow part: a worker that is not warm yet
    imports the CAD kernel first, which is seconds. A caller holding a lock over the
    store can let go of it before calling this.

    Raises ValueError with a sentence when there is no file to hand over, because the
    caller has a download to answer and nothing to attach.
    """
    if fmt not in ("3mf", "stl", "step"):
        raise ValueError(f"nurb does not export {fmt!r}. Have: 3mf, stl, step.")
    database_path, project_id, part_name = identity
    remaining = (deadline - time.monotonic()) if deadline is not None else timeout
    if remaining <= 0:
        result = _empty_result(
            f"this took longer than the {timeout:g} second deadline", timed_out=True
        )
    else:
        request = {
            "op": "export",
            "scratch_root": None,
            "database_path": database_path,
            "project_id": project_id,
            "part_name": part_name,
            "overrides": overrides,
            "profile": profile,
            "tolerance": 0.1,
            "fmt": fmt,
        }
        with _WORKER_LOCK:
            result = _WORKER.run(request, remaining)
    if result.get("error") or not result.get("bytes"):
        raise ValueError(result.get("error") or "the export came back empty")
    return result["bytes"], result["filename"], result["note"]


def export_part(conn, part_id, fmt, overrides=None, profile=None, timeout=BUILD_TIMEOUT_SECONDS, deadline=None):
    """One part as a downloadable file, read and exported in one call."""
    return export_geometry(
        part_identity(conn, part_id),
        fmt,
        overrides=overrides,
        profile=profile,
        timeout=timeout,
        deadline=deadline,
    )


def _build_project(database_path, project_id, part_name, overrides, profile, timeout):
    request = {
        "op": "build",
        "scratch_root": None,
        "database_path": str(database_path),
        "project_id": project_id,
        "part_name": part_name,
        "overrides": overrides,
        "profile": profile,
        "tolerance": 0.1,
    }
    with _WORKER_LOCK:
        return _WORKER.run(request, timeout)


def run_build(
    conn,
    part_id,
    overrides=None,
    profile=None,
    timeout=BUILD_TIMEOUT_SECONDS,
    deadline=None,
):
    """Build a part and record the attempt. Returns (run_id, result).

    Two callers reach for the same revision whenever a request writes one: the request
    builds it, and the background builder wakes on that same change event and finds a
    current revision with no run. Both used to build, so "Building" lasted twice as
    long and the second result was thrown away (#334). The first caller through builds;
    the others wait on its gate and read its run back.
    """
    if deadline is None:
        deadline = time.monotonic() + timeout
    row = _part_row(conn, part_id)
    revision_id = row["current_revision_id"]
    with _INFLIGHT_LOCK:
        gate = _INFLIGHT.setdefault(revision_id, _Inflight())
        gate.waiters += 1
    try:
        with gate.lock:
            if gate.run_id is not None and gate.overrides == (overrides or {}):
                done = conn.execute(
                    "SELECT * FROM build_runs WHERE id = ?", (gate.run_id,)
                ).fetchone()
                if done is not None:
                    return gate.run_id, _result_of(done)
            run_id, result = _build_and_record(conn, row, overrides, profile, timeout, deadline)
            gate.run_id, gate.overrides = run_id, overrides or {}
            return run_id, result
    finally:
        with _INFLIGHT_LOCK:
            gate.waiters -= 1
            if gate.waiters == 0:
                _INFLIGHT.pop(revision_id, None)


class _Inflight:
    """One revision's build, and the run it left behind for whoever waited."""

    def __init__(self):
        self.lock = threading.Lock()
        self.waiters = 0
        self.run_id = None
        self.overrides = None


_INFLIGHT = {}
_INFLIGHT_LOCK = threading.Lock()


def _result_of(row):
    """A stored run read back in the shape a fresh build returns."""
    return {
        "glb_bytes": row["glb"],
        "render": row["render"],
        "params": json.loads(row["params"]),
        "findings": json.loads(row["findings"]),
        "stats": json.loads(row["stats"]),
        "inspect": json.loads(row["inspect_report"]),
        "error": row["error"],
        "timed_out": False,
    }


def _build_and_record(conn, row, overrides, profile, timeout, deadline):
    started = db.now()
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        result = _empty_result(
            f"build exceeded the {timeout:g} second deadline; simplify the part and try again",
            timed_out=True,
        )
    else:
        database_path = conn.execute("PRAGMA database_list").fetchone()["file"]
        result = _build_project(
            database_path,
            row["project_id"],
            row["name"],
            overrides,
            profile,
            remaining,
        )

    run_id = db.new_id()
    with conn:
        conn.execute(
            "INSERT INTO build_runs (id, revision_id, status, error, findings, inspect_report, stats,"
            " params, overrides, glb, render, started_at, finished_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                run_id,
                row["current_revision_id"],
                "ok" if result["glb_bytes"] is not None else "error",
                result.get("traceback") or result["error"],
                json.dumps(result["findings"]),
                json.dumps(result["inspect"]),
                json.dumps(result["stats"]),
                json.dumps(result["params"]),
                json.dumps(overrides or {}),
                result["glb_bytes"],
                result["render"],
                started,
                db.now(),
            ),
        )
    db.changed("build", run_id, row["project_id"])
    return run_id, result
