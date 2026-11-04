"""The v2 store: one SQLite file holding projects, parts, revisions and builds.

A v1 project is a folder; a v2 project is rows. The folder is still the only thing the
engine can build, so it is regenerated on demand (see materialize.py) and the database
stays the source of truth.
"""

import ast
import contextlib
import datetime
import json
import os
import pathlib
import re
import sqlite3
import threading
import uuid

# What a part may be called. It becomes a filename and a Python module name, so the
# rule is the intersection of both, and it is re-checked wherever a name meets a path.
PART_NAME = re.compile(r"^[a-z][a-z0-9_]*\Z")
PARTS_MODULE_KIND = "parts_module"

MIGRATIONS = [
    """
    CREATE TABLE projects (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        printer_toml TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE parts (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        kind TEXT NOT NULL DEFAULT 'part',
        -- Not a foreign key: parts and part_revisions point at each other, and a
        -- circular reference cannot be satisfied by either insert on its own.
        current_revision_id TEXT,
        created_at TEXT NOT NULL,
        UNIQUE (project_id, name, kind)
    );

    CREATE TABLE part_revisions (
        id TEXT PRIMARY KEY,
        part_id TEXT NOT NULL REFERENCES parts(id) ON DELETE CASCADE,
        source TEXT NOT NULL,
        card_md TEXT,
        params TEXT NOT NULL DEFAULT '[]',
        parent_id TEXT,
        note TEXT,
        created_at TEXT NOT NULL
    );
    CREATE INDEX part_revisions_part ON part_revisions (part_id);

    CREATE TABLE build_runs (
        id TEXT PRIMARY KEY,
        revision_id TEXT NOT NULL REFERENCES part_revisions(id) ON DELETE CASCADE,
        status TEXT NOT NULL,
        error TEXT,
        findings TEXT NOT NULL DEFAULT '[]',
        inspect_report TEXT NOT NULL DEFAULT '[]',
        stats TEXT NOT NULL DEFAULT '{}',
        params TEXT NOT NULL DEFAULT '[]',
        overrides TEXT NOT NULL DEFAULT '{}',
        glb BLOB,
        render BLOB,
        started_at TEXT NOT NULL,
        finished_at TEXT
    );
    CREATE INDEX build_runs_revision ON build_runs (revision_id, started_at);

    CREATE TABLE measurements (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        value REAL NOT NULL,
        unit TEXT NOT NULL DEFAULT 'mm',
        how TEXT NOT NULL,
        provisional INTEGER NOT NULL DEFAULT 0,
        value_changed_at TEXT NOT NULL,
        UNIQUE (project_id, name)
    );

    CREATE TABLE project_files (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
        path TEXT NOT NULL,
        content BLOB NOT NULL,
        UNIQUE (project_id, path)
    );

    CREATE TABLE messages (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
        role TEXT NOT NULL,
        content TEXT,
        payload TEXT NOT NULL DEFAULT '{}',
        sequence_number INTEGER NOT NULL,
        created_at TEXT NOT NULL
    );
    CREATE INDEX messages_project ON messages (project_id, sequence_number);

    CREATE TABLE pinned_specs (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
        spec TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE attachments (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        mime TEXT NOT NULL,
        bytes BLOB NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE (project_id, name)
    );
    CREATE INDEX attachments_project ON attachments (project_id);
    """,
    """
    -- project_files was added to the first migration after databases already existed
    -- at schema 2, and a migration that has run never runs again; those databases
    -- reach this one without the table.
    CREATE TABLE IF NOT EXISTS project_files (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
        path TEXT NOT NULL,
        content BLOB NOT NULL,
        UNIQUE (project_id, path)
    );
    ALTER TABLE project_files ADD COLUMN executable INTEGER NOT NULL DEFAULT 0;
    UPDATE project_files SET executable = 1 WHERE path = 'viewer.command';
    """,
    """
    -- stress is unused since the stress tool was removed. A migration that has run
    -- never runs again, so the column stays where user databases already have it.
    ALTER TABLE build_runs ADD COLUMN stress TEXT;
    ALTER TABLE build_runs ADD COLUMN slice TEXT;
    """,
    """
    -- Sync with a hosted account, since removed; migration 8 drops these columns.
    ALTER TABLE projects ADD COLUMN sync_id TEXT;
    ALTER TABLE projects ADD COLUMN hosted_id TEXT;
    ALTER TABLE projects ADD COLUMN account_id TEXT;
    ALTER TABLE projects ADD COLUMN backup INTEGER NOT NULL DEFAULT 0;
    ALTER TABLE projects ADD COLUMN synced_at TEXT;
    ALTER TABLE projects ADD COLUMN sync_digest TEXT;
    ALTER TABLE projects ADD COLUMN pull_cursor TEXT;
    ALTER TABLE projects ADD COLUMN conflict TEXT;

    ALTER TABLE parts ADD COLUMN visibility TEXT NOT NULL DEFAULT 'private';
    ALTER TABLE parts ADD COLUMN hosted_revision_id TEXT;
    ALTER TABLE parts ADD COLUMN synced_revision_id TEXT;
    ALTER TABLE parts ADD COLUMN public_url TEXT;
    """,
    """
    -- Sync again, dropped in migration 8.
    ALTER TABLE projects ADD COLUMN upgrade TEXT;
    """,
    """
    -- The part is the unit. A project with folder = 0 is an invisible container for
    -- exactly one part, so only a real folder is something the user sees and names.
    ALTER TABLE projects ADD COLUMN folder INTEGER NOT NULL DEFAULT 0;
    -- Which part a turn of the transcript was about, so a part carries its own chat.
    ALTER TABLE messages ADD COLUMN part TEXT;

    -- Everything that already exists was made when a project was the unit: anything
    -- but a single part is a folder, or it would vanish from the rail on upgrade.
    UPDATE projects SET folder = 1
     WHERE (SELECT COUNT(*) FROM parts WHERE project_id = projects.id AND kind = 'part') <> 1;
    """,
    """
    -- Sync with a hosted account is gone, so the columns migrations 5 and 6 added for
    -- it go too. Those migrations stay, because a migration that has run never runs
    -- again and a fresh database has to reach the same schema number.
    ALTER TABLE projects DROP COLUMN sync_id;
    ALTER TABLE projects DROP COLUMN hosted_id;
    ALTER TABLE projects DROP COLUMN account_id;
    ALTER TABLE projects DROP COLUMN backup;
    ALTER TABLE projects DROP COLUMN synced_at;
    ALTER TABLE projects DROP COLUMN sync_digest;
    ALTER TABLE projects DROP COLUMN pull_cursor;
    ALTER TABLE projects DROP COLUMN conflict;
    ALTER TABLE projects DROP COLUMN upgrade;
    ALTER TABLE parts DROP COLUMN visibility;
    ALTER TABLE parts DROP COLUMN hosted_revision_id;
    ALTER TABLE parts DROP COLUMN synced_revision_id;
    ALTER TABLE parts DROP COLUMN public_url;
    """,
    """
    -- What a person calls the part, exactly as typed ("Drill Bits"). The name stays the
    -- part's file name, lowercase with underscores, which a title cannot be.
    ALTER TABLE parts ADD COLUMN title TEXT;
    """,
    """
    -- What a person calls a spot on the part ("lip", "hook"), so they and the agent can
    -- name the same place. A point and its surface normal in the part's own mm, never a
    -- B-rep face: face ids do not survive an edit, and a point can be checked against
    -- whatever the next build made.
    CREATE TABLE labels (
        id TEXT PRIMARY KEY,
        part_id TEXT NOT NULL REFERENCES parts(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        x REAL NOT NULL, y REAL NOT NULL, z REAL NOT NULL,
        nx REAL NOT NULL, ny REAL NOT NULL, nz REAL NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE (part_id, name)
    );
    """,
]

