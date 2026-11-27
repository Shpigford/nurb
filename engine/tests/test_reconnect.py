"""A reconnect survives a build worker that was force-killed.

A build worker holds the database open on purpose, and when it will not stop it is
force-killed. The kernel releases that process's file handles, but not instantly, and
a connect landing in that window reads a write-ahead log whose shared-memory header is
no longer coherent. SQLite reports it as "disk I/O error". That is not a lock timeout,
so busy_timeout does not cover it, and it clears a few hundred milliseconds later when
the kernel has finished.

Measured on Windows after a hard kill: 6 of 25 connects failed on the first attempt,
0 of 25 with the retry.

The race itself cannot be asserted - it depends on how fast this machine reaps a
process, which is why the earlier attempts at this test passed on both the broken and
the fixed code. These drive the retry directly instead: the open fails and then
succeeds, which is the shape the race produces.
"""

import sqlite3

import pytest

from nurb import db


@pytest.fixture
def fresh(tmp_path):
    return tmp_path / "nurb.db"


def fail_n_times(monkeypatch, n, error):
    """Raise for the first n sqlite3.connect calls, then behave normally."""
    real = sqlite3.connect
    seen = []

    def connect(*args, **kwargs):
        seen.append(len(seen) + 1)
        if len(seen) <= n:
            raise error
        return real(*args, **kwargs)

    monkeypatch.setattr(db.sqlite3, "connect", connect)
    return seen


def test_a_stale_wal_error_is_retried(fresh, monkeypatch):
    seen = fail_n_times(monkeypatch, 1, sqlite3.OperationalError("disk I/O error"))
    conn = db.connect(fresh)
    try:
        assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        project = db.create_project(conn, "slabs")
        assert db.get_project(conn, project)["name"] == "slabs"
    finally:
        conn.close()

    assert len(seen) == 2, "the connect should have retried exactly once"


def test_the_retry_gives_up_and_reports_the_real_error(fresh, monkeypatch):
    """A database that is genuinely broken still fails, rather than hanging or lying."""
    seen = fail_n_times(
        monkeypatch, db.RECONNECT_ATTEMPTS, sqlite3.OperationalError("unable to open database file")
    )
    with pytest.raises(sqlite3.OperationalError, match="unable to open database file"):
        db.connect(fresh)

    assert len(seen) == db.RECONNECT_ATTEMPTS


def test_a_failed_attempt_closes_what_it_opened(fresh, monkeypatch):
    """An attempt that dies partway must close its handle before opening another.

    The stale WAL surfaces partway through, not at the open, so this fails inside
    migrate() with a real connection already in hand. Without the close, every retry
    leaks one open handle to the database - which on Windows keeps the very window
    this retry is waiting out alive.
    """
    opened = []
    real = sqlite3.connect

    def connect(*args, **kwargs):
        conn = real(*args, **kwargs)
        opened.append(conn)
        return conn

    real_migrate = db.migrate

    def migrate(conn):
        if len(opened) == 1:
            raise sqlite3.OperationalError("disk I/O error")
        return real_migrate(conn)

    monkeypatch.setattr(db.sqlite3, "connect", connect)
    monkeypatch.setattr(db, "migrate", migrate)

    conn = db.connect(fresh)
    conn.close()

    assert len(opened) == 2, "the attempt should have been retried once"
    discarded = [handle for handle in opened if handle is not conn]
    assert discarded, "the first attempt should have opened something"
    for handle in discarded:
        with pytest.raises(sqlite3.ProgrammingError):
            handle.execute("SELECT 1")
