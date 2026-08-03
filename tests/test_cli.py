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


def test_an_exhausted_walk_falls_back_to_an_ephemeral_port(monkeypatch):
    """Forty viewers is not a reason to refuse to start (issue #55)."""
    monkeypatch.setattr(cli, "_is_free", lambda port: False)
    port = cli._pick_port(None)
    assert port not in range(cli.DEFAULT_PORT, cli.DEFAULT_PORT + 40)
    assert port > 0


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
    cli.cmd_verify(argparse.Namespace(part=None, report=False))  # passes first
    assert "ok," in capsys.readouterr().out

    md = part.with_suffix(".md")
    md.write_text(md.read_text().replace("Size:", "Size: TAMPERED", 1))
    with pytest.raises(SystemExit) as exc:
        cli.cmd_verify(argparse.Namespace(part=None, report=False))
    assert exc.value.code == 1
    assert "card disagrees with the geometry" in capsys.readouterr().out


def test_verify_report_survives_a_missing_browser(tmp_path, monkeypatch, capsys):
    """The report is the verdict and the renders are its evidence; without Playwright
    the evidence is missing and the report says so, instead of the command dying."""
    import argparse

    from nurb import render
    from nurb.builder import BuildError

    monkeypatch.chdir(tmp_path)
    _finished(tmp_path)

    def refuse(root, shots, timeout=30000):
        raise BuildError("no browser here")

    monkeypatch.setattr(render, "snapshots", refuse)
    cli.cmd_verify(argparse.Namespace(part=None, report=True))
    text = (tmp_path / "build" / "renders" / "thing.verify.md").read_text(encoding="utf-8")
    assert "No renders this time" in text
    assert "clean: no findings" in text
    assert "![" not in text  # no links to pictures that were never written


THIN = "from nurb import *\n\n\n@part\ndef thing(w=10.0, draft=False):\n    return Box(w, w, 0.5)\n"


def test_verify_report_pictures_each_finding(tmp_path, monkeypatch, capsys):
    """Every finding that sits on a face gets a still standing at that face, and the
    report embeds it next to the finding's own line."""
    import argparse

    from nurb import render

    monkeypatch.chdir(tmp_path)
    _finished(tmp_path, source=THIN)  # a plate under the printable wall
    renders = tmp_path / "build" / "renders"
    renders.mkdir(parents=True)
    stale = renders / "thing.finding-9.png"
    stale.touch()  # a still of a finding a previous run had and this one will not
    taken = []

    def pretend(root, shots, timeout=30000):
        taken.extend(shots)
        for s in shots:
            pathlib.Path(s["file"]).parent.mkdir(parents=True, exist_ok=True)
            pathlib.Path(s["file"]).touch()
        return [pathlib.Path(s["file"]) for s in shots]

    monkeypatch.setattr(render, "snapshots", pretend)
    with pytest.raises(SystemExit):  # the findings are still failures
        cli.cmd_verify(argparse.Namespace(part=None, report=True))
    text = (renders / "thing.verify.md").read_text(encoding="utf-8")
    assert "![finding 1](thing.finding-1.png)" in text
    names = {s["file"].name for s in taken}
    assert {"thing.verify.png", "thing.verify.section.png", "thing.finding-1.png"} <= names
    finding = next(s for s in taken if s["file"].name == "thing.finding-1.png")
    assert finding["check"], "the still would carry no marks without the check pass"
    assert finding["view"] not in ("iso", None), "the camera never moved to the face"
    assert not stale.exists(), "the stale still kept claiming a finding that is gone"


def test_verify_says_what_it_cannot_check(tmp_path, monkeypatch, capsys):
    """Two of the doctrine's six items need a human, and hiding that is worse."""
    import argparse

    parts = tmp_path / "parts"
    parts.mkdir()
    (parts / "thing.py").write_text(PLAIN)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        cli.cmd_verify(argparse.Namespace(part=None, report=False))
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
        cli.cmd_verify(argparse.Namespace(part=None, report=False))
    assert "no generated block yet" in capsys.readouterr().out


def test_verify_names_the_counts_it_flexed(tmp_path, monkeypatch, capsys):
    """"0 flexes" reads like a pass and means the sweep never ran."""
    import argparse

    monkeypatch.chdir(tmp_path)
    _finished(tmp_path, "from nurb import *\n\n\n@part\n"
                        "def thing(rows=2, w=10.0, draft=False):\n"
                        "    return Box(w, w, w * rows)\n")
    capsys.readouterr()
    cli.cmd_verify(argparse.Namespace(part=None, report=False))
    assert "flexed rows" in capsys.readouterr().out