# What a run can carry besides its geometry: it is measured from one build, so it
# hangs off that run and dies with it rather than outliving the shape it describes.
RUN_RESULTS = ("slice",)


def home():
    """Where nurb keeps its own state, next to the machine's config.toml."""
    override = os.environ.get("NURB_HOME")
    if override:
        return pathlib.Path(override)
    from . import checks

    root = checks.global_file().parent
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    root.chmod(0o700)
    _harden_existing_state(root)
    return root


def _harden_existing_state(root):
    """Repair older default state created under the process umask.

    NURB_HOME is deliberately excluded by `home`: an explicit override may be a shared location whose group permissions belong to its owner.
    """
    for candidate in root.glob("nurb.db*"):
        if candidate.is_file() and not candidate.is_symlink():
            candidate.chmod(0o600)
    for name in ("serve.json", "serve.json.tmp", "serve.lock", "serve.log"):
        candidate = root / name
        if candidate.is_file() and not candidate.is_symlink():
            candidate.chmod(0o600)
    scratch = root / "scratch"
    if scratch.is_dir() and not scratch.is_symlink():
        scratch.chmod(0o700)
        for candidate in scratch.rglob("*"):
            if candidate.is_symlink():
                continue
            candidate.chmod(0o700 if candidate.is_dir() else 0o600)


