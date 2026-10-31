"""Rows back into the folder the engine can build.

`builder.build` loads a file and puts the project root on sys.path, so every v2 build
starts by writing the project out to a scratch directory. It is a snapshot, not a merge:
a part deleted in the database must not survive on disk as a file that still imports.
"""

import math
import os
import pathlib
import re
import shutil

from . import db


def toml_string(value):
    out = str(value).replace("\\", "\\\\").replace('"', '\\"')
    out = out.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
    return '"' + re.sub(r"[\x00-\x1f\x7f]", lambda m: f"\\u{ord(m.group()):04x}", out) + '"'


def measurements_toml(rows):
    """The measurements file, exactly as the v1 folder wants it."""
    tables = []
    for row in rows:
        name = row["name"]
        value = float(row["value"])
        if not math.isfinite(value):
            raise ValueError(f"{name} is not a finite measurement: {value!r}")
        try:
            unit = row["unit"]
        except (KeyError, IndexError):
            unit = "mm"
        # A bare key stays bare, so a checkout reads like the file the user wrote.
        header = name if re.fullmatch(r"[A-Za-z0-9_-]+", name) else toml_string(name)
        lines = [
            f"[{header}]",
            f"value = {value!r}",
            f"unit = {toml_string(unit)}",
            f"how = {toml_string(row['how'])}",
        ]
        if row["provisional"]:
            lines.append("provisional = true")
        tables.append("\n".join(lines))
    return "\n\n".join(tables) + "\n" if tables else ""


def _project_file_path(root, relative):
    path = pathlib.PurePosixPath(relative)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"not a project file path: {relative!r}")
    target = root.joinpath(*path.parts)
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"not a project file path: {relative!r}")
    return target


def write_project_files(conn, project_id, root):
    for row in db.project_files_of(conn, project_id):
        target = _project_file_path(root, row["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(row["content"])
        if row["executable"]:
            target.chmod(target.stat().st_mode | 0o111)


def materialize(conn, project_id, into=None):
    private = into is None and not os.environ.get("NURB_HOME")
    directory_mode = 0o700 if private else 0o777
    if into:
        root = pathlib.Path(into)
    else:
        scratch = db.home() / "scratch"
        scratch.mkdir(parents=True, exist_ok=True, mode=directory_mode)
        if private:
            scratch.chmod(0o700)
        root = scratch / project_id
    if root.is_symlink():
        raise ValueError(f"materialization directory is a symlink: {root}")
    if root.exists():
        for child in root.iterdir():
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink()
    parts = root / "parts"
    parts.mkdir(parents=True, exist_ok=True, mode=directory_mode)
    if private:
        root.chmod(0o700)
        parts.chmod(0o700)
    write_project_files(conn, project_id, root)

    for row in db.parts_of(conn, project_id):
        if row["source"] is None:
            continue
        name, kind = row["name"], row["kind"]
        # The name becomes a path here, so it is checked here too.
        if kind == "part":
            if not db.PART_NAME.match(name):
                raise ValueError(f"not a part name: {name!r}")
            (parts / f"{name}.py").write_text(row["source"], encoding="utf-8")
            if row["card_md"]:
                (parts / f"{name}.md").write_text(row["card_md"], encoding="utf-8")
        elif kind == "module":
            if not name.isidentifier():
                raise ValueError(f"not a part name: {name!r}")
            (root / f"{name}.py").write_text(row["source"], encoding="utf-8")
        elif kind == db.PARTS_MODULE_KIND:
            if not name.isidentifier() or not name.startswith("_"):
                raise ValueError(f"not a parts module name: {name!r}")
            (parts / f"{name}.py").write_text(row["source"], encoding="utf-8")
        else:
            raise ValueError(f"not a part kind: {kind!r}")

    (root / "measurements.toml").write_text(
        measurements_toml(db.measurements_of(conn, project_id)), encoding="utf-8"
    )
    project = db.get_project(conn, project_id)
    if project and project["printer_toml"]:
        (root / "printer.toml").write_text(project["printer_toml"], encoding="utf-8")
    if private:
        for candidate in root.rglob("*"):
            if candidate.is_symlink():
                continue
            candidate.chmod(
                0o700 if candidate.is_dir() or candidate.stat().st_mode & 0o111 else 0o600
            )
    return root