def test_verify_says_so_when_a_part_has_no_counts_to_flex(tmp_path, monkeypatch, capsys):
    import argparse

    monkeypatch.chdir(tmp_path)
    _finished(tmp_path)
    capsys.readouterr()
    cli.cmd_verify(argparse.Namespace(part=None, report=False))
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


def test_the_first_part_brings_the_launcher(tmp_path, monkeypatch):
    """Project birth is the only moment it appears on its own; deleting it sticks."""
    monkeypatch.chdir(tmp_path)
    cli.main(["new", "one"])
    launcher = tmp_path / "viewer.command"
    assert launcher.exists()
    launcher.unlink()
    cli.main(["new", "two"])
    assert not launcher.exists()


def test_launcher_is_an_executable_that_runs_dev(tmp_path, monkeypatch):
    """Double-clickable from Finder: executable, login shell, lands on `nurb dev --open`."""
    import os

    (tmp_path / "parts").mkdir()
    monkeypatch.chdir(tmp_path)
    cli.main(["launcher"])
    file = tmp_path / "viewer.command"
    text = file.read_text()
    assert text.startswith("#!/bin/zsh -l\n")
    assert "nurb dev --open" in text
    assert os.access(file, os.X_OK)


def test_export_reads_the_projects_formats(tmp_path, monkeypatch):
    """printer.toml's [export] table is the standing preference; the flag still wins."""
    import argparse

    parts = tmp_path / "parts"
    parts.mkdir()
    (parts / "thing.py").write_text(PLAIN)
    (tmp_path / "printer.toml").write_text('[export]\nformats = ["stl", "step"]\n')
    monkeypatch.chdir(tmp_path)
    cli.cmd_export(argparse.Namespace(part=None, formats=None))
    assert (tmp_path / "build" / "thing.stl").exists()
    assert (tmp_path / "build" / "thing.step").exists()
    (tmp_path / "build" / "thing.step").unlink()
    cli.cmd_export(argparse.Namespace(part=None, formats=["stl"]))
    assert not (tmp_path / "build" / "thing.step").exists()


def test_export_flags_the_formats_it_left_stale(tmp_path, monkeypatch, capsys):
    """An old STEP sitting next to a fresh STL looks current, and sharing it as
    current is the upgrade trap of the STL-only default. The export says so."""
    import argparse

    parts = tmp_path / "parts"
    parts.mkdir()
    (parts / "thing.py").write_text(PLAIN)
    monkeypatch.chdir(tmp_path)
    cli.cmd_export(argparse.Namespace(part=None, formats=["stl", "step"]))
    capsys.readouterr()
    cli.cmd_export(argparse.Namespace(part=None, formats=["stl"]))
    out = capsys.readouterr().out
    assert "thing.step" in out
    assert "not rewritten" in out


def _global_config(text):
    from nurb.checks import global_file

    global_file().parent.mkdir(parents=True, exist_ok=True)
    global_file().write_text(text)


def test_export_falls_back_to_the_global_formats(tmp_path, monkeypatch):
    """The global config covers projects that say nothing; printer.toml still wins."""
    import argparse

    parts = tmp_path / "parts"
    parts.mkdir()
    (parts / "thing.py").write_text(PLAIN)
    _global_config('[export]\nformats = ["stl", "step"]\n')
    monkeypatch.chdir(tmp_path)
    cli.cmd_export(argparse.Namespace(part=None, formats=None))
    assert (tmp_path / "build" / "thing.step").exists()
    (tmp_path / "build" / "thing.step").unlink()
    (tmp_path / "printer.toml").write_text('[export]\nformats = ["stl"]\n')
    cli.cmd_export(argparse.Namespace(part=None, formats=None))
    assert not (tmp_path / "build" / "thing.step").exists()


def test_check_says_where_the_printer_came_from(tmp_path, monkeypatch, capsys):
    """A profile picked up from a file is invisible without this line, and invisible
    is how two machines check the same part differently for no stated reason."""
    parts = tmp_path / "parts"
    parts.mkdir()
    (parts / "thing.py").write_text(PLAIN)
    _global_config('profile = "bambu_a1_mini"\n')
    monkeypatch.chdir(tmp_path)
    cli.main(["check"])
    assert "printer: bambu_a1_mini (global)" in capsys.readouterr().out
    (tmp_path / "printer.toml").write_text('profile = "prusa_mk4s"\n')
    cli.main(["check"])
    assert "printer: prusa_mk4s (printer.toml)" in capsys.readouterr().out