def path():
    return home() / "nurb.db"


def connect(db_path=None, check_same_thread=True):
    p = pathlib.Path(db_path) if db_path else path()
    p.parent.mkdir(parents=True, exist_ok=True)
    private = db_path is None and not os.environ.get("NURB_HOME")
    if private:
        # Creating the file ourselves avoids a window where SQLite's umask-derived
        # mode exposes a new database before the chmod below.
        p.touch(mode=0o600, exist_ok=True)
        p.chmod(0o600)
    # Autocommit first: journal_mode cannot change inside a transaction, and
    # foreign_keys is a silent no-op there.
    conn = sqlite3.connect(p, autocommit=True, check_same_thread=check_same_thread)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.row_factory = sqlite3.Row
    migrate(conn)
    if private:
        for candidate in (p, pathlib.Path(f"{p}-wal"), pathlib.Path(f"{p}-shm")):
            if candidate.exists():
                candidate.chmod(0o600)
    return conn


@contextlib.contextmanager
def transaction(conn):
    """One atomic write while ordinary reads remain fresh across processes."""
    outer = not conn.in_transaction
    if outer:
        conn.execute("BEGIN IMMEDIATE")
        held, _held.events = getattr(_held, "events", None), []
    try:
        yield conn
    except BaseException:
        if outer:
            conn.execute("ROLLBACK")
            _held.events = held
        raise
    else:
        if outer:
            conn.execute("COMMIT")
            queued, _held.events = _held.events, held
            for event in queued:
                changed(*event)


def migrate(conn):
    have = conn.execute("PRAGMA user_version").fetchone()[0]
    if have > len(MIGRATIONS):
        raise RuntimeError(
            f"{path()} was written by a newer nurb (schema {have}, this one knows {len(MIGRATIONS)}). Upgrade nurb."
        )
    for i, sql in enumerate(MIGRATIONS, start=1):
        if i <= have:
            continue
        try:
            conn.executescript(
                f"BEGIN IMMEDIATE;\n{sql}\nPRAGMA user_version = {i};\nCOMMIT;"
            )
        except BaseException:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise


# Who to tell when a row lands. The serve subscribes one listener and fans the
# events out to the connected pages; nothing else in the engine listens, and nothing
# here knows what a websocket is.
listeners = []

# Events raised while an outer transaction is still open, so a listener never hears
# about a row it cannot read yet. An import wraps a project and all its parts in one
# transaction, and the nested writes announce themselves from inside it; the builder
# woke, read on its own connection, saw nothing, and the parts stayed unbuilt (#339).
_held = threading.local()


def changed(kind, row_id, project_id):
    """Announce a write, once the transaction it belongs to has committed."""
    queued = getattr(_held, "events", None)
    if queued is not None:
        if (kind, row_id, project_id) not in queued:
            queued.append((kind, row_id, project_id))
        return
    _announce(kind, row_id, project_id)


