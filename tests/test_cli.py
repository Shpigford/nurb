"""Configuration-set validation happens before artifact writes."""

import pytest

from nurb import cli


def test_export_rejects_a_configuration_error(monkeypatch, tmp_path):
    part = tmp_path / "parts" / "thing.py"
    monkeypatch.setattr(cli, "_configs", lambda path: [])
    with pytest.raises(SystemExit) as exc:
        cli._collect_exports([part])
    assert exc.value.code == 1


def test_export_rejects_duplicate_artifact_names(monkeypatch, tmp_path, capsys):
    one = tmp_path / "parts" / "one.py"
    two = tmp_path / "parts" / "two.py"
    ctx = object()
    configs = {
        one: [("shared", {}, ctx)],
        two: [("shared", {"width": 20}, ctx)],
    }
    monkeypatch.setattr(cli, "_configs", configs.__getitem__)
    with pytest.raises(SystemExit) as exc:
        cli._collect_exports([one, two])
    assert exc.value.code == 1
    output = capsys.readouterr().out
    assert "shared" in output
    assert "one.py" in output
    assert "two.py" in output


def test_export_collection_keeps_the_source_part(monkeypatch, tmp_path):
    part = tmp_path / "parts" / "thing.py"
    ctx = object()
    monkeypatch.setattr(cli, "_configs", lambda path: [("thing", {"width": 20}, ctx)])
    assert cli._collect_exports([part]) == [(part, "thing", {"width": 20}, ctx)]


# --- picking a port -----------------------------------------------------------


def test_an_unasked_port_walks_past_one_that_is_busy():
    """A project is any directory with parts/, so two at once is the ordinary case."""
    import socket

    with socket.socket() as held:
        held.bind(("127.0.0.1", 0))
        held.listen()
        busy = held.getsockname()[1]
        assert cli._pick_port(None) != busy
        assert cli._is_free(busy) is False


def test_asking_for_a_busy_port_is_an_error_not_a_suggestion():
    """`--port 7373` picking 7374 would open a tab onto somebody else's parts."""
    import socket

    with socket.socket() as held:
        held.bind(("127.0.0.1", 0))
        held.listen()
        busy = held.getsockname()[1]
        with pytest.raises(SystemExit) as exc:
            cli._pick_port(busy)
        assert str(busy) in str(exc.value.code)
