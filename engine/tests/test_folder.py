"""A folder goes in and the same folder comes back out.

The round trip is the whole claim of the v2 store: nothing about a v1 project is lost
by keeping it in rows, so the engine can keep reading files it has always read.
"""

import pathlib
import stat
import tomllib

import pytest

from nurb import db, engine_run, folder, materialize
from nurb.measurements import MeasurementError, measured

NOTCH = pathlib.Path(__file__).parents[1] / "examples" / "notch"
DEMO = pathlib.Path(__file__).parents[1] / "examples" / "demo"


@pytest.fixture
def conn(tmp_path):
    conn = db.connect(tmp_path / "x.db")
    yield conn
    conn.close()


def files(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def test_notch_round_trips(conn, tmp_path):
    project_id, count = folder.import_folder(conn, NOTCH)
    assert count == 13

    out = folder.checkout(conn, project_id, tmp_path / "out")
    assert files(out / "parts") == files(NOTCH / "parts")
    assert (out / "system.py").read_bytes() == (NOTCH / "system.py").read_bytes()
    assert (out / "calibrate.py").read_bytes() == (NOTCH / "calibrate.py").read_bytes()

    written = tomllib.loads((out / "measurements.toml").read_text())
    source = tomllib.loads((NOTCH / "measurements.toml").read_text())
    assert written == source


def test_demo_round_trips(conn, tmp_path):
    project_id, count = folder.import_folder(conn, DEMO)
    assert count == 1

    out = folder.checkout(conn, project_id, tmp_path / "out")
    assert not (out / "measurements.toml").exists()
    assert (out / "parts" / "bracket.md").read_bytes() == (DEMO / "parts" / "bracket.md").read_bytes()
    assert (out / "parts" / "bracket.py").read_bytes() == (DEMO / "parts" / "bracket.py").read_bytes()


def test_parts_module_round_trips_and_builds_from_materialized_location(conn, tmp_path):
    project = tmp_path / "v1"
    parts = project / "parts"
    parts.mkdir(parents=True)
    root_module_source = b"VALUE = 2.0\n"
    parts_module_source = b"VALUE = 12.0\n"
    part_source = (
        b"from nurb import *\n\n"
        b"from _shared import VALUE as ROOT_VALUE\n"
        b"from parts._shared import VALUE as PARTS_VALUE\n\n"
        b"@part\n"
        b"def shelf():\n"
        b"    return Box(ROOT_VALUE + PARTS_VALUE, 8, 4)\n"
    )
    (project / "_shared.py").write_bytes(root_module_source)
    (parts / "_shared.py").write_bytes(parts_module_source)
    (parts / "shelf.py").write_bytes(part_source)

    project_id, count = folder.import_folder(conn, project)
    assert count == 1
    rows = conn.execute(
        "SELECT kind FROM parts WHERE project_id = ? AND name = '_shared'", (project_id,)
    ).fetchall()
    assert {row["kind"] for row in rows} == {"module", db.PARTS_MODULE_KIND}

    scratch = materialize.materialize(conn, project_id, into=tmp_path / "scratch")
    assert (scratch / "_shared.py").read_bytes() == root_module_source
    assert (scratch / "parts" / "_shared.py").read_bytes() == parts_module_source
    result = engine_run.build(scratch, "shelf")
    assert result["error"] is None
    assert result["stats"]["bbox"] == [14.0, 8.0, 4.0]

    out = folder.checkout(conn, project_id, tmp_path / "out")
    assert (out / "_shared.py").read_bytes() == root_module_source
    assert (out / "parts" / "_shared.py").read_bytes() == parts_module_source
    assert (out / "parts" / "shelf.py").read_bytes() == part_source


def test_assets_and_nested_packages_round_trip_and_build(conn, tmp_path):
    project = tmp_path / "v1"
    parts = project / "parts"
    helpers = project / "helpers"
    parts.mkdir(parents=True)
    helpers.mkdir()
    (helpers / "__init__.py").write_text("from .sizes import WIDTH\n")
    (helpers / "sizes.py").write_text("WIDTH = 13\n")
    asset = b"solid reference\nendsolid reference\n"
    (project / "scans").mkdir()
    (project / "scans" / "reference.stl").write_bytes(asset)
    (parts / "shelf.py").write_text(
        "from pathlib import Path\nfrom nurb import *\nfrom helpers import WIDTH\n\n@part\ndef shelf():\n    assert (Path(__file__).parents[1] / 'scans' / 'reference.stl').read_bytes()\n    return Box(WIDTH, 8, 4)\n"
    )
    (parts / "notes.md").write_text("Project-owned notes.\n")
    (project / "build").mkdir()
    (project / "build" / "stale.stl").write_bytes(b"generated")
    (project / "__pycache__").mkdir()
    (project / "__pycache__" / "helper.pyc").write_bytes(b"cache")

    project_id, _ = folder.import_folder(conn, project)
    scratch = materialize.materialize(conn, project_id, into=tmp_path / "scratch")
    assert engine_run.build(scratch, "shelf")["stats"]["bbox"] == [13.0, 8.0, 4.0]
    assert (scratch / "scans" / "reference.stl").read_bytes() == asset

    out = folder.checkout(conn, project_id, tmp_path / "out")
    assert (out / "helpers" / "sizes.py").read_text() == "WIDTH = 13\n"
    assert (out / "scans" / "reference.stl").read_bytes() == asset
    assert (out / "parts" / "notes.md").read_text() == "Project-owned notes.\n"
    assert not (out / "build").exists()
    assert not (out / "__pycache__").exists()


def test_project_file_paths_cannot_escape_materialization(conn, tmp_path):
    project_id, _ = folder.import_folder(conn, DEMO)
    conn.execute(
        "INSERT INTO project_files (id, project_id, path, content) VALUES (?, ?, ?, ?)",
        (db.new_id(), project_id, "../escape", b"bad"),
    )

    with pytest.raises(ValueError, match="not a project file path"):
        materialize.materialize(conn, project_id, into=tmp_path / "scratch")
    assert not (tmp_path / "escape").exists()


def test_checkout_refuses_a_used_directory(conn, tmp_path):
    project_id, _ = folder.import_folder(conn, DEMO)
    (tmp_path / "out").mkdir()
    (tmp_path / "out" / "something.txt").write_text("mine")
    with pytest.raises(ValueError, match="not empty"):
        folder.checkout(conn, project_id, tmp_path / "out")


def test_importing_twice_makes_two_projects(conn):
    first, _ = folder.import_folder(conn, NOTCH)
    second, _ = folder.import_folder(conn, NOTCH)
    assert first != second
    assert conn.execute("SELECT count(*) FROM projects").fetchone()[0] == 2


def test_materialize_writes_the_build_folder(conn, tmp_path):
    project_id, _ = folder.import_folder(conn, NOTCH)
    root = materialize.materialize(conn, project_id, into=tmp_path / "scratch")

    assert (root / "parts" / "shelf_basic.py").is_file()
    assert (root / "system.py").is_file()
    assert not (root / "parts" / "system.py").exists()
    assert tomllib.loads((root / "measurements.toml").read_text()) == tomllib.loads(
        (NOTCH / "measurements.toml").read_text()
    )


def test_materialize_is_a_snapshot(conn, tmp_path):
    project_id, _ = folder.import_folder(conn, NOTCH)
    root = materialize.materialize(conn, project_id, into=tmp_path / "scratch")
    assert (root / "parts" / "shelf_basic.py").is_file()

    with conn:
        conn.execute(
            "DELETE FROM parts WHERE project_id = ? AND name = 'shelf_basic'", (project_id,)
        )
    materialize.materialize(conn, project_id, into=tmp_path / "scratch")
    assert not (root / "parts" / "shelf_basic.py").exists()
    assert not (root / "parts" / "shelf_basic.md").exists()
    assert (root / "parts" / "shelf_gridfinity.py").is_file()


def test_measurements_toml_is_written_back_readable():
    rows = [
        {"name": "pitch", "value": 25.16, "how": 'off the "wall" run,\nmeasured twice', "provisional": 0},
        {"name": "guess", "value": 3.0, "how": "eyeballed", "provisional": 1},
    ]
    text = materialize.measurements_toml(rows)
    parsed = tomllib.loads(text)
    assert parsed["pitch"]["value"] == 25.16
    assert parsed["pitch"]["how"] == 'off the "wall" run,\nmeasured twice'
    assert "provisional" not in parsed["pitch"]
    assert parsed["guess"]["provisional"] is True
    assert text.endswith("\n") and not text.endswith("\n\n")
    assert text.startswith("[pitch]\n"), "a bare key must not come back quoted"


def test_quoted_measurement_name_round_trips_and_builds(conn, monkeypatch, tmp_path):
    project = tmp_path / "v1"
    (project / "parts").mkdir(parents=True)
    (project / "parts" / "shelf.py").write_text(
        'from nurb import *\n\n@part\ndef shelf():\n    return Box(measured("shelf depth"), 10, 10)\n'
    )
    (project / "measurements.toml").write_text(
        '["shelf depth"]\nvalue = 25.0\nunit = "mm"\nhow = "tape"\n'
    )
    monkeypatch.setenv("NURB_HOME", str(tmp_path / "home"))

    project_id, _ = folder.import_folder(conn, project)
    out = folder.checkout(conn, project_id, tmp_path / "out")
    assert tomllib.loads((out / "measurements.toml").read_text())["shelf depth"]["value"] == 25.0

    part_id = conn.execute(
        "SELECT id FROM parts WHERE project_id = ? AND name = 'shelf'", (project_id,)
    ).fetchone()["id"]
    _, result = engine_run.run_build(conn, part_id)
    assert result["error"] is None
    assert result["glb_bytes"]


def test_non_mm_measurement_keeps_its_unit_and_refuses_geometry(conn, monkeypatch, tmp_path):
    project = tmp_path / "v1"
    (project / "parts").mkdir(parents=True)
    (project / "parts" / "shelf.py").write_text(
        'from nurb import *\n\n@part\ndef shelf():\n    return Box(measured("width"), 10, 10)\n'
    )
    (project / "measurements.toml").write_text(
        '[width]\nvalue = 2.0\nunit = "in"\nhow = "ruler"\n'
    )
    monkeypatch.setenv("NURB_HOME", str(tmp_path / "home"))

    project_id, _ = folder.import_folder(conn, project)
    assert db.measurements_of(conn, project_id)[0]["unit"] == "in"
    scratch = materialize.materialize(conn, project_id, into=tmp_path / "scratch")
    assert tomllib.loads((scratch / "measurements.toml").read_text())["width"]["unit"] == "in"
    with pytest.raises(MeasurementError, match="works in mm"):
        measured("width", start=scratch / "parts")
    part_id = conn.execute(
        "SELECT id FROM parts WHERE project_id = ? AND name = 'shelf'", (project_id,)
    ).fetchone()["id"]
    _, result = engine_run.run_build(conn, part_id)
    assert result["glb_bytes"] is None
    assert "works in mm" in result["error"]
    out = folder.checkout(conn, project_id, tmp_path / "out")
    assert tomllib.loads((out / "measurements.toml").read_text())["width"]["unit"] == "in"


def test_no_measurements_is_an_empty_file():
    assert materialize.measurements_toml([]) == ""


def test_a_part_file_that_is_not_snake_case_is_refused(conn, tmp_path):
    project = tmp_path / "v1"
    (project / "parts").mkdir(parents=True)
    (project / "parts" / "Bracket.py").write_text("from nurb import *\n")

    with pytest.raises(ValueError, match="Bracket.py: a part name is lowercase snake_case"):
        folder.import_folder(conn, project)
    assert conn.execute("SELECT count(*) FROM projects").fetchone()[0] == 0


def test_root_python_file_with_non_identifier_name_round_trips_as_project_file(conn, tmp_path):
    project = tmp_path / "v1"
    (project / "parts").mkdir(parents=True)
    (project / "parts" / "shelf.py").write_text("from nurb import *\n")
    script = project / "build-part.py"
    script.write_text("print('build')\n")

    project_id, _ = folder.import_folder(conn, project)

    assert [row["name"] for row in db.parts_of(conn, project_id)] == ["shelf"]
    assert [(row["path"], row["content"]) for row in db.project_files_of(conn, project_id)] == [
        ("build-part.py", b"print('build')\n")
    ]
    out = folder.checkout(conn, project_id, tmp_path / "out")
    assert (out / "build-part.py").read_bytes() == script.read_bytes()


@pytest.mark.parametrize(
    ("relative", "target"),
    [
        ("parts", "directory"),
        ("parts/shelf.py", "file"),
        ("parts/shelf.md", "file"),
        ("shared.py", "file"),
        ("parts/_shared.py", "file"),
        ("printer.toml", "file"),
        ("measurements.toml", "file"),
    ],
)
def test_import_refuses_symlinked_modeled_inputs(conn, tmp_path, relative, target):
    project = tmp_path / "v1"
    outside = tmp_path / "outside"
    real_parts = project / "parts"
    real_parts.mkdir(parents=True)
    outside.mkdir()
    (real_parts / "shelf.py").write_text("from nurb import *\n")

    path = project / relative
    if path.exists():
        if path.is_dir():
            path.rename(outside / "parts")
        else:
            path.unlink()
    if target == "directory":
        path.symlink_to(outside / "parts", target_is_directory=True)
    else:
        source = outside / path.name
        source.write_text("outside\n")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(source)

    with pytest.raises(ValueError, match="symlinks are not allowed"):
        folder.import_folder(conn, project)
    assert conn.execute("SELECT count(*) FROM projects").fetchone()[0] == 0


def test_keyboard_interrupt_rolls_back_the_whole_import(conn, monkeypatch, tmp_path):
    project = tmp_path / "v1"
    (project / "parts").mkdir(parents=True)
    (project / "parts" / "first.py").write_text("from nurb import *\n")
    (project / "parts" / "second.py").write_text("from nurb import *\n")
    original = db.create_part
    calls = 0

    def interrupt_second(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise KeyboardInterrupt
        return original(*args, **kwargs)

    monkeypatch.setattr(db, "create_part", interrupt_second)
    with pytest.raises(KeyboardInterrupt):
        folder.import_folder(conn, project)
    for table in ("projects", "parts", "part_revisions"):
        assert conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 0


def test_default_materialized_scratch_is_private(conn, monkeypatch, tmp_path):
    monkeypatch.delenv("NURB_HOME", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    project_id, _ = folder.import_folder(conn, DEMO)

    root = materialize.materialize(conn, project_id)
    assert stat.S_IMODE(root.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(root.stat().st_mode) == 0o700
    assert stat.S_IMODE((root / "parts").stat().st_mode) == 0o700
    for path in root.rglob("*"):
        if path.is_file():
            assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_reference_images_become_attachments_and_come_back(conn, tmp_path):
    root = tmp_path / "proj"
    (root / "parts").mkdir(parents=True)
    (root / "parts" / "x.py").write_text(
        "from nurb import *\n\n\n@part\ndef x(w=10.0):\n    return Box(w, w, w)\n",
        encoding="utf-8",
    )
    (root / "references").mkdir()
    png = b"\x89PNG\r\n\x1a\n" + b"not really a png"
    jpg = b"\xff\xd8\xff" + b"not really a jpeg"
    (root / "references" / "a.png").write_bytes(png)
    (root / "references" / "b.jpg").write_bytes(jpg)

    project_id, _ = folder.import_folder(conn, root)
    rows = db.attachments_of(conn, project_id)
    assert [(row["name"], row["mime"], row["bytes"]) for row in rows] == [
        ("a.png", "image/png", png),
        ("b.jpg", "image/jpeg", jpg),
    ]
    assert not [
        row for row in db.project_files_of(conn, project_id) if row["path"].startswith("references/")
    ]

    out = folder.checkout(conn, project_id, tmp_path / "out")
    assert (out / "references" / "a.png").read_bytes() == png
    assert (out / "references" / "b.jpg").read_bytes() == jpg


def test_reference_images_in_sibling_folders_keep_their_paths(conn, tmp_path):
    root = tmp_path / "proj"
    (root / "parts").mkdir(parents=True)
    (root / "parts" / "x.py").write_text(
        "from nurb import *\n\n\n@part\ndef x(w=10.0):\n    return Box(w, w, w)\n",
        encoding="utf-8",
    )
    for side in ("left", "right"):
        (root / "references" / side).mkdir(parents=True)
        (root / "references" / side / "x.png").write_bytes(side.encode())

    project_id, _ = folder.import_folder(conn, root)
    rows = db.attachments_of(conn, project_id)
    assert [(row["name"], row["bytes"]) for row in rows] == [
        ("left/x.png", b"left"),
        ("right/x.png", b"right"),
    ]

    out = folder.checkout(conn, project_id, tmp_path / "out")
    assert (out / "references" / "left" / "x.png").read_bytes() == b"left"
    assert (out / "references" / "right" / "x.png").read_bytes() == b"right"


def test_checkout_refuses_an_attachment_name_that_escapes(conn, tmp_path):
    root = tmp_path / "proj"
    (root / "parts").mkdir(parents=True)
    (root / "parts" / "x.py").write_text("from nurb import *\n", encoding="utf-8")
    project_id, _ = folder.import_folder(conn, root)
    db.add_attachment(conn, project_id, "../escape.png", "image/png", b"x")
    with pytest.raises(ValueError, match="not an attachment name"):
        folder.checkout(conn, project_id, tmp_path / "out")
    assert not (tmp_path / "escape.png").exists()


def test_project_file_executable_mode_survives_checkout_and_materialize(conn, tmp_path):
    root = tmp_path / "proj"
    (root / "parts").mkdir(parents=True)
    (root / "parts" / "x.py").write_text("from nurb import *\n", encoding="utf-8")
    script = root / "viewer.command"
    script.write_text("#!/bin/sh\n", encoding="utf-8")
    script.chmod(0o755)
    plain = root / "notes.txt"
    plain.write_text("notes\n", encoding="utf-8")
    plain.chmod(0o644)

    project_id, _ = folder.import_folder(conn, root)
    rows = {row["path"]: row for row in db.project_files_of(conn, project_id)}
    assert rows["viewer.command"]["executable"] == 1
    assert rows["notes.txt"]["executable"] == 0

    for out in (
        folder.checkout(conn, project_id, tmp_path / "out"),
        materialize.materialize(conn, project_id, into=tmp_path / "scratch"),
    ):
        assert stat.S_IMODE((out / "viewer.command").stat().st_mode) & 0o111
        assert not stat.S_IMODE((out / "notes.txt").stat().st_mode) & 0o111