def _announce(kind, row_id, project_id):
    for listener in list(listeners):
        # The bus is a nudge to whoever is watching, never part of the write. A serve
        # shutting down closes its loop under a build thread's feet, and a page that
        # misses an event redraws on its next read; a failed build is forever.
        with contextlib.suppress(Exception):
            listener(kind, row_id, project_id)


def new_id():
    return uuid.uuid4().hex


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def measurement_names(source):
    """Literal names read with `measured()`, in first-use order."""
    try:
        tree = ast.parse(source or "")
    except (SyntaxError, ValueError):
        return []

    found = []
    calls = sorted(
        (
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "measured"
        ),
        key=lambda node: (node.lineno, node.col_offset),
    )
    for call in calls:
        value = call.args[0] if call.args else next(
            (keyword.value for keyword in call.keywords if keyword.arg == "name"), None
        )
        if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
            continue
        if value.value not in found:
            found.append(value.value)
    return found


# A name is a label in a sidebar row, never a paragraph.
NAME_LIMIT = 100


def create_project(conn, name, printer_toml=None, folder=False):
    project_id = new_id()
    with transaction(conn):
        conn.execute(
            "INSERT INTO projects (id, name, printer_toml, folder, created_at) VALUES (?, ?, ?, ?, ?)",
            (project_id, name, printer_toml, int(folder), now()),
        )
    changed("project", project_id, project_id)
    return project_id


def promote_to_folder(conn, project_id, name):
    """Turn a one-part container into a folder the user can see, and name it."""
    name = (name or "").strip()
    if not name:
        raise ValueError("a folder needs a name")
    with transaction(conn):
        updated = conn.execute(
            "UPDATE projects SET folder = 1, name = ? WHERE id = ?", (name, project_id)
        ).rowcount
    if not updated:
        raise ValueError(f"no project {project_id!r}")
    changed("project", project_id, project_id)
    return name


def move_part(conn, part_id, project_id):
    """Carry a part into another project. Returns the project it came from.

    Revisions follow by part_id and need no help. The turns of the transcript that were
    about this part move with it, renumbered onto the end of the target's transcript,
    because sequence_number is only unique within one project. A hidden container has one
    chat with no part names on it, so all of it goes, stamped with this part's name.

    Measurements belong to the project, so they are copied rather than moved: all of a
    hidden container's, or the ones this part reads out of a folder its siblings still use.
    A name the target already has keeps the target's number.
    """
    with transaction(conn):
        part = conn.execute(
            "SELECT p.project_id, p.name, p.kind, j.folder, r.source FROM parts p"
            " JOIN projects j ON j.id = p.project_id"
            " LEFT JOIN part_revisions r ON r.id = p.current_revision_id WHERE p.id = ?",
            (part_id,),
        ).fetchone()
        if part is None:
            raise ValueError(f"no part {part_id!r}")
        if get_project(conn, project_id) is None:
            raise ValueError(f"no project {project_id!r}")
        was = part["project_id"]
        if was == project_id:
            return was
        taken = conn.execute(
            "SELECT 1 FROM parts WHERE project_id = ? AND name = ? AND kind = ?",
            (project_id, part["name"], part["kind"]),
        ).fetchone()
        if taken is not None:
            raise ValueError(
                f"that project already has a part called {part['name']}; rename one of them first"
            )
        conn.execute("UPDATE parts SET project_id = ? WHERE id = ?", (project_id, part_id))
        last = conn.execute(
            "SELECT COALESCE(MAX(sequence_number), 0) FROM messages WHERE project_id = ?",
            (project_id,),
        ).fetchone()[0]
        mine = "" if part["folder"] else " OR part IS NULL"
        moving = conn.execute(
            f"SELECT id FROM messages WHERE project_id = ? AND (part = ?{mine}) ORDER BY sequence_number",
            (was, part["name"]),
        ).fetchall()
        for offset, row in enumerate(moving, start=1):
            conn.execute(
                "UPDATE messages SET project_id = ?, part = ?, sequence_number = ? WHERE id = ?",
                (project_id, part["name"], last + offset, row["id"]),
            )
        reads = measurement_names(part["source"])
        for row in measurements_of(conn, was):
            if part["folder"] and row["name"] not in reads:
                continue
            conn.execute(
                "INSERT OR IGNORE INTO measurements"
                " (id, project_id, name, value, unit, how, provisional, value_changed_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (new_id(), project_id, row["name"], row["value"], row["unit"], row["how"],
                 row["provisional"], row["value_changed_at"]),
            )
    changed("part", part_id, project_id)
    changed("project", was, was)
    changed("project", project_id, project_id)
    return was


