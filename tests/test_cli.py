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


# --- verify -------------------------------------------------------------------


PLAIN = "from nurb import *\n\n\n@part\ndef thing(w=10.0, draft=False):\n    return Box(w, w, w)\n"


def _finished(tmp_path, source=None):
    """A part that passes `nurb verify`: real geometry, and a card someone wrote."""
    import argparse

    parts = tmp_path / "parts"
    parts.mkdir(exist_ok=True)
    (parts / "thing.py").write_text(source or PLAIN)
    body = "# thing\n\n" + "".join(
        f"{h}\n\nsomething\n\n" for h in
        ("## What it is", "## Design notes", "## Don't", "## Changelog")
    )
    (parts / "thing.md").write_text(body)
    cli.cmd_card(argparse.Namespace(part=None))
    return parts / "thing.py"


def test_verify_fails_on_a_card_that_disagrees_with_its_part(tmp_path, monkeypatch, capsys):
    """The command has to be able to fail, or it is decoration."""
    import argparse

    monkeypatch.chdir(tmp_path)
    part = _finished(tmp_path)
    cli.cmd_verify(argparse.Namespace(part=None))  # passes first
    assert "ok," in capsys.readouterr().out

    md = part.with_suffix(".md")
    md.write_text(md.read_text().replace("Size:", "Size: TAMPERED", 1))
    with pytest.raises(SystemExit) as exc:
        cli.cmd_verify(argparse.Namespace(part=None))
    assert exc.value.code == 1
    assert "card disagrees with the geometry" in capsys.readouterr().out


def test_verify_says_what_it_cannot_check(tmp_path, monkeypatch, capsys):
    """Two of the doctrine's six items need a human, and hiding that is worse."""
    import argparse

    parts = tmp_path / "parts"
    parts.mkdir()
    (parts / "thing.py").write_text(PLAIN)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        cli.cmd_verify(argparse.Namespace(part=None))
    assert "fit faces by coordinate" in capsys.readouterr().out


# --- provisional measurements -------------------------------------------------


def test_a_guess_is_allowed_to_be_written_down_and_has_to_say_so(tmp_path):
    from nurb.measurements import measured, provisional

    (tmp_path / "parts").mkdir()
    (tmp_path / "measurements.toml").write_text(
        '[bore]\nvalue = 24.0\nunit = "mm"\nhow = "eyeballed"\nprovisional = true\n\n'
        '[pitch]\nvalue = 25.16\nunit = "mm"\nhow = "calipers"\n',
        encoding="utf-8",
    )
    assert measured("bore", start=tmp_path) == 24.0  # it still builds a real part
    assert provisional(tmp_path) == [("bore", "eyeballed")]  # and it still says so


def test_verify_tells_a_missing_card_block_from_a_stale_one(tmp_path, monkeypatch, capsys):
    """The first thing a new user sees from this command should be true.

    A card that has never been generated was reported as disagreeing with the geometry,
    which reads as a defect in a part that has none.
    """
    import argparse

    parts = tmp_path / "parts"
    parts.mkdir()
    (parts / "thing.py").write_text(PLAIN)
    (parts / "thing.md").write_text("# thing\n")
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        cli.cmd_verify(argparse.Namespace(part=None))
    assert "no generated block yet" in capsys.readouterr().out


def test_verify_names_the_counts_it_flexed(tmp_path, monkeypatch, capsys):
    """"0 flexes" reads like a pass and means the sweep never ran."""
    import argparse

    monkeypatch.chdir(tmp_path)
    _finished(tmp_path, "from nurb import *\n\n\n@part\n"
                        "def thing(rows=2, w=10.0, draft=False):\n"
                        "    return Box(w, w, w * rows)\n")
    capsys.readouterr()
    cli.cmd_verify(argparse.Namespace(part=None))
    assert "flexed rows" in capsys.readouterr().out


def test_verify_says_so_when_a_part_has_no_counts_to_flex(tmp_path, monkeypatch, capsys):
    import argparse

    monkeypatch.chdir(tmp_path)
    _finished(tmp_path)
    capsys.readouterr()
    cli.cmd_verify(argparse.Namespace(part=None))
    assert "no counts to flex" in capsys.readouterr().out


def test_export_refuses_a_format_it_cannot_write(tmp_path, monkeypatch, capsys):
    """It used to print the filename anyway and exit 0."""
    import argparse

    parts = tmp_path / "parts"
    parts.mkdir()
    (parts / "thing.py").write_text(PLAIN)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        cli.cmd_export(argparse.Namespace(part=None, formats=["obj"]))
    assert "no exporter for 'obj'" in str(exc.value.code)
    assert not (tmp_path / "build" / "thing.obj").exists()


def test_the_shim_promises_what_export_actually_writes():
    shim = (pathlib.Path(cli.__file__).parent / "agents.md").read_text(encoding="utf-8")
    assert "STL and STEP" in shim
    assert list(cli.DEFAULT_FORMATS) == ["stl", "step"]


# --- the agent skill ----------------------------------------------------------


def test_skill_output_is_the_shipped_file(capsys):
    cli.main(["skill"])
    printed = capsys.readouterr().out
    shipped = (pathlib.Path(cli.__file__).parent / "skill.md").read_text(encoding="utf-8")
    assert printed.strip() == shipped.strip()
    assert "nurb rules" in printed  # a shim points at the doctrine, never copies it


def test_the_skill_is_the_shim_with_a_trigger_on_top():
    """One body, enforced rather than hoped.

    The packaged skill.md serves anyone who installed from PyPI, the repo root
    SKILL.md serves agents working in a checkout, and both are the agents.md
    shim under a frontmatter trigger. If any of the three drift apart, the rule
    about one copy has quietly broken.
    """
    pkg = pathlib.Path(cli.__file__).parent
    repo = pathlib.Path(__file__).parents[1]
    shipped = (pkg / "skill.md").read_text(encoding="utf-8")
    assert shipped == (repo / "SKILL.md").read_text(encoding="utf-8")
    assert shipped.endswith((pkg / "agents.md").read_text(encoding="utf-8"))
    assert shipped.startswith("---\n")  # the trigger a harness keys on
    # Strict YAML reads an unquoted ": " inside a value as a nested mapping, and
    # skills.sh parses strictly: a colon in the description made `npx skills add`
    # skip the whole file with "Nested mappings are not allowed".
    for line in shipped.split("---\n")[1].splitlines():
        assert ": " not in line.split(": ", 1)[1], f"strict-YAML trap in: {line}"
