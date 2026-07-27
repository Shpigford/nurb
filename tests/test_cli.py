"""Configuration-set validation happens before artifact writes."""

import pathlib

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


# --- day one ------------------------------------------------------------------


def _new(tmp_path, name="thing"):
    import argparse, os
    was = os.getcwd()
    os.chdir(tmp_path)
    try:
        cli.cmd_new(argparse.Namespace(name=name))
    finally:
        os.chdir(was)


def test_a_fresh_project_gets_a_pointer_at_the_doctrine(tmp_path, capsys):
    """Day one is the whole problem. A project is two files that read like an ordinary
    build123d script, so an agent treats them as one and never types `nurb`."""
    _new(tmp_path)
    shim = tmp_path / "AGENTS.md"
    assert shim.is_file()
    assert "nurb rules" in shim.read_text(encoding="utf-8")
    assert "nurb check" in shim.read_text(encoding="utf-8")
    assert "AGENTS.md" in capsys.readouterr().out  # it says what it wrote


def test_the_shim_it_writes_is_the_one_the_package_ships():
    """One copy, in the package, which is the rule the doctrine already follows."""
    shipped = (pathlib.Path(cli.__file__).parent / "agents.md").read_text(encoding="utf-8")
    repo = pathlib.Path(__file__).parents[1]
    assert (repo / "AGENTS.md").read_text(encoding="utf-8") == shipped
    assert shipped in (repo / "SKILL.md").read_text(encoding="utf-8")


def test_a_second_part_does_not_mention_the_shim_again(tmp_path, capsys):
    _new(tmp_path, "one")
    capsys.readouterr()
    _new(tmp_path, "two")
    assert "AGENTS.md" not in capsys.readouterr().out


def test_a_harness_file_of_the_user_s_own_is_never_touched(tmp_path, capsys):
    (tmp_path / "CLAUDE.md").write_text("# mine\n", encoding="utf-8")
    _new(tmp_path)
    assert (tmp_path / "CLAUDE.md").read_text(encoding="utf-8") == "# mine\n"
    assert not (tmp_path / "AGENTS.md").exists()
    assert "CLAUDE.md is yours" in capsys.readouterr().out
