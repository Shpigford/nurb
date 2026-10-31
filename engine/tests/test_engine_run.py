"""A build that starts from rows and ends in a build_runs row."""

import io
import json
import pathlib
import time

import pytest

from nurb import db, engine_run, folder

NOTCH = pathlib.Path(__file__).parents[1] / "examples" / "notch"

BROKEN = """from nurb import *


@part
def broken(width=10.0):
    return Box(width, width, 0)
"""

REFUSING = """from nurb import *


@part
def picky(width=10.0):
    reject("too small", param="width")
"""

EXITING = """from nurb import *


raise SystemExit("user source exited")
"""

SLEEPING = """from nurb import *


@part
def sleeping():
    import time
    time.sleep(60)
    return Box(10, 10, 10)
"""

CUBE = """from nurb import *


@part
def cube():
    return Box(10, 10, 10)
"""


@pytest.fixture
def conn(tmp_path):
    conn = db.connect(tmp_path / "x.db")
    yield conn
    conn.close()


def part_id(conn, project_id, name):
    return conn.execute(
        "SELECT id FROM parts WHERE project_id = ? AND name = ?", (project_id, name)
    ).fetchone()["id"]


def run_row(conn, run_id):
    return conn.execute("SELECT * FROM build_runs WHERE id = ?", (run_id,)).fetchone()


def test_a_part_builds_and_is_recorded(conn, monkeypatch, tmp_path):
    monkeypatch.setenv("NURB_HOME", str(tmp_path / "home"))
    project_id, _ = folder.import_folder(conn, NOTCH)
    run_id, result = engine_run.run_build(conn, part_id(conn, project_id, "shelf_basic"))

    row = run_row(conn, run_id)
    assert row["status"] == "ok"
    assert row["error"] is None
    assert len(row["glb"]) > 0
    assert "bbox" in json.loads(row["stats"])
    assert isinstance(json.loads(row["findings"]), list)
    assert result["glb_bytes"] == row["glb"]


def test_a_part_that_reads_measurements_builds(conn, monkeypatch, tmp_path):
    """`measured()` walks up from the part file, so it proves the scratch folder is whole."""
    monkeypatch.setenv("NURB_HOME", str(tmp_path / "home"))
    project_id, _ = folder.import_folder(conn, NOTCH)
    run_id, _ = engine_run.run_build(conn, part_id(conn, project_id, "mount_akrobin_rail"))
    assert run_row(conn, run_id)["status"] == "ok"


def test_a_raising_part_reports_the_users_own_frame(conn, monkeypatch, tmp_path):
    monkeypatch.setenv("NURB_HOME", str(tmp_path / "home"))
    project_id = db.create_project(conn, "scratchpad")
    part = db.create_part(conn, project_id, "broken", BROKEN)
    run_id, result = engine_run.run_build(conn, part)

    row = run_row(conn, run_id)
    assert row["status"] == "error"
    assert row["glb"] is None
    first = row["error"].splitlines()[:2]
    assert first[0] == "Traceback (most recent call last):"
    assert first[1].startswith('  File "')
    assert 'parts/broken.py"' in first[1]


def test_a_refused_part_has_no_traceback(conn, monkeypatch, tmp_path):
    monkeypatch.setenv("NURB_HOME", str(tmp_path / "home"))
    project_id = db.create_project(conn, "scratchpad")
    part = db.create_part(conn, project_id, "picky", REFUSING)
    run_id, result = engine_run.run_build(conn, part)

    assert run_row(conn, run_id)["error"] == "too small"
    assert "traceback" not in result
    assert result["params"]


def test_a_module_cannot_be_built(conn, monkeypatch, tmp_path):
    monkeypatch.setenv("NURB_HOME", str(tmp_path / "home"))
    project_id = db.create_project(conn, "scratchpad")
    part = db.create_part(conn, project_id, "system", "VALUE = 1", kind="module")
    with pytest.raises(ValueError, match="module"):
        engine_run.run_build(conn, part)


def test_a_part_name_cannot_be_a_path(tmp_path):
    with pytest.raises(ValueError, match="not a part name"):
        engine_run.build(tmp_path, "../x")