def _check_name(name, kind):
    ok = PART_NAME.match(name) if kind == "part" else str(name).isidentifier()
    if not ok:
        raise ValueError(f"not a part name: {name!r}")


def create_part(conn, project_id, name, source, card_md=None, kind="part"):
    _check_name(name, kind)
    part_id, revision_id, stamp = new_id(), new_id(), now()
    with transaction(conn):
        conn.execute(
            "INSERT INTO parts (id, project_id, name, kind, created_at) VALUES (?, ?, ?, ?, ?)",
            (part_id, project_id, name, kind, stamp),
        )
        conn.execute(
            "INSERT INTO part_revisions (id, part_id, source, card_md, created_at) VALUES (?, ?, ?, ?, ?)",
            (revision_id, part_id, source, card_md, stamp),
        )
        conn.execute(
            "UPDATE parts SET current_revision_id = ? WHERE id = ?", (revision_id, part_id)
        )
    changed("part", part_id, project_id)
    return part_id


def add_revision(conn, part_id, source, card_md=None, note=None):
    revision_id = new_id()
    with transaction(conn):
        row = conn.execute(
            "SELECT project_id, current_revision_id FROM parts WHERE id = ?", (part_id,)
        ).fetchone()
        if row is None:
            raise ValueError(f"no part {part_id!r}")
        conn.execute(
            "INSERT INTO part_revisions (id, part_id, source, card_md, parent_id, note, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (revision_id, part_id, source, card_md, row["current_revision_id"], note, now()),
        )
        conn.execute(
            "UPDATE parts SET current_revision_id = ? WHERE id = ?", (revision_id, part_id)
        )
    changed("part", part_id, row["project_id"])
    return revision_id


def set_run_result(conn, run_id, column, payload):
    """Hang a print estimate on the run it was measured from."""
    if column not in RUN_RESULTS:
        raise ValueError(f"a run carries {' and '.join(RUN_RESULTS)}, not {column!r}")
    with transaction(conn):
        row = conn.execute(
            "SELECT p.project_id AS project_id FROM build_runs b"
            " JOIN part_revisions r ON r.id = b.revision_id"
            " JOIN parts p ON p.id = r.part_id WHERE b.id = ?",
            (run_id,),
        ).fetchone()
        if row is None:
            raise ValueError(f"no build run {run_id!r}")
        conn.execute(
            f"UPDATE build_runs SET {column} = ? WHERE id = ?", (json.dumps(payload), run_id)
        )
    changed("build", run_id, row["project_id"])


def delete_project(conn, project_id):
    """Remove a project and everything under it; every child table cascades."""
    with transaction(conn):
        removed = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,)).rowcount
    if not removed:
        raise ValueError(f"no project {project_id!r}")
    changed("project", project_id, project_id)


def delete_part(conn, part_id):
    """Remove a part and every revision under it. The last part in a hidden container
    takes the container with it, because an empty container has nothing left to show.
    Count the siblings: nothing stops an agent writing a second part into a container.
    Returns (project_id, whether the whole project went)."""
    with transaction(conn):
        row = conn.execute(
            "SELECT p.project_id, j.folder,"
            " (SELECT COUNT(*) FROM parts s WHERE s.project_id = p.project_id"
            "  AND s.kind = 'part' AND s.id != p.id) AS siblings"
            " FROM parts p JOIN projects j ON j.id = p.project_id WHERE p.id = ?",
            (part_id,),
        ).fetchone()
        if row is None:
            raise ValueError(f"no part {part_id!r}")
        project_id = row["project_id"]
        whole = not row["folder"] and not row["siblings"]
        if whole:
            conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        else:
            conn.execute("DELETE FROM parts WHERE id = ?", (part_id,))
    if whole:
        changed("project", project_id, project_id)
    else:
        changed("part", part_id, project_id)
    return project_id, whole


