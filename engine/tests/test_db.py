"""The store itself: schema, pragmas, and the few row helpers everything else uses."""

import json
import pathlib
import sqlite3
import stat

import pytest

from nurb import db, folder, materialize


def tables(conn):
    return {r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}


def test_connect_creates_the_schema(tmp_path):
    conn = db.connect(tmp_path / "x.db")
    try:
        assert {
            "projects",
            "parts",
            "part_revisions",
            "build_runs",
            "measurements",
            "project_files",
            "messages",
            "pinned_specs",
        } <= tables(conn)
    finally:
        conn.close()


def test_pragmas_are_set(tmp_path):
    conn = db.connect(tmp_path / "x.db")
    try:
        assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    finally:
        conn.close()


def test_migrating_twice_is_a_no_op(tmp_path):
    conn = db.connect(tmp_path / "x.db")
    conn.close()
    conn = db.connect(tmp_path / "x.db")
    try:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == len(db.MIGRATIONS)
        assert "projects" in tables(conn)
    finally:
        conn.close()


def test_a_newer_schema_is_refused(tmp_path):
    conn = db.connect(tmp_path / "x.db")
    conn.close()
    conn = db.connect(tmp_path / "x.db")
    try:
        conn.execute(f"PRAGMA user_version = {len(db.MIGRATIONS) + 1}")
        conn.commit()
        with pytest.raises(RuntimeError, match="newer nurb"):
            db.migrate(conn)
    finally:
        conn.close()


def test_part_names_are_checked(tmp_path):
    conn = db.connect(tmp_path / "x.db")
    try:
        project = db.create_project(conn, "p")
        with pytest.raises(ValueError, match="not a part name"):
            db.create_part(conn, project, "Bad-Name", "x = 1")
        with pytest.raises(ValueError, match="not a part name"):
            db.create_part(conn, project, "_hidden", "x = 1")
        with pytest.raises(ValueError, match="not a part name"):
            db.create_part(conn, project, "shelf\n", "x = 1")
        assert db.create_part(conn, project, "helper", "x = 1", kind="module")
    finally:
        conn.close()


def test_reads_stay_fresh_and_can_be_followed_by_a_write(tmp_path):
    path = tmp_path / "x.db"
    reader = db.connect(path)
    writer = db.connect(path)
    try:
        db.create_project(reader, "first")
        assert reader.execute("SELECT count(*) FROM projects").fetchone()[0] == 1

        db.create_project(writer, "second")
        assert reader.execute("SELECT count(*) FROM projects").fetchone()[0] == 2
        db.create_project(reader, "third")
        assert writer.execute("SELECT count(*) FROM projects").fetchone()[0] == 3
    finally:
        reader.close()
        writer.close()


def test_multi_statement_helpers_remain_atomic(tmp_path):
    conn = db.connect(tmp_path / "x.db")
    try:
        project = db.create_project(conn, "p")
        conn.execute(
            "CREATE TRIGGER refuse_current_revision BEFORE UPDATE OF current_revision_id ON parts"
            " BEGIN SELECT RAISE(ABORT, 'refused'); END"
        )
        with pytest.raises(sqlite3.IntegrityError, match="refused"):
            db.create_part(conn, project, "shelf", "x = 1")
        assert conn.execute("SELECT count(*) FROM parts").fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM part_revisions").fetchone()[0] == 0
    finally:
        conn.close()