def test_system_exit_is_an_error_and_the_warm_worker_survives(conn, monkeypatch, tmp_path):
    monkeypatch.setenv("NURB_HOME", str(tmp_path / "home"))
    project_id = db.create_project(conn, "scratchpad")
    exiting = db.create_part(conn, project_id, "exiting", EXITING)
    cube = db.create_part(conn, project_id, "cube", CUBE)

    run_id, result = engine_run.run_build(conn, exiting)
    worker_pid = engine_run._WORKER.process.pid
    assert run_row(conn, run_id)["status"] == "error"
    assert result["error"] == "SystemExit: user source exited"

    next_run, next_result = engine_run.run_build(conn, cube)
    assert engine_run._WORKER.process.pid == worker_pid
    assert run_row(conn, next_run)["status"] == "ok"
    assert next_result["glb_bytes"]


def test_a_timed_out_build_is_killed_and_the_next_build_recovers(conn, monkeypatch, tmp_path):
    monkeypatch.setenv("NURB_HOME", str(tmp_path / "home"))
    project_id = db.create_project(conn, "scratchpad")
    sleeping = db.create_part(conn, project_id, "sleeping", SLEEPING)
    cube = db.create_part(conn, project_id, "cube", CUBE)

    started = time.monotonic()
    run_id, result = engine_run.run_build(conn, sleeping, timeout=0.1)
    assert time.monotonic() - started < 2
    assert run_row(conn, run_id)["status"] == "error"
    assert "deadline" in result["error"]

    next_run, next_result = engine_run.run_build(conn, cube)
    assert run_row(conn, next_run)["status"] == "ok"
    assert next_result["glb_bytes"]


def test_materialization_runs_inside_the_timed_worker(conn, monkeypatch, tmp_path):
    monkeypatch.setenv("NURB_HOME", str(tmp_path / "home"))
    project_id = db.create_project(conn, "scratchpad")
    cube = db.create_part(conn, project_id, "cube", CUBE)
    captured = {}

    def timed_worker(request, timeout):
        captured.update(request)
        captured["timeout"] = timeout
        return engine_run._empty_result("build exceeded the deadline", timed_out=True)

    monkeypatch.setattr(engine_run._WORKER, "run", timed_worker)
    run_id, result = engine_run.run_build(conn, cube, timeout=1)

    assert run_row(conn, run_id)["status"] == "error"
    assert "deadline" in result["error"]
    assert captured["scratch_root"] is None
    assert captured["database_path"] == str(tmp_path / "x.db")
    assert captured["project_id"] == project_id
    assert 0 < captured["timeout"] <= 1


def test_exports_carry_the_bytes_of_the_format_they_name(conn, monkeypatch, tmp_path):
    """One build's worth of geometry, three ways out of the worker."""
    import zipfile

    monkeypatch.setenv("NURB_HOME", str(tmp_path / "home"))
    project_id = db.create_project(conn, "scratchpad")
    part = db.create_part(conn, project_id, "cube", CUBE)

    body, filename, note = engine_run.export_part(conn, part, "stl")
    assert filename == "cube.stl"
    assert note is None
    # An STL is either "solid" or an 80-byte header and a triangle count.
    assert body[:5] == b"solid" or len(body) == 84 + 50 * int.from_bytes(body[80:84], "little")

    body, filename, _ = engine_run.export_part(conn, part, "step")
    assert filename == "cube.step"
    assert body[:13] == b"ISO-10303-21;"

    body, filename, note = engine_run.export_part(conn, part, "3mf")
    assert filename == "cube.3mf"
    with zipfile.ZipFile(io.BytesIO(body)) as bundle:
        assert "3D/3dmodel.model" in bundle.namelist()
    # No printer named in this project, so the note says what the file is missing.
    assert note is None or note.startswith("geometry only:") or "wall" in note

    with pytest.raises(ValueError, match="does not export"):
        engine_run.export_part(conn, part, "obj")


def test_an_export_of_a_broken_part_is_a_sentence(conn, monkeypatch, tmp_path):
    monkeypatch.setenv("NURB_HOME", str(tmp_path / "home"))
    project_id = db.create_project(conn, "scratchpad")
    part = db.create_part(conn, project_id, "broken", BROKEN)
    with pytest.raises(ValueError) as refused:
        engine_run.export_part(conn, part, "stl")
    assert "Traceback" not in str(refused.value)


def test_overrides_reach_the_exported_geometry(conn, monkeypatch, tmp_path):
    monkeypatch.setenv("NURB_HOME", str(tmp_path / "home"))
    project_id = db.create_project(conn, "scratchpad")
    part = db.create_part(
        conn, project_id, "slab", "from nurb import *\n\n\n@part\ndef slab(width=10.0):\n    return Box(width, 10, 10)\n"
    )
    plain, _, _ = engine_run.export_part(conn, part, "stl")
    wider, _, _ = engine_run.export_part(conn, part, "stl", overrides={"width": 40.0})
    assert plain != wider
