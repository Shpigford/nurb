"""Configuration-set validation happens before artifact writes."""

import argparse
import pathlib
import re
import subprocess
import sys

import pytest

from nurb import __version__, cli


def test_version_command_does_not_import_the_cad_package(tmp_path, monkeypatch):
    blocked = tmp_path / "nurb"
    blocked.mkdir()
    (blocked / "__init__.py").write_text(
        'raise AssertionError("version command imported nurb")\n', encoding="utf-8"
    )
    monkeypatch.setenv("PYTHONPATH", str(tmp_path))
    result = subprocess.run(
        [pathlib.Path(sys.executable).with_name("nurb"), "--version"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout == f"nurb {__version__}\n"


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


def test_an_unasked_port_walks_past_one_that_is_busy(tmp_path):
    """A project is any directory with parts/, so two at once is the ordinary case."""
    import socket

    with socket.socket() as held:
        held.bind(("127.0.0.1", 0))
        held.listen()
        busy = held.getsockname()[1]
        assert cli._pick_port(None, tmp_path) != busy
        assert cli._is_free(busy) is False


def test_an_exhausted_walk_falls_back_to_an_ephemeral_port(monkeypatch, tmp_path):
    """Forty viewers is not a reason to refuse to start (issue #55)."""
    monkeypatch.setattr(cli, "_is_free", lambda port: False)
    monkeypatch.setattr(cli, "_serving", lambda port, root: None)
    port = cli._pick_port(None, tmp_path)
    assert port not in range(cli.DEFAULT_PORT, cli.DEFAULT_PORT + 40)
    assert port > 0


def test_asking_for_a_busy_port_is_an_error_not_a_suggestion(tmp_path):
    """`--port 7373` picking 7374 would open a tab onto somebody else's parts."""
    import socket

    with socket.socket() as held:
        held.bind(("127.0.0.1", 0))
        held.listen()
        busy = held.getsockname()[1]
        with pytest.raises(SystemExit) as exc:
            cli._pick_port(busy, tmp_path)
        assert str(busy) in str(exc.value.code)


def _fake_dev_server(root):
    """A thread answering /api/sync the way a running nurb dev does."""
    import http.server
    import json
    import threading

    body = json.dumps({"type": "sync", "root": str(root)}).encode()

    class Sync(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    httpd = http.server.HTTPServer(("127.0.0.1", 0), Sync)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def test_a_second_dev_for_the_same_project_refuses_with_the_running_url(monkeypatch, tmp_path):
    """Restarting `nurb dev` per turn is how an agent piles up viewer tabs (issue #102)."""
    httpd = _fake_dev_server(tmp_path)
    try:
        port = httpd.server_address[1]
        with pytest.raises(SystemExit) as exc:
            cli._pick_port(port, tmp_path)
        assert f"http://127.0.0.1:{port}" in str(exc.value.code)
        assert "already serving" in str(exc.value.code)
        # The unasked walk refuses too, rather than quietly binding the next port.
        monkeypatch.setattr(cli, "DEFAULT_PORT", port)
        with pytest.raises(SystemExit) as exc:
            cli._pick_port(None, tmp_path)
        assert "already serving" in str(exc.value.code)
    finally:
        httpd.shutdown()


def test_a_free_lower_port_does_not_hide_the_running_project(monkeypatch, tmp_path):
    """A stopped earlier project can leave a gap below this project's server."""
    base = cli.DEFAULT_PORT
    running = base + 1
    monkeypatch.setattr(cli, "_is_free", lambda port: port == base)
    monkeypatch.setattr(
        cli,
        "_serving",
        lambda port, root: f"http://127.0.0.1:{port}" if port == running else None,
    )

    with pytest.raises(SystemExit) as exc:
        cli._pick_port(None, tmp_path)

    assert f"http://127.0.0.1:{running}" in str(exc.value.code)


def test_a_dev_for_a_different_project_is_walked_past_not_reused(tmp_path):
    """The running URL is only an answer when it shows this project's parts."""
    httpd = _fake_dev_server(tmp_path / "other")
    try:
        port = httpd.server_address[1]
        assert cli._serving(port, tmp_path) is None
    finally:
        httpd.shutdown()


# --- day one ------------------------------------------------------------------


def _new(tmp_path, name="thing", root=None, embed=False):
    import argparse, os
    was = os.getcwd()
    os.chdir(tmp_path)
    try:
        cli.cmd_new(argparse.Namespace(name=name, root=root, embed=embed))
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
    # Claude Code does not read AGENTS.md, so fresh multi-agent projects also
    # carry its native pointer without duplicating the doctrine.
    assert (tmp_path / "CLAUDE.md").read_text(encoding="utf-8") == "@AGENTS.md\n"
    output = capsys.readouterr().out
    assert "AGENTS.md" in output  # it says what it wrote
    assert "CLAUDE.md" in output


def test_a_seeded_shim_never_carries_the_markers(tmp_path):
    _new(tmp_path)
    text = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "cli-only" not in text
    assert "Start `nurb dev`" in text
    assert "permission allowlist" in text
    assert "nurb skill --sync" in text
    assert "\n\n\n" not in text


def test_an_embedded_seed_drops_what_the_app_already_owns(tmp_path):
    """The desktop app runs the server, the updates and the permissions itself, so an
    agent told to do them there spends turns on work that is already done."""
    _new(tmp_path, embed=True)
    text = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "cli-only" not in text
    assert "Start `nurb dev`" not in text
    assert "nurb skill --sync" not in text
    assert "permission allowlist" not in text
    assert '"Bash(nurb:*)"' not in text
    assert "not on PATH" not in text
    assert "Run `nurb rules` before you design" in text
    assert "\n\n\n" not in text


def test_a_plain_new_replaces_an_exact_embedded_shim(tmp_path):
    _new(tmp_path, "one", embed=True)

    _new(tmp_path, "two")

    assert (tmp_path / "AGENTS.md").read_text(encoding="utf-8") == cli.agents_text()


def test_an_embedded_new_replaces_an_exact_plain_shim(tmp_path):
    _new(tmp_path, "one")

    _new(tmp_path, "two", embed=True)

    assert (tmp_path / "AGENTS.md").read_text(encoding="utf-8") == cli.agents_text(True)


def test_a_second_part_does_not_mention_the_shim_again(tmp_path, capsys):
    _new(tmp_path, "one")
    capsys.readouterr()
    _new(tmp_path, "two")
    output = capsys.readouterr().out
    assert "AGENTS.md" not in output
    assert "CLAUDE.md" not in output


def test_an_old_generated_agents_shim_gets_a_claude_pointer(tmp_path):
    from nurb import __file__ as pkg

    current = (pathlib.Path(pkg).parent / "agents.md").read_text(encoding="utf-8")
    shim = current.replace(
        "**Run `nurb rules` before you design.**",
        "**Run `nurb rules` before modelling.**",
    )
    assert shim != current
    (tmp_path / "AGENTS.md").write_text(shim, encoding="utf-8")

    _new(tmp_path)

    assert (tmp_path / "CLAUDE.md").read_text(encoding="utf-8") == "@AGENTS.md\n"


def test_a_custom_agents_file_does_not_grow_a_claude_pointer(tmp_path):
    custom = "# nurb\n\nOur workflow starts with `nurb rules`, then follows team policy.\n"
    (tmp_path / "AGENTS.md").write_text(custom, encoding="utf-8")

    _new(tmp_path)

    assert not (tmp_path / "CLAUDE.md").exists()
    assert (tmp_path / "AGENTS.md").read_text(encoding="utf-8") == custom


def test_an_explicit_root_never_seeds_an_ancestor_project(tmp_path):
    parent = tmp_path / "existing"
    child = parent / "new-project"
    (parent / "parts").mkdir(parents=True)
    child.mkdir()

    _new(child, "widget", root=child)

    assert (child / "parts" / "widget.py").is_file()
    assert not (parent / "parts" / "widget.py").exists()


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
    assert {"thing.verify.png", "thing.verify.back.png", "thing.verify.section.png", "thing.finding-1.png"} <= names
    finding = next(s for s in taken if s["file"].name == "thing.finding-1.png")
    assert finding["check"], "the still would carry no marks without the check pass"
    assert finding["view"] not in ("iso", None), "the camera never moved to the face"
    assert not stale.exists(), "the stale still kept claiming a finding that is gone"
    # The two overviews stand at opposite corners, so no face is unseen in both.
    back = next(s for s in taken if s["file"].name == "thing.verify.back.png")
    assert [float(v) for v in back["view"].split(",")] == [pytest.approx(-v) for v in cli.ISO]
    assert "![thing, from the opposite corner](thing.verify.back.png)" in text


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


def test_verify_accepts_a_designed_refusal_while_flexing_counts(
    tmp_path, monkeypatch, capsys
):
    import argparse

    monkeypatch.chdir(tmp_path)
    _finished(
        tmp_path,
        "from nurb import *\n\n\n@part\n"
        "def thing(rows=2):\n"
        "    if rows > 2:\n"
        "        reject('only two rows fit', param='rows')\n"
        "    return Box(10, 10, 5 * rows)\n",
    )
    capsys.readouterr()

    cli.cmd_verify(argparse.Namespace(part=None, report=False))

    assert "ok," in capsys.readouterr().out


def test_verify_reports_a_bare_value_error_while_flexing_counts(
    tmp_path, monkeypatch, capsys
):
    import argparse

    monkeypatch.chdir(tmp_path)
    _finished(
        tmp_path,
        "from nurb import *\n\n\n@part\n"
        "def thing(rows=2):\n"
        "    if rows > 2:\n"
        "        raise ValueError('only two rows fit')\n"
        "    return Box(10, 10, 5 * rows)\n",
    )
    capsys.readouterr()

    with pytest.raises(SystemExit):
        cli.cmd_verify(argparse.Namespace(part=None, report=False))

    assert "rows=3: ValueError: only two rows fit" in capsys.readouterr().out


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
    launcher = tmp_path / cli.LAUNCHER
    assert launcher.exists()
    launcher.unlink()
    cli.main(["new", "two"])
    assert not launcher.exists()


def test_launcher_is_an_executable_that_runs_dev(tmp_path, monkeypatch):
    """Double-clickable from Finder or Explorer: runnable, lands on `nurb dev --open`."""
    import os
    import sys

    (tmp_path / "parts").mkdir()
    monkeypatch.chdir(tmp_path)
    cli.main(["launcher"])
    file = tmp_path / cli.LAUNCHER
    text = file.read_text(encoding="utf-8")
    assert "nurb dev --open" in text
    if sys.platform == "win32":
        assert file.suffix == ".cmd"
        assert text.startswith("@echo off")
    else:
        assert text.startswith("#!/bin/zsh -l\n")
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


def test_3mf_writes_a_tessellation_with_a_crack_in_it(tmp_path, monkeypatch):
    """OCCT leaves the odd seam crack on a curved face, and build123d's Mesher refuses
    to write anything non-manifold: one four-edge hole used to kill the whole export
    with "3mf mesh is invalid". The STL carries the same holes and slicers repair them,
    so the 3MF writes too. A box missing a face stands in for the crack."""
    import trimesh
    import zipfile

    from build123d import Box

    from nurb import builder

    cracked = trimesh.creation.box(extents=(10, 10, 10))
    cracked.update_faces([i for i in range(len(cracked.faces)) if i > 1])
    assert not cracked.is_watertight, "the stand-in has to be the broken case"
    monkeypatch.setattr(builder, "to_mesh", lambda *a, **k: cracked)

    target = tmp_path / "cracked.3mf"
    builder.write_3mf(Box(10, 10, 10), target)

    with zipfile.ZipFile(target) as z:
        model = z.read("3D/3dmodel.model").decode()
    assert 'unit="millimeter"' in model
    assert model.count("<triangle ") == len(cracked.faces)


def test_3mf_refuses_a_part_that_tessellates_to_nothing(tmp_path):
    """lib3mf writes an empty model happily, and a download that opens to an empty
    plate reads as success. Say what happened instead, without leaving yesterday's
    printable artifact looking current."""
    from build123d import Box

    from nurb import builder

    target = tmp_path / "gone.3mf"
    target.write_bytes(b"stale 3mf")
    with pytest.raises(builder.BuildError) as exc:
        builder.write_3mf(Box(10, 10, 10) - Box(20, 20, 20), target)
    assert "no geometry" in str(exc.value)
    assert not target.exists(), "a refusal must not leave a file behind"


def test_export_reports_an_empty_3mf_without_a_traceback(tmp_path, monkeypatch):
    """The default exporter owns this expected refusal, so the command says it in
    one line rather than leaking the implementation stack to the user."""
    parts = tmp_path / "parts"
    parts.mkdir()
    (parts / "gone.py").write_text(
        "from nurb import *\n\n@part\ndef gone():\n"
        "    return Box(10, 10, 10) - Box(20, 20, 20)\n"
    )
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit) as exc:
        cli.main(["export"])

    assert "gone has no geometry to export" in str(exc.value)
    assert not (tmp_path / "build" / "gone.3mf").exists()


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
    assert "3MF with tuned print settings into build/" in shim
    assert "hit 3mf to print" in shim
    assert 'formats = ["3mf", "step"]' in shim
    assert "hit stl to print" not in shim
    assert list(cli.DEFAULT_FORMATS) == ["3mf"]

    readme = (pathlib.Path(__file__).parents[1] / "README.md").read_text(encoding="utf-8")
    assert "click `3mf`, print" in readme
    assert 'formats = ["3mf", "step"]' in readme


def test_export_defaults_to_a_3mf_that_says_millimeter(tmp_path, monkeypatch):
    """3MF is the default because it is what Bambu and Orca open natively, and unlike
    STL the file carries its unit, so a slicer never guesses the scale."""
    import argparse
    import zipfile

    parts = tmp_path / "parts"
    parts.mkdir()
    (parts / "thing.py").write_text(PLAIN)
    monkeypatch.chdir(tmp_path)
    cli.cmd_export(argparse.Namespace(part=None, formats=None))
    target = tmp_path / "build" / "thing.3mf"
    with zipfile.ZipFile(target) as z:
        model = z.read("3D/3dmodel.model").decode()
    assert 'unit="millimeter"' in model


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
    # agents.md carries the cli-only markers; the skill files carry the same body
    # with the markers taken out, because `nurb skill` prints them to a terminal.
    assert shipped.endswith(cli.agents_text())
    assert shipped.startswith("---\n")  # the trigger a harness keys on
    # Strict YAML reads an unquoted ": " inside a value as a nested mapping, and
    # skills.sh parses strictly: a colon in the description made `npx skills add`
    # skip the whole file with "Nested mappings are not allowed".
    for line in shipped.split("---\n")[1].splitlines():
        _, separator, value = line.partition(": ")
        if separator:
            assert ": " not in value, f"strict-YAML trap in: {line}"


def test_skill_allowlist_covers_the_shared_project_module():
    skill = (pathlib.Path(cli.__file__).parent / "skill.md").read_text(encoding="utf-8")
    assert '"Edit(system.py)"' in skill


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


def test_desktop_app_version_is_the_package_version():
    """The desktop app and the engine release together as one version: the DMG a
    user downloads and the wheel it provisions carry the same number, and the
    updater feed advertises engine releases. A pyproject bump without the matching
    tauri.conf.json bump must go red here rather than ship a mismatched pair."""
    import json
    import tomllib

    repo = pathlib.Path(__file__).parents[1]
    version = tomllib.loads((repo / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    conf = json.loads((repo / "desktop" / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8"))
    assert conf["version"] == version


def test_skill_sync_rewrites_a_stale_copy_and_writes_the_shared_one_once(tmp_path, monkeypatch, capsys):
    """skills.sh symlinks every harness at one universal copy; sync must not report it twice."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
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
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    packaged = (pathlib.Path(cli.__file__).parent / "skill.md").read_text(encoding="utf-8")
    claude = tmp_path / ".claude" / "skills" / "nurb"
    claude.mkdir(parents=True)
    (claude / "SKILL.md").write_text(packaged, encoding="utf-8")
    cli.main(["skill", "--sync"])
    assert "current" in capsys.readouterr().out


def test_skill_sync_with_nothing_installed_points_at_the_installer(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    cli.main(["skill", "--sync"])
    assert "npx skills add shpigford/nurb --skill nurb" in capsys.readouterr().out


# --- diff --------------------------------------------------------------------

RIBBED = """\
from nurb import *


@part
def thing(gap=8.0, draft=False):
    body = Box(60.0, 30.0, 6.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    for x in (-gap / 2, gap / 2):
        body += Pos(x, 0, 6.0) * Box(2.0, 30.0, 8.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    if draft:
        return body
    bed = body.bounding_box().min.Z
    keep = body.edges().filter_by(lambda e: e.bounding_box().min.Z > bed)
    return polish(body, keep, 1.0)
"""


def test_diff_wants_a_card_first(tmp_path, monkeypatch, capsys):
    import argparse

    monkeypatch.chdir(tmp_path)
    parts = tmp_path / "parts"
    parts.mkdir()
    (parts / "thing.py").write_text(PLAIN)
    cli.cmd_diff(argparse.Namespace(part=None))
    assert "nothing recorded yet" in capsys.readouterr().out


def test_diff_is_quiet_when_nothing_moved(tmp_path, monkeypatch, capsys):
    import argparse

    monkeypatch.chdir(tmp_path)
    _finished(tmp_path)
    cli.cmd_diff(argparse.Namespace(part=None))
    out = capsys.readouterr().out
    assert "unchanged since its card" in out
    assert "nurb card" not in out, "nothing to write back, so nothing to suggest"


def test_diff_catches_a_chamfer_that_stopped_landing(tmp_path, monkeypatch, capsys):
    """The whole reason the command exists.

    Closing the gap between two ribs leaves their chamfers no room, so `polish` drops
    them. The part still builds, the volume moves two tenths of a percent, and no check
    goes red: the face count is the only place it shows.
    """
    import argparse

    monkeypatch.chdir(tmp_path)
    part = _finished(tmp_path, source=RIBBED)
    part.write_text(RIBBED.replace("gap=8.0", "gap=3.2"))
    cli.cmd_diff(argparse.Namespace(part=None))
    out = capsys.readouterr().out
    # Not pinned to the counts themselves. How many chamfers a failing batch takes down
    # with it is OCCT's call, and it answers differently on macOS and on Linux: the same
    # part is 44 faces on one and something else on the other. What has to hold is that
    # faces fell and that nothing else in the line would have raised a hand.
    faces = re.search(r"faces: (\d+) -> (\d+)", out)
    assert faces, out
    assert int(faces[2]) < int(faces[1])
    volume = re.search(r"volume: [\d.]+ -> [\d.]+ mm3, ([-+][\d.]+)%", out)
    assert volume and abs(float(volume[1])) < 1.0, "volume barely moves, which is the point"
    assert "nurb card" in out, "the way to accept the new numbers is worth saying"


# --- slice -------------------------------------------------------------------


def test_a_profile_failure_removes_the_previous_gcode(tmp_path, monkeypatch):
    import argparse

    from nurb import slicing

    monkeypatch.chdir(tmp_path)
    parts = tmp_path / "parts"
    parts.mkdir()
    (parts / "thing.py").write_text(PLAIN)
    build = tmp_path / "build"
    build.mkdir()
    stale = build / "thing.gcode"
    stale.write_text("yesterday's print")
    monkeypatch.setattr(slicing, "app", lambda: tmp_path / "BambuStudio")
    monkeypatch.setattr(slicing, "vendors", lambda exe: tmp_path / "profiles")
    monkeypatch.setattr(
        slicing,
        "machine",
        lambda *args: (_ for _ in ()).throw(slicing.Unavailable("no matching nozzle")),
    )
    with pytest.raises(SystemExit) as exc:
        cli.cmd_slice(
            argparse.Namespace(
                part="thing",
                printer="bambu_a1_mini",
                nozzle=None,
                layer="0.20",
                filament="PLA",
                plate="Textured PEI Plate",
            )
        )
    assert exc.value.code == 1
    assert not stale.exists()


def test_a_missing_slicer_removes_the_previous_gcode(tmp_path, monkeypatch):
    from nurb import slicing

    monkeypatch.chdir(tmp_path)
    parts = tmp_path / "parts"
    parts.mkdir()
    (parts / "thing.py").write_text(PLAIN)
    build = tmp_path / "build"
    build.mkdir()
    stale = build / "thing.gcode"
    stale.write_text("yesterday's print")
    monkeypatch.setattr(slicing, "app", lambda: None)
    with pytest.raises(SystemExit):
        cli.main(["slice", "thing", "--printer", "bambu_a1_mini"])
    assert not stale.exists()


def test_stress_walks_variants_without_reusing_the_base_cards_coordinates(
    tmp_path, monkeypatch, capsys
):
    import argparse

    from nurb import stress

    monkeypatch.chdir(tmp_path)
    parts = tmp_path / "parts"
    parts.mkdir()
    part = parts / "thing.py"
    part.write_text(
        """from nurb import *

@part
def thing(width=10.0):
    return Box(width, 10, 5)
"""
    )
    part.with_suffix(".md").write_text(
        """# thing

```toml
[stress]
kg = 2
load = [0, 0, 2.5]
hold = [[-5, 0, 0]]

[variants.wide.params]
width = 20.0
```
"""
    )
    calls = []

    def analyze(shape, holds, load, kg, **kwargs):
        calls.append((shape.bounding_box().size.X, holds, load, kg, kwargs["material"]))
        return {
            "material": "PLA",
            "hold_centers": holds,
            "load_center": load,
            "max_mpa": 1,
            "hotspot": (0, 0, 0),
            "across_mpa": 0,
            "deflection_mm": 0,
            "factor": 2,
            "gives": "plastic",
        }

    monkeypatch.setattr(stress, "analyze", analyze)
    monkeypatch.setattr(stress, "default_spots", lambda shape: ([(9, 9, 9)], (8, 8, 8)))

    cli.cmd_stress(
        argparse.Namespace(
            part="thing",
            kg=None,
            at=None,
            hold=[],
            pitch=None,
            material=None,
        )
    )

    assert calls == [
        (10.0, [(-5.0, 0.0, 0.0)], (0.0, 0.0, 2.5), 2.0, "PLA"),
        (20.0, [(9, 9, 9)], (8, 8, 8), 2.0, "PLA"),
    ]
    output = capsys.readouterr().out
    assert "thing:" in output
    assert "wide:" in output


def test_build_says_when_the_geometry_did_not_move(tmp_path, monkeypatch, capsys):
    """The surface the agent sees: the build succeeded and the part is what it was."""
    import argparse

    monkeypatch.chdir(tmp_path)
    parts = tmp_path / "parts"
    parts.mkdir()
    part = parts / "thing.py"
    part.write_text(PLAIN)
    args = argparse.Namespace(part=None, draft=False)
    cli.cmd_build(args)
    assert "geometry unchanged" not in capsys.readouterr().out  # nothing to compare to
    part.write_text(PLAIN + "\n# a note, not a change\n")
    cli.cmd_build(args)
    assert "geometry unchanged since last build" in capsys.readouterr().out
    part.write_text(
        PLAIN.replace("return Box(w, w, w)", "return Pos(5, 0, 0) * Box(w, w, w)")
    )
    cli.cmd_build(args)
    assert "geometry unchanged" not in capsys.readouterr().out
    part.write_text(PLAIN.replace("w=10.0", "w=20.0"))
    cli.cmd_build(args)
    assert "geometry unchanged" not in capsys.readouterr().out


def test_build_fingerprints_same_named_variants_per_source(
    tmp_path, monkeypatch, capsys
):
    import argparse

    monkeypatch.chdir(tmp_path)
    parts = tmp_path / "parts"
    parts.mkdir()
    for name, width in (("one", 10), ("two", 20)):
        (parts / f"{name}.py").write_text(
            PLAIN.replace("thing", name).replace("w=10.0", f"w={width}.0")
        )
        (parts / f"{name}.md").write_text(
            f"""# {name}

```toml
[variants.shared.params]
w = {width + 1}.0
```
"""
        )
    args = argparse.Namespace(part=None, draft=False)
    cli.cmd_build(args)
    capsys.readouterr()

    cli.cmd_build(args)

    assert capsys.readouterr().out.count("geometry unchanged since last build") == 4


# --- supports and --strict ---------------------------------------------------


SLOTTED = '''from nurb import *


@part
def slot(span=44.0, height=40.0):
    """A slot wider than this printer bridges."""
    return Box(90, 20, height) - Pos(0, 0, -height / 2 + 10) * Box(span, 20, 16)
'''


def supports_project(tmp_path, declared):
    parts = tmp_path / "parts"
    parts.mkdir(parents=True, exist_ok=True)
    (parts / "slot.py").write_text(SLOTTED)
    card = "# slot\n\n## What it is\n\nA wide slot.\n"
    if declared:
        card += "\nThe span is set by what passes through it.\n\n```toml\n[part]\nsupports = true\n```\n"
    (parts / "slot.md").write_text(card)
    return tmp_path


def check_strict(monkeypatch, root, capsys):
    """`nurb check --strict`'s exit code, and what it printed."""
    monkeypatch.setattr(cli, "project_root", lambda *a, **k: root)
    args = argparse.Namespace(part=None, strict=True, printer=None)
    code = 0
    try:
        cli.cmd_check(args)
    except SystemExit as exc:
        code = exc.code
    return code, capsys.readouterr().out


def test_strict_fails_an_overhang_and_passes_it_once_declared(monkeypatch, tmp_path, capsys):
    undeclared, _ = check_strict(monkeypatch, supports_project(tmp_path / "a", False), capsys)
    assert undeclared == 1
    declared, out = check_strict(monkeypatch, supports_project(tmp_path / "b", True), capsys)
    assert declared == 0
    # The finding is still on screen, and the summary says where it went, because
    # "0 to fix" beside a listed finding reads like the checker is broken.
    assert "note  overhang" in out
    assert "1 on supports" in out


def test_verify_agrees_with_check_about_a_carried_overhang(monkeypatch, tmp_path, capsys):
    """The two commands judging the same geometry differently is worse than either
    of them being wrong, because there is no way to tell which to believe."""
    root = supports_project(tmp_path / "c", True)
    monkeypatch.setattr(cli, "project_root", lambda *a, **k: root)
    try:
        cli.cmd_verify(argparse.Namespace(part=None, report=False))
    except SystemExit as exc:
        assert exc.code in (0, 1)
    out = capsys.readouterr().out
    assert "note  overhang" not in out  # not listed as a problem to fix