def rename_project(conn, project_id, name):
    """Call a project something else. The name is a label, so nothing on disk moves."""
    name = (name or "").strip()
    if not name:
        raise ValueError("a project needs a name")
    with transaction(conn):
        updated = conn.execute(
            "UPDATE projects SET name = ? WHERE id = ?", (name, project_id)
        ).rowcount
    if not updated:
        raise ValueError(f"no project {project_id!r}")
    changed("project", project_id, project_id)
    return name


def part_name_from(text):
    """What a person typed, as a part name: "Bench Hook" is bench_hook."""
    return re.sub(r"[^a-z0-9]+", "_", (text or "").strip().lower()).strip("_")


def rename_part(conn, part_id, name, title=None):
    """Call a part something else. The title is what a person typed and is saved as is;
    the name is its file's name, so when it changes the transcript's turns follow it, and
    the function that carries @part takes the name in a new revision, so the source an
    agent reads agrees with the part it opened."""
    if not PART_NAME.match(name or ""):
        raise ValueError(f"{name or 'that'} can't be a part name: start with a letter, then use letters, numbers and underscores")
    with transaction(conn):
        part = conn.execute("SELECT project_id, name, kind FROM parts WHERE id = ?", (part_id,)).fetchone()
        if part is None:
            raise ValueError(f"no part {part_id!r}")
        old = part["name"]
        if title is not None:
            conn.execute("UPDATE parts SET title = ? WHERE id = ?", (title.strip() or None, part_id))
        if old == name:
            changed("part", part_id, part["project_id"])
            return name
        if conn.execute(
            "SELECT 1 FROM parts WHERE project_id = ? AND name = ? AND kind = ?",
            (part["project_id"], name, part["kind"]),
        ).fetchone():
            raise ValueError(f"this project already has a part called {name}")
        conn.execute("UPDATE parts SET name = ? WHERE id = ?", (name, part_id))
        conn.execute(
            "UPDATE messages SET part = ? WHERE project_id = ? AND part = ?", (name, part["project_id"], old)
        )
        current = conn.execute(
            "SELECT part_revisions.source, part_revisions.card_md FROM parts"
            " JOIN part_revisions ON part_revisions.id = parts.current_revision_id WHERE parts.id = ?",
            (part_id,),
        ).fetchone()
    source = current["source"] if current else None
    renamed = re.sub(rf"^def {re.escape(old)}\(", f"def {name}(", source or "", count=1, flags=re.M)
    if source and renamed != source:
        add_revision(conn, part_id, renamed, card_md=current["card_md"], note=f"Renamed from {old}")
    else:
        changed("part", part_id, part["project_id"])
    # use() opens parts/{name}.py, so a caller still saying the old name would stop
    # building. It also accepts dashes for underscores.
    called = re.compile(rf"""\buse\(\s*(["']){re.escape(old).replace("_", "[_-]")}\1""")
    for row in parts_of(conn, part["project_id"]):
        if row["id"] == part_id or not row["source"]:
            continue
        rewired = called.sub(lambda m: f"use({m[1]}{name}{m[1]}", row["source"])
        if rewired != row["source"]:
            add_revision(conn, row["id"], rewired, card_md=row["card_md"], note=f"{old} renamed to {name}")
    return name


def set_printer(conn, project_id, printer_toml):
    """Name the machine this project prints on."""
    with transaction(conn):
        updated = conn.execute(
            "UPDATE projects SET printer_toml = ? WHERE id = ?", (printer_toml, project_id)
        ).rowcount
    if not updated:
        raise ValueError(f"no project {project_id!r}")
    changed("project", project_id, project_id)