def test_default_state_permissions_are_private(monkeypatch, tmp_path):
    monkeypatch.delenv("NURB_HOME", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    root = tmp_path / "config" / "nurb"
    root.mkdir(parents=True, mode=0o777)
    root.chmod(0o777)
    log = root / "serve.log"
    log.write_text("old log")
    log.chmod(0o666)

    conn = db.connect()
    try:
        assert stat.S_IMODE(root.stat().st_mode) == 0o700
        assert stat.S_IMODE(log.stat().st_mode) == 0o600
        for path in (root / "nurb.db", root / "nurb.db-wal", root / "nurb.db-shm"):
            assert path.exists()
            assert stat.S_IMODE(path.stat().st_mode) == 0o600
    finally:
        conn.close()


def test_explicit_home_keeps_shared_permissions(monkeypatch, tmp_path):
    root = tmp_path / "shared"
    root.mkdir(mode=0o770)
    root.chmod(0o770)
    database = root / "nurb.db"
    database.touch()
    database.chmod(0o660)
    monkeypatch.setenv("NURB_HOME", str(root))

    conn = db.connect()
    conn.close()
    assert stat.S_IMODE(root.stat().st_mode) == 0o770
    assert stat.S_IMODE(database.stat().st_mode) == 0o660


def test_measurement_dependencies_accept_quoted_v1_names():
    source = '''width = measured ("shelf depth")
again = measured(name='rail\\'s width')
duplicate = measured(name="shelf depth")
# measured("comment")
example = 'measured("string")'
'''
    assert db.measurement_names(source) == ["shelf depth", "rail's width"]


def test_measurement_dependencies_fail_safely_on_invalid_python():
    assert db.measurement_names('width = measured(name="shelf depth"') == []


def test_a_revision_chains_and_repoints(tmp_path):
    conn = db.connect(tmp_path / "x.db")
    try:
        project = db.create_project(conn, "p")
        part = db.create_part(conn, project, "shelf", "one")
        first = conn.execute("SELECT current_revision_id FROM parts WHERE id = ?", (part,)).fetchone()[0]
        second = db.add_revision(conn, part, "two", note="edited")
        row = conn.execute("SELECT * FROM part_revisions WHERE id = ?", (second,)).fetchone()
        assert row["parent_id"] == first
        assert row["source"] == "two"
        current = conn.execute("SELECT current_revision_id FROM parts WHERE id = ?", (part,)).fetchone()[0]
        assert current == second
    finally:
        conn.close()


def test_value_changed_at_tracks_the_value_only(tmp_path):
    conn = db.connect(tmp_path / "x.db")
    try:
        project = db.create_project(conn, "p")
        db.set_measurement(conn, project, "pitch", 25.16, "calipers")
        first = db.measurements_of(conn, project)[0]["value_changed_at"]

        db.set_measurement(conn, project, "pitch", 25.16, "calipers, twice")
        row = db.measurements_of(conn, project)[0]
        assert row["value_changed_at"] == first
        assert row["how"] == "calipers, twice"

        db.set_measurement(conn, project, "pitch", 25.2, "calipers, twice")
        row = db.measurements_of(conn, project)[0]
        assert row["value_changed_at"] != first
        assert row["value"] == 25.2
    finally:
        conn.close()


def test_a_fresh_database_has_the_attachments_table(tmp_path):
    conn = db.connect(tmp_path / "x.db")
    try:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == len(db.MIGRATIONS)
        assert "attachments" in tables(conn)
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(project_files)")}
        assert "executable" in columns
        runs = {row["name"] for row in conn.execute("PRAGMA table_info(build_runs)")}
        assert "slice" in runs
    finally:
        conn.close()


def test_an_old_database_migrates_forward(tmp_path):
    raw = sqlite3.connect(tmp_path / "old.db")
    raw.executescript(db.MIGRATIONS[0])
    raw.execute(
        "INSERT INTO projects (id, name, created_at) VALUES ('project', 'old', 'now')"
    )
    raw.execute(
        "INSERT INTO project_files (id, project_id, path, content)"
        " VALUES ('launcher', 'project', 'viewer.command', X'23')"
    )
    raw.execute("PRAGMA user_version = 1")
    raw.commit()
    raw.close()

    conn = db.connect(tmp_path / "old.db")
    try:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == len(db.MIGRATIONS)
        assert "attachments" in tables(conn)
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(project_files)")}
        assert "executable" in columns
        runs = {row["name"] for row in conn.execute("PRAGMA table_info(build_runs)")}
        assert "slice" in runs
        launcher = conn.execute(
            "SELECT executable FROM project_files WHERE id = 'launcher'"
        ).fetchone()
        assert launcher["executable"] == 1
        for out in (
            folder.checkout(conn, "project", tmp_path / "checkout"),
            materialize.materialize(conn, "project", into=tmp_path / "scratch"),
        ):
            assert stat.S_IMODE((out / "viewer.command").stat().st_mode) & 0o111
    finally:
        conn.close()


def _one_run(conn):
    """A project, a part and one recorded build, with no engine involved."""
    project = db.create_project(conn, "p")
    part = db.create_part(conn, project, "shelf", "one")
    revision = conn.execute(
        "SELECT current_revision_id FROM parts WHERE id = ?", (part,)
    ).fetchone()[0]
    run_id = db.new_id()
    conn.execute(
        "INSERT INTO build_runs (id, revision_id, status, started_at) VALUES (?, ?, 'ok', ?)",
        (run_id, revision, db.now()),
    )
    return project, part, run_id


def test_a_run_carries_its_slice(tmp_path):
    conn = db.connect(tmp_path / "x.db")
    try:
        project, _, run_id = _one_run(conn)
        heard = []
        db.listeners.append(lambda *event: heard.append(event))
        try:
            db.set_run_result(conn, run_id, "slice", {"seconds": 1200})
        finally:
            db.listeners.pop()
        row = conn.execute("SELECT slice FROM build_runs WHERE id = ?", (run_id,)).fetchone()
        assert json.loads(row["slice"]) == {"seconds": 1200}
        assert heard == [("build", run_id, project)] * 1

        with pytest.raises(ValueError, match="not 'glb'"):
            db.set_run_result(conn, run_id, "glb", {})
        with pytest.raises(ValueError, match="no build run"):
            db.set_run_result(conn, "nosuchrun", "slice", {})
    finally:
        conn.close()


def test_a_fresh_run_carries_none(tmp_path):
    conn = db.connect(tmp_path / "x.db")
    try:
        _, _, run_id = _one_run(conn)
        row = conn.execute("SELECT slice FROM build_runs WHERE id = ?", (run_id,)).fetchone()
        assert row["slice"] is None
    finally:
        conn.close()


def test_the_printer_is_named_once_on_the_project(tmp_path):
    conn = db.connect(tmp_path / "x.db")
    try:
        project = db.create_project(conn, "p")
        heard = []
        db.listeners.append(lambda *event: heard.append(event))
        try:
            db.set_printer(conn, project, 'profile = "bambu_x1c"\n')
        finally:
            db.listeners.pop()
        assert db.get_project(conn, project)["printer_toml"] == 'profile = "bambu_x1c"\n'
        assert heard == [("project", project, project)]
        with pytest.raises(ValueError, match="no project"):
            db.set_printer(conn, "nosuchproject", "")
    finally:
        conn.close()


def test_a_database_that_predates_project_files_migrates_forward(tmp_path):
    # Schema 2 databases from before project_files joined the first migration.
    raw = sqlite3.connect(tmp_path / "older.db")
    raw.executescript(db.MIGRATIONS[0].replace("CREATE TABLE project_files", "CREATE TABLE project_files_gone"))
    raw.executescript(db.MIGRATIONS[1])
    raw.execute("PRAGMA user_version = 2")
    raw.commit()
    raw.close()

    conn = db.connect(tmp_path / "older.db")
    try:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == len(db.MIGRATIONS)
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(project_files)")}
        assert {"path", "content", "executable"} <= columns
    finally:
        conn.close()


def test_a_database_that_predates_folders_migrates_forward(tmp_path):
    """The part is the unit now, so what already exists has to stay a folder."""
    raw = sqlite3.connect(tmp_path / "old.db")
    before = next(i for i, step in enumerate(db.MIGRATIONS) if "ADD COLUMN folder" in step)
    for step in db.MIGRATIONS[:before]:
        raw.executescript(step)
    for project, parts in (("many", ("a", "b")), ("one", ("solo",)), ("empty", ())):
        raw.execute(
            "INSERT INTO projects (id, name, created_at) VALUES (?, ?, 'now')", (project, project)
        )
        for name in parts:
            raw.execute(
                "INSERT INTO parts (id, project_id, name, kind, created_at)"
                " VALUES (?, ?, ?, 'part', 'now')",
                (f"{project}-{name}", project, name),
            )
    raw.execute(f"PRAGMA user_version = {before}")
    raw.commit()
    raw.close()

    conn = db.connect(tmp_path / "old.db")
    try:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == len(db.MIGRATIONS)
        folders = dict(conn.execute("SELECT id, folder FROM projects"))
        assert folders == {"many": 1, "one": 0, "empty": 1}
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(messages)")}
        assert "part" in columns
        # The sync columns that database carried are dropped on the way forward.
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(parts)")}
        assert "visibility" not in columns and "public_url" not in columns
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(projects)")}
        assert "backup" not in columns and "upgrade" not in columns
    finally:
        conn.close()


def test_a_project_is_a_container_until_it_is_promoted(tmp_path):
    conn = db.connect(tmp_path / "x.db")
    try:
        project_id = db.create_project(conn, "drab flange 1")
        assert db.get_project(conn, project_id)["folder"] == 0

        assert db.promote_to_folder(conn, project_id, "  Shelf brackets  ") == "Shelf brackets"
        row = db.get_project(conn, project_id)
        assert (row["folder"], row["name"]) == (1, "Shelf brackets")

        with pytest.raises(ValueError, match="needs a name"):
            db.promote_to_folder(conn, project_id, "   ")
        with pytest.raises(ValueError, match="no project"):
            db.promote_to_folder(conn, "nosuchproject", "Shelf brackets")
    finally:
        conn.close()


def test_deleting_one_part_spares_its_siblings_in_a_hidden_container(tmp_path):
    conn = db.connect(tmp_path / "x.db")
    try:
        project_id = db.create_project(conn, "drab flange 1")
        hook = db.create_part(conn, project_id, "hook", "from nurb import *\n")
        shelf = db.create_part(conn, project_id, "shelf", "from nurb import *\n")
        db.create_part(conn, project_id, "helper", "x = 1", kind="module")

        assert db.delete_part(conn, hook) == (project_id, False)
        names = [r["name"] for r in conn.execute("SELECT name FROM parts WHERE project_id = ?", (project_id,))]
        assert sorted(names) == ["helper", "shelf"]

        # The last part takes the container, and the helper module with it.
        assert db.delete_part(conn, shelf) == (project_id, True)
        assert db.get_project(conn, project_id) is None
    finally:
        conn.close()


def test_moving_a_loose_part_takes_its_whole_chat_and_its_measurements(tmp_path):
    conn = db.connect(tmp_path / "x.db")
    try:
        loose = db.create_project(conn, "drab flange 1")
        target = db.create_project(conn, "target", folder=True)
        part_id = db.create_part(conn, loose, "clip", 'from nurb import *\nspan = measured("span")\n')
        db.set_measurement(conn, loose, "span", 40, "calipers")
        db.set_measurement(conn, loose, "gap", 3, "calipers")
        db.set_measurement(conn, target, "gap", 5, "ruler")
        db.add_message(conn, loose, "user", "make a clip", {})

        db.move_part(conn, part_id, target)

        # The folder's own number wins a clash, because the folder owns its measurements.
        values = {row["name"]: row["value"] for row in db.measurements_of(conn, target)}
        assert values == {"gap": 5.0, "span": 40.0}
        moved = conn.execute(
            "SELECT content, part FROM messages WHERE project_id = ?", (target,)
        ).fetchall()
        assert [(row["content"], row["part"]) for row in moved] == [("make a clip", "clip")]
    finally:
        conn.close()


def test_moving_a_part_out_of_a_folder_takes_the_measurements_it_reads(tmp_path):
    conn = db.connect(tmp_path / "x.db")
    try:
        home = db.create_project(conn, "home", folder=True)
        target = db.create_project(conn, "target", folder=True)
        part_id = db.create_part(conn, home, "clip", 'from nurb import *\nspan = measured("span")\n')
        db.set_measurement(conn, home, "span", 40, "calipers")
        db.set_measurement(conn, home, "wall", 80, "tape")

        db.move_part(conn, part_id, target)

        assert [row["name"] for row in db.measurements_of(conn, target)] == ["span"]
        assert [row["name"] for row in db.measurements_of(conn, home)] == ["span", "wall"]
    finally:
        conn.close()


def test_moving_a_part_takes_its_history_and_its_chat(tmp_path):
    conn = db.connect(tmp_path / "x.db")
    try:
        home = db.create_project(conn, "home", folder=True)
        target = db.create_project(conn, "target", folder=True)
        part_id = db.create_part(conn, home, "hook", "from nurb import *\n")
        other_id = db.create_part(conn, home, "shelf", "from nurb import *\n")
        db.add_revision(conn, part_id, "from nurb import *\n# two\n")
        db.add_message(conn, home, "user", "about the hook", {}, part="hook")
        db.add_message(conn, home, "user", "about the shelf", {}, part="shelf")
        db.add_message(conn, home, "user", "about nothing", {})
        db.add_message(conn, target, "user", "already here", {})

        assert db.move_part(conn, part_id, target) == home

        assert db.get_project(conn, target) is not None
        assert [row["name"] for row in db.parts_of(conn, target)] == ["hook"]
        assert [row["name"] for row in db.parts_of(conn, home)] == ["shelf"]
        revisions = conn.execute(
            "SELECT COUNT(*) FROM part_revisions WHERE part_id = ?", (part_id,)
        ).fetchone()[0]
        assert revisions == 2

        moved = conn.execute(
            "SELECT content, sequence_number FROM messages WHERE project_id = ?"
            " ORDER BY sequence_number",
            (target,),
        ).fetchall()
        assert [row["content"] for row in moved] == ["already here", "about the hook"]
        assert [row["sequence_number"] for row in moved] == [1, 2]
        left = conn.execute(
            "SELECT content FROM messages WHERE project_id = ? ORDER BY sequence_number", (home,)
        ).fetchall()
        assert [row["content"] for row in left] == ["about the shelf", "about nothing"]

        # A later turn in the target still gets a number nothing else holds.
        db.add_message(conn, target, "user", "and now", {}, part="hook")
        numbers = [
            row["sequence_number"]
            for row in conn.execute(
                "SELECT sequence_number FROM messages WHERE project_id = ?", (target,)
            )
        ]
        assert sorted(numbers) == [1, 2, 3]

        db.create_part(conn, target, "shelf", "from nurb import *\n")
        with pytest.raises(ValueError, match="already has a part called shelf"):
            db.move_part(conn, other_id, target)
        assert db.get_project(conn, home) is not None
        with pytest.raises(ValueError, match="no part"):
            db.move_part(conn, "nosuchpart", target)
        with pytest.raises(ValueError, match="no project"):
            db.move_part(conn, other_id, "nosuchproject")
    finally:
        conn.close()


def test_renaming_a_part_carries_its_transcript_and_its_function(tmp_path):
    """The name is the file's name, so the turns about the part follow it, and the
    @part function takes the new name so the source agrees with the part."""
    conn = db.connect(tmp_path / "x.db")
    project_id, _ = folder.import_folder(conn, pathlib.Path(__file__).parents[1] / "examples" / "demo")
    part = conn.execute("SELECT id FROM parts WHERE name = 'bracket'").fetchone()
    db.add_message(conn, project_id, "user", "make it taller", {}, part="bracket")

    assert db.part_name_from("  Shelf Bracket! ") == "shelf_bracket"
    db.rename_part(conn, part["id"], "shelf_bracket")

    row = conn.execute(
        "SELECT parts.name, part_revisions.source, part_revisions.note FROM parts"
        " JOIN part_revisions ON part_revisions.id = parts.current_revision_id WHERE parts.id = ?",
        (part["id"],),
    ).fetchone()
    assert row["name"] == "shelf_bracket"
    assert "def shelf_bracket(" in row["source"] and "def bracket(" not in row["source"]
    assert row["note"] == "Renamed from bracket"
    assert conn.execute("SELECT part FROM messages WHERE project_id = ?", (project_id,)).fetchone()["part"] == "shelf_bracket"

    with pytest.raises(ValueError, match="can't be a part name"):
        db.rename_part(conn, part["id"], "9lives")
    conn.close()


def test_a_rename_keeps_the_title_exactly_as_typed(tmp_path):
    """"Drill Bits" is the same part name as drill_bits, but it is still what the person
    asked to see, so it saves even when the file's name does not move."""
    conn = db.connect(tmp_path / "x.db")
    project_id, _ = folder.import_folder(conn, pathlib.Path(__file__).parents[1] / "examples" / "demo")
    part = conn.execute("SELECT id FROM parts WHERE name = 'bracket'").fetchone()
    db.rename_part(conn, part["id"], db.part_name_from("Bracket"), title="Bracket")
    row = conn.execute("SELECT name, title FROM parts WHERE id = ?", (part["id"],)).fetchone()
    assert (row["name"], row["title"]) == ("bracket", "Bracket")
    db.rename_part(conn, part["id"], db.part_name_from("Shelf Bracket"), title="Shelf Bracket")
    row = conn.execute("SELECT name, title FROM parts WHERE id = ?", (part["id"],)).fetchone()
    assert (row["name"], row["title"]) == ("shelf_bracket", "Shelf Bracket")
    conn.close()