def test_stl_is_meshed_for_printing_not_archival(tmp_path):
    """build123d's 1e-3mm default made a 145x364mm tray 97k triangles (issue #55).

    Fresh shapes per export, because OCCT caches the triangulation on the shape and
    an export at a coarser tolerance silently reuses an existing finer mesh.
    """
    from build123d import Cylinder, export_stl

    from nurb import builder

    export_stl(Cylinder(20, 40), str(tmp_path / "default.stl"))
    builder.write_stl(Cylinder(20, 40), tmp_path / "ours.stl")
    assert builder.stl_triangles(tmp_path / "ours.stl") < builder.stl_triangles(
        tmp_path / "default.stl"
    )


def test_the_shim_promises_what_export_actually_writes():
    shim = (pathlib.Path(cli.__file__).parent / "agents.md").read_text(encoding="utf-8")
    assert "STL into build/" in shim
    assert list(cli.DEFAULT_FORMATS) == ["stl"]


# --- the agent skill ----------------------------------------------------------


def test_skill_output_is_the_shipped_file(capsys):
    cli.main(["skill"])
    printed = capsys.readouterr().out
    shipped = (pathlib.Path(cli.__file__).parent / "skill.md").read_text(encoding="utf-8")
    assert printed.strip() == shipped.strip()
    assert "nurb rules" in printed  # a shim points at the doctrine, never copies it


def test_the_skill_is_the_shim_with_a_trigger_on_top():
    """One body, enforced rather than hoped.

    The packaged skill.md serves anyone who installed from PyPI, the repo copy in
    skills/nurb/ serves `npx skills add`, and both are the agents.md shim under a
    frontmatter trigger. If any of the three drift apart, the rule about one copy
    has quietly broken. The repo copy lives in skills/nurb/ rather than the root
    because skills.sh installs the whole directory containing SKILL.md: at the
    root, `npx skills add` copied the entire repo.
    """
    pkg = pathlib.Path(cli.__file__).parent
    repo = pathlib.Path(__file__).parents[1]
    shipped = (pkg / "skill.md").read_text(encoding="utf-8")
    assert shipped == (repo / "skills" / "nurb" / "SKILL.md").read_text(encoding="utf-8")
    assert shipped.endswith((pkg / "agents.md").read_text(encoding="utf-8"))
    assert shipped.startswith("---\n")  # the trigger a harness keys on
    # Strict YAML reads an unquoted ": " inside a value as a nested mapping, and
    # skills.sh parses strictly: a colon in the description made `npx skills add`
    # skip the whole file with "Nested mappings are not allowed".
    for line in shipped.split("---\n")[1].splitlines():
        _, separator, value = line.partition(": ")
        if separator:
            assert ": " not in value, f"strict-YAML trap in: {line}"


def test_skill_frontmatter_version_is_the_package_version():
    """The frontmatter version is what `nurb dev` compares an installed copy against,
    so a release that bumps pyproject.toml without regenerating the skill files must
    go red here rather than ship a check that never fires."""
    import tomllib

    repo = pathlib.Path(__file__).parents[1]
    version = tomllib.loads((repo / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    shipped = (pathlib.Path(cli.__file__).parent / "skill.md").read_text(encoding="utf-8")
    frontmatter = shipped.split("---\n")[1].splitlines()
    assert "metadata:" in frontmatter
    assert f'  version: "{version}"' in frontmatter


def test_skill_sync_rewrites_a_stale_copy_and_writes_the_shared_one_once(tmp_path, monkeypatch, capsys):
    """skills.sh symlinks every harness at one universal copy; sync must not report it twice."""
    monkeypatch.setenv("HOME", str(tmp_path))
    packaged = (pathlib.Path(cli.__file__).parent / "skill.md").read_text(encoding="utf-8")
    universal = tmp_path / ".agents" / "skills" / "nurb"
    universal.mkdir(parents=True)
    (universal / "SKILL.md").write_text("stale", encoding="utf-8")
    claude = tmp_path / ".claude" / "skills" / "nurb"
    claude.mkdir(parents=True)
    (claude / "SKILL.md").symlink_to(universal / "SKILL.md")
    cli.main(["skill", "--sync"])
    out = capsys.readouterr().out
    assert (universal / "SKILL.md").read_text(encoding="utf-8") == packaged
    assert (claude / "SKILL.md").is_symlink()
    assert out.count("skills/nurb") == 1
    assert "updated" in out


def test_skill_sync_leaves_a_current_copy_alone(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    packaged = (pathlib.Path(cli.__file__).parent / "skill.md").read_text(encoding="utf-8")
    claude = tmp_path / ".claude" / "skills" / "nurb"
    claude.mkdir(parents=True)
    (claude / "SKILL.md").write_text(packaged, encoding="utf-8")
    cli.main(["skill", "--sync"])
    assert "current" in capsys.readouterr().out


def test_skill_sync_with_nothing_installed_points_at_the_installer(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    cli.main(["skill", "--sync"])
    assert "npx skills add shpigford/nurb" in capsys.readouterr().out
