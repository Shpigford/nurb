"""The two doors between a v1 folder and the v2 store.

`import_folder` reads a project in; `checkout` writes one back out. Neither is a sync:
importing twice makes two projects, and a checkout wants an empty directory.
"""

import os
import pathlib
import tomllib

from . import db, materialize


IGNORED_DIRECTORIES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
}
IGNORED_FILES = {".DS_Store"}

# Images under references/ are the project's reference photos, so they become
# attachments a model can look at rather than opaque project files.
REFERENCES = "references"
IMAGE_MIMES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


def import_folder(conn, directory):
    """Read a v1 project folder into the database. Returns (project_id, part_count)."""
    root = pathlib.Path(directory).resolve()
    parts_dir = root / "parts"
    if parts_dir.is_symlink():
        raise ValueError("parts/: symlinks are not allowed when importing a project")
    if not parts_dir.is_dir():
        raise ValueError(f"no parts/ in {root}")

    printer = root / "printer.toml"
    if printer.is_symlink():
        raise ValueError("printer.toml: symlinks are not allowed when importing a project")
    with db.transaction(conn):
        project_id = db.create_project(
            conn,
            root.name,
            printer.read_text(encoding="utf-8") if printer.is_file() else None,
            folder=True,
        )
        count = _read_into(conn, project_id, root, parts_dir)
    return project_id, count


def _read_into(conn, project_id, root, parts_dir):
    count = 0
    part_files = sorted(parts_dir.glob("*.py"))
    root_modules = [py for py in sorted(root.glob("*.py")) if py.stem.isidentifier()]
    cards = [py.with_suffix(".md") for py in part_files if not py.stem.startswith("_")]
    book = root / "measurements.toml"
    for path in [*part_files, *root_modules, *cards, book]:
        if path.is_symlink():
            relative = path.relative_to(root).as_posix()
            raise ValueError(f"{relative}: symlinks are not allowed when importing a project")

    for py in part_files:
        if py.stem.startswith("_"):
            continue
        # v1 builds parts/Bracket.py happily; v2 cannot, because the name is also a
        # tool argument and a slug.
        if not db.PART_NAME.match(py.stem):
            raise ValueError(
                f"{py.name}: a part name is lowercase snake_case, so rename the file and import again"
            )
        card = py.with_suffix(".md")
        db.create_part(
            conn,
            project_id,
            py.stem,
            py.read_text(encoding="utf-8"),
            card_md=card.read_text(encoding="utf-8") if card.is_file() else None,
        )
        count += 1

    # A project's shared code: root modules the parts import, plus the underscored
    # files in parts/ that `nurb build` already skips.
    for py in root_modules:
        db.create_part(
            conn, project_id, py.stem, py.read_text(encoding="utf-8"), kind="module"
        )
    for py in (path for path in part_files if path.stem.startswith("_")):
        db.create_part(
            conn,
            project_id,
            py.stem,
            py.read_text(encoding="utf-8"),
            kind=db.PARTS_MODULE_KIND,
        )

    if book.is_file():
        for name, entry in tomllib.loads(book.read_text(encoding="utf-8")).items():
            db.set_measurement(
                conn,
                project_id,
                name,
                float(entry["value"]),
                entry["how"],
                unit=entry.get("unit", "mm"),
                provisional=bool(entry.get("provisional", False)),
            )

    modeled = {*root_modules, *part_files, *cards, book, root / "printer.toml"}
    for directory, names, filenames in os.walk(root, followlinks=False):
        names[:] = sorted(
            name
            for name in names
            if name not in IGNORED_DIRECTORIES and not (pathlib.Path(directory) / name).is_symlink()
        )
        for filename in sorted(filenames):
            path = pathlib.Path(directory) / filename
            if (
                path.is_symlink()
                or filename in IGNORED_FILES
                or path.resolve() in modeled
                or path.suffix in {".pyc", ".pyo"}
            ):
                continue
            relative = path.relative_to(root)
            mime = IMAGE_MIMES.get(path.suffix.lower())
            if mime and relative.parts[0] == REFERENCES:
                # The path below references/ is the name, so two photos in sibling
                # folders with one basename stay two photos.
                name = pathlib.PurePosixPath(*relative.parts[1:]).as_posix()
                db.add_attachment(conn, project_id, name, mime, path.read_bytes())
                continue
            db.add_project_file(
                conn,
                project_id,
                relative.as_posix(),
                path.read_bytes(),
                executable=bool(path.stat().st_mode & 0o111),
            )

    return count


def checkout(conn, project_id, directory):
    """Write a project out as a v1 folder, into a directory that is empty or absent."""
    root = pathlib.Path(directory)
    if root.exists() and any(root.iterdir()):
        raise ValueError(f"{root.name} already has files in it, so export to a new folder")
    parts = root / "parts"
    parts.mkdir(parents=True, exist_ok=True)

    materialize.write_project_files(conn, project_id, root)

    attachments = db.attachments_of(conn, project_id)
    if attachments:
        (root / REFERENCES).mkdir(parents=True, exist_ok=True)
        for row in attachments:
            name = pathlib.PurePosixPath(row["name"])
            if name.is_absolute() or not name.parts or ".." in name.parts:
                raise ValueError(f"not an attachment name: {row['name']!r}")
            target = root / REFERENCES / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(row["bytes"])

    for row in db.parts_of(conn, project_id):
        if row["source"] is None:
            continue
        name = row["name"]
        if row["kind"] == "part":
            if not db.PART_NAME.match(name):
                raise ValueError(f"not a part name: {name!r}")
            (parts / f"{name}.py").write_text(row["source"], encoding="utf-8")
            if row["card_md"]:
                (parts / f"{name}.md").write_text(row["card_md"], encoding="utf-8")
        elif row["kind"] == "module":
            if not name.isidentifier():
                raise ValueError(f"not a part name: {name!r}")
            (root / f"{name}.py").write_text(row["source"], encoding="utf-8")
        elif row["kind"] == db.PARTS_MODULE_KIND:
            if not name.isidentifier() or not name.startswith("_"):
                raise ValueError(f"not a parts module name: {name!r}")
            (parts / f"{name}.py").write_text(row["source"], encoding="utf-8")
        else:
            raise ValueError(f"not a part kind: {row['kind']!r}")

    rows = db.measurements_of(conn, project_id)
    if rows:
        (root / "measurements.toml").write_text(
            materialize.measurements_toml(rows), encoding="utf-8"
        )
    project = db.get_project(conn, project_id)
    if project and project["printer_toml"]:
        (root / "printer.toml").write_text(project["printer_toml"], encoding="utf-8")
    return root
