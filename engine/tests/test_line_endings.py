"""A part nurb writes holds the same bytes on every machine.

`Path.write_text` and `open(..., "w")` default to `newline=None`, which on Windows
translates "\n" to os.linesep. Without a pinned newline the same part is CRLF on one
machine and LF on the other, which is not cosmetic. A folder checked out on Windows
and put under git shows every line changed. A part written on Windows and opened on
macOS carries carriage returns into source a person then has to edit. And a project
folder shared between two machines disagrees about its own contents while agreeing
about its meaning, because Python parses both happily.

These assert the bytes rather than the string, since the translation happens between
them. The examples are the stronger half: `notch` is LF in git, so a checkout that
translates is caught by comparing against the file on disk.
"""

import pathlib

import pytest

from nurb import db, folder

NOTCH = pathlib.Path(__file__).parents[1] / "examples" / "notch"

SOURCE = "from nurb import *\n\n\n@part\ndef slab(width=40.0):\n    return Box(width, 10, 2)\n"


@pytest.fixture
def conn(tmp_path):
    conn = db.connect(tmp_path / "x.db")
    yield conn
    conn.close()


@pytest.fixture
def slab(conn):
    project = db.create_project(conn, "slabs")
    db.create_part(conn, project, "slab", SOURCE)
    return project


def text_files(root):
    """The files whose bytes are text. A project's own binary asset may hold any byte."""
    return [p for p in sorted(root.rglob("*")) if p.is_file() and p.suffix in {".py", ".md", ".toml"}]


def test_a_checked_out_part_is_byte_for_byte_the_source(conn, slab, tmp_path):
    out = folder.checkout(conn, slab, tmp_path / "out")
    assert (out / "parts" / "slab.py").read_bytes() == SOURCE.encode("utf-8")


def test_a_checked_out_folder_holds_no_carriage_return(conn, slab, tmp_path):
    out = folder.checkout(conn, slab, tmp_path / "out")
    written = text_files(out)
    assert written, "the checkout wrote nothing, so this test would pass by accident"
    for path in written:
        raw = path.read_bytes()
        assert b"\r" not in raw, f"{path.name} carries a carriage return: {raw[:80]!r}"


def test_a_real_project_checks_out_with_the_bytes_it_shipped(conn, tmp_path):
    """The examples are LF in git, so a translating checkout fails here."""
    project_id, _ = folder.import_folder(conn, NOTCH)
    out = folder.checkout(conn, project_id, tmp_path / "out")
    written = sorted(p.name for p in (out / "parts").glob("*.py"))
    assert written, "the checkout wrote no parts, so this test would pass by accident"
    for name in written:
        assert (out / "parts" / name).read_bytes() == (NOTCH / "parts" / name).read_bytes(), (
            f"{name} did not survive the round trip with its bytes intact"
        )