def set_measurement(conn, project_id, name, value, how, unit="mm", provisional=False):
    value = float(value)
    with transaction(conn):
        row = conn.execute(
            "SELECT id, value FROM measurements WHERE project_id = ? AND name = ?",
            (project_id, name),
        ).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO measurements (id, project_id, name, value, unit, how, provisional, value_changed_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (new_id(), project_id, name, value, unit, how, int(provisional), now()),
            )
        else:
            # `value_changed_at` dates the physical measurement, not the row: rewording
            # `how` must not make an old number look freshly taken.
            stamp = now() if row["value"] != value else None
            if stamp:
                conn.execute(
                    "UPDATE measurements SET value = ?, unit = ?, how = ?, provisional = ?, value_changed_at = ?"
                    " WHERE id = ?",
                    (value, unit, how, int(provisional), stamp, row["id"]),
                )
            else:
                conn.execute(
                    "UPDATE measurements SET unit = ?, how = ?, provisional = ? WHERE id = ?",
                    (unit, how, int(provisional), row["id"]),
                )
    changed("project", project_id, project_id)


def set_label(conn, part_id, name, point, normal):
    """Put a label on a spot, or move the one of that name there."""
    name = (name or "").strip()
    if not name:
        raise ValueError("a label needs a name")
    if len(name) > NAME_LIMIT:
        raise ValueError(f"a label's name is at most {NAME_LIMIT} characters")
    with transaction(conn):
        part = conn.execute("SELECT project_id FROM parts WHERE id = ?", (part_id,)).fetchone()
        if part is None:
            raise ValueError(f"no part {part_id!r}")
        conn.execute(
            "INSERT INTO labels (id, part_id, name, x, y, z, nx, ny, nz, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
            " ON CONFLICT (part_id, name) DO UPDATE SET"
            " x = excluded.x, y = excluded.y, z = excluded.z,"
            " nx = excluded.nx, ny = excluded.ny, nz = excluded.nz",
            (new_id(), part_id, name, *map(float, point), *map(float, normal), now()),
        )
    changed("part", part_id, part["project_id"])
    return name


def rename_label(conn, part_id, name, to):
    to = (to or "").strip()
    if not to:
        raise ValueError("a label needs a name")
    if len(to) > NAME_LIMIT:
        raise ValueError(f"a label's name is at most {NAME_LIMIT} characters")
    with transaction(conn):
        part = conn.execute("SELECT project_id FROM parts WHERE id = ?", (part_id,)).fetchone()
        if part is None:
            raise ValueError(f"no part {part_id!r}")
        if to != name and conn.execute(
            "SELECT 1 FROM labels WHERE part_id = ? AND name = ?", (part_id, to)
        ).fetchone():
            raise ValueError(f"this part already has a label called {to}")
        updated = conn.execute(
            "UPDATE labels SET name = ? WHERE part_id = ? AND name = ?", (to, part_id, name)
        ).rowcount
    if not updated:
        raise ValueError(f"no label called {name}")
    changed("part", part_id, part["project_id"])
    return to


def delete_label(conn, part_id, name):
    with transaction(conn):
        part = conn.execute("SELECT project_id FROM parts WHERE id = ?", (part_id,)).fetchone()
        if part is None:
            raise ValueError(f"no part {part_id!r}")
        removed = conn.execute(
            "DELETE FROM labels WHERE part_id = ? AND name = ?", (part_id, name)
        ).rowcount
    if not removed:
        raise ValueError(f"no label called {name}")
    changed("part", part_id, part["project_id"])


def labels_of(conn, part_id):
    return conn.execute(
        "SELECT * FROM labels WHERE part_id = ? ORDER BY created_at, name", (part_id,)
    ).fetchall()


def get_project(conn, project_id):
    return conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()


def parts_of(conn, project_id):
    return conn.execute(
        "SELECT p.*, r.source AS source, r.card_md AS card_md"
        " FROM parts p LEFT JOIN part_revisions r ON r.id = p.current_revision_id"
        " WHERE p.project_id = ? ORDER BY p.name",
        (project_id,),
    ).fetchall()


