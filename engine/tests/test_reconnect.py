"""A reconnect survives a build worker that was force-killed.

A build worker holds the database open on purpose, and when it will not stop it is
force-killed. The kernel releases that process's file handles a moment later, and a
connect landing in that window gets "disk I/O error" from the journal_mode read rather
than "database is locked" - so busy_timeout does not cover it. It clears within a few
hundred milliseconds once the kernel has finished.

Measured on Windows over rounds of start-a-worker, write, kill, connect-immediately:
5 of 15 plain connects failed, 0 of 15 with the wait. Every failure landed on that one
statement - never on the write, never on migrate(), never on the first read after it -
which is why the wait is on the read and nowhere else. Retrying on the connection that
already failed is enough; a fresh connect per attempt measures the same.

The race itself cannot be asserted - it depends on how fast this machine reaps a
process, which is why earlier attempts at this test passed on both the broken and the
fixed code. These drive the helper and the open directly.

sqlite3.Connection is an immutable type, so its execute cannot be monkeypatched. The
statement is intercepted one level up, at the connect that db calls.
"""

import sqlite3

import pytest

from nurb import db


class Recorder:
    """Wraps a real connection, counting statements and failing chosen ones once."""

    def __init__(self, real, statements, fail_on, fail_times):
        self.real = real
        self.statements = statements
        self.fail_on = fail_on
        self.fail_times = fail_times
        self.faulted = 0

    def execute(self, statement, *args, **kwargs):
        self.statements.append(statement)
        if self.fail_on is not None and self.fail_on in statement and self.faulted < self.fail_times:
            self.faulted += 1
            raise sqlite3.OperationalError("disk I/O error")
        return self.real.execute(statement, *args, **kwargs)

    def close(self):
        return self.real.close()

    # Assignment has to reach the real connection. Without this, db's
    # `conn.row_factory = sqlite3.Row` lands on the wrapper and rows come back as
    # tuples, so the test fails somewhere far from what it is testing.
    @property
    def row_factory(self):
        return self.real.row_factory

    @row_factory.setter
    def row_factory(self, value):
        self.real.row_factory = value

    def __getattr__(self, name):
        return getattr(self.real, name)


class Connector:
    """Stands in for the sqlite3 module inside db, wrapping only connect().

    Everything else - Row, the exception types, the constants - comes from the real
    module, so db keeps seeing the sqlite3 it expects.
    """

    def __init__(self, statements, fail_on=None, fail_times=0):
        self.statements = statements
        self.fail_on = fail_on
        self.fail_times = fail_times
        self.connections = 0

    def connect(self, *args, **kwargs):
        self.connections += 1
        return Recorder(
            sqlite3.connect(*args, **kwargs), self.statements, self.fail_on, self.fail_times
        )

    def __getattr__(self, name):
        return getattr(sqlite3, name)


def journal_reads(statements):
    return [s for s in statements if "journal_mode" in s and "journal_mode =" not in s]


def journal_writes(statements):
    return [s for s in statements if "journal_mode =" in s]


def test_a_dying_holder_is_waited_for(tmp_path, monkeypatch):
    """The read fails once with a disk I/O error, and the retry gets through."""
    statements = []
    monkeypatch.setattr(db, "sqlite3", Connector(statements, fail_on="journal_mode", fail_times=1))

    conn = db.connect(tmp_path / "nurb.db")
    # Counted here, before this test does its own read of the mode, so the number is
    # what connect() did and not what connect() plus an assertion did.
    during_connect = len(journal_reads(statements))
    try:
        assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        project = db.create_project(conn, "slabs")
        assert db.get_project(conn, project)["name"] == "slabs"
    finally:
        conn.close()

    assert during_connect == 2, "the read should have been attempted twice"


def test_an_already_wal_database_is_not_rewritten(tmp_path, monkeypatch):
    """Setting journal_mode is a write that takes an exclusive lock even when the file
    is already WAL, so a reconnect should read the mode and leave it alone."""
    first = db.connect(tmp_path / "nurb.db")
    first.close()

    statements = []
    monkeypatch.setattr(db, "sqlite3", Connector(statements))
    conn = db.connect(tmp_path / "nurb.db")
    conn.close()

    assert journal_writes(statements) == [], (
        "a reconnect set journal_mode on a database that was already WAL"
    )


def test_a_fresh_database_is_still_converted(tmp_path, monkeypatch):
    """The guard must not skip the one write that actually matters."""
    statements = []
    monkeypatch.setattr(db, "sqlite3", Connector(statements))
    conn = db.connect(tmp_path / "nurb.db")
    conn.close()

    assert journal_writes(statements) == ["PRAGMA journal_mode = WAL"]


def test_an_unrelated_error_is_not_retried(tmp_path, monkeypatch):
    """Only the disk I/O error is waited out. Anything else is a real problem."""
    opened = []

    class OtherError(Connector):
        def connect(self, *args, **kwargs):
            opened.append(args)
            raise sqlite3.OperationalError("unable to open database file")

    monkeypatch.setattr(db, "sqlite3", OtherError(opened))
    with pytest.raises(sqlite3.OperationalError, match="unable to open database file"):
        db.connect(tmp_path / "nurb.db")


def test_the_wait_gives_up_rather_than_hanging_forever(tmp_path, monkeypatch):
    """A database that never becomes readable has to surface the error, not spin.

    Driven through the helper with a short deadline rather than through connect(),
    whose real deadline is ten seconds - long enough to cover a dying process, far too
    long to sit through in a test.
    """
    statements = []
    recorder = Recorder(
        sqlite3.connect(tmp_path / "nurb.db", autocommit=True),
        statements,
        fail_on="journal_mode",
        fail_times=10**6,
    )
    with pytest.raises(sqlite3.OperationalError, match="disk I/O error"):
        db._read_journal_mode(recorder, deadline_seconds=0.3)

    assert len(journal_reads(statements)) > 1, "it should have waited before giving up"
    recorder.close()