def measurements_of(conn, project_id):
    return conn.execute(
        "SELECT * FROM measurements WHERE project_id = ? ORDER BY name", (project_id,)
    ).fetchall()


def add_project_file(conn, project_id, path, content, executable=False):
    with transaction(conn):
        conn.execute(
            "INSERT INTO project_files (id, project_id, path, content, executable) VALUES (?, ?, ?, ?, ?)",
            (new_id(), project_id, path, content, bool(executable)),
        )


def project_files_of(conn, project_id):
    return conn.execute(
        "SELECT path, content, executable FROM project_files WHERE project_id = ? ORDER BY path",
        (project_id,),
    ).fetchall()


def add_attachment(conn, project_id, name, mime, data):
    """Store one reference image, replacing any earlier one of the same name."""
    attachment_id = new_id()
    with transaction(conn):
        conn.execute(
            "INSERT INTO attachments (id, project_id, name, mime, bytes, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)"
            " ON CONFLICT (project_id, name) DO UPDATE SET"
            " mime = excluded.mime, bytes = excluded.bytes, created_at = excluded.created_at",
            (attachment_id, project_id, name, mime, data, now()),
        )
        row = conn.execute(
            "SELECT id FROM attachments WHERE project_id = ? AND name = ?", (project_id, name)
        ).fetchone()
    return row["id"]


def attachments_of(conn, project_id):
    return conn.execute(
        "SELECT * FROM attachments WHERE project_id = ? ORDER BY created_at, name",
        (project_id,),
    ).fetchall()


def add_message(conn, project_id, role, content, payload, part=None):
    message_id = new_id()
    with transaction(conn):
        seq = conn.execute(
            "SELECT COALESCE(MAX(sequence_number), 0) + 1 FROM messages WHERE project_id = ?",
            (project_id,),
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO messages (id, project_id, role, content, payload, part, sequence_number, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (message_id, project_id, role, content, json.dumps(payload), part, seq, now()),
        )
    changed("message", message_id, project_id)
    return message_id


def claim_messages(conn, project_id, part, after):
    """Stamp a folder's unnamed turns after `after` with the part they made.

    A new part in a folder is described before it has a name, so its first turns are
    stored without one and handed to the part once the agent has written it.
    """
    with transaction(conn):
        claimed = conn.execute(
            "UPDATE messages SET part = ? WHERE project_id = ? AND part IS NULL AND sequence_number > ?",
            (part, project_id, after),
        ).rowcount
    if claimed:
        changed("message", None, project_id)
    return claimed


def latest_run(conn, part_id, revision_id=None):
    """The part's newest build attempt, whatever its status, across every revision.

    Pass `revision_id` to ask about one revision only. A reader that reports current
    state needs that: a revision commits before its build runs, so an older revision's
    passing run would otherwise stand in for source that has since changed.
    """
    if revision_id is not None:
        return conn.execute(
            "SELECT * FROM build_runs WHERE revision_id = ? ORDER BY started_at DESC LIMIT 1",
            (revision_id,),
        ).fetchone()
    return conn.execute(
        "SELECT b.* FROM build_runs b JOIN part_revisions r ON r.id = b.revision_id"
        " WHERE r.part_id = ? ORDER BY b.started_at DESC LIMIT 1",
        (part_id,),
    ).fetchone()


def latest_ok_run(conn, part_id):
    """The part's newest build that produced geometry, whatever revision made it.

    A picture outlives a failed edit: `look` shows the last build that worked and says
    it is stale, rather than going blank because the source is mid-repair.
    """
    return conn.execute(
        "SELECT b.* FROM build_runs b JOIN part_revisions r ON r.id = b.revision_id"
        " WHERE r.part_id = ? AND b.status = 'ok' AND b.glb IS NOT NULL"
        " ORDER BY b.started_at DESC LIMIT 1",
        (part_id,),
    ).fetchone()
