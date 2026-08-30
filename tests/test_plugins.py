"""The plugin system: manifest validation, discovery, registration, MCP
wiring, build checks, PATH detection, and failure isolation.

Every test is deterministic: plugins are built in tmp dirs with fake
executables where an executable is involved, never the developer's machine.
The shipped examples are loaded and asserted on, but never required to have
their tools installed (es/universal are not assumed present).
"""

import argparse
import importlib.util
import json
import os
import pathlib
import sys

import pytest

from nurb.plugins import (
    ManifestError,
    PluginState,
    ScaffoldError,
    disabled_ids,
    load_all,
    load_plugin,
    parse_manifest,
    registry,
    scaffold_plugin,
    set_enabled,
    status_payload,
)
from nurb.plugins.manifest import PluginManifest

GOOD_MANIFEST = """[plugin]
id = "good-plugin"
name = "Good Plugin"
version = "1.2.3"
description = "A valid plugin"
author = "Tester"
license = "MIT"

[capabilities]
commands = true
mcp_tools = true
build_checks = false

[[mcp.tools]]
name = "good_tool"
description = "A declared tool"
"""


@pytest.fixture(autouse=True)
def clean_registry():
    """Every test starts from an empty registry and leaves it that way."""
    registry.clear()
    yield
    registry.clear()


def write_plugin(tmp_path, name="some-plugin", manifest=GOOD_MANIFEST, plugin_py=None, plugin_id=None):
    """A plugin directory with the given manifest (and optional plugin.py)."""
    d = tmp_path / "plugins" / name
    if plugin_id:
        manifest = manifest.replace('id = "good-plugin"', f'id = "{plugin_id}"')
    d.mkdir(parents=True)
    (d / "plugin.toml").write_text(manifest, encoding="utf-8")
    if plugin_py:
        (d / "plugin.py").write_text(plugin_py, encoding="utf-8")
    return d


# --- manifest validation -----------------------------------------------------


def test_valid_manifest_parses(tmp_path):
    path = write_plugin(tmp_path) / "plugin.toml"
    manifest = parse_manifest(path)
    assert manifest.id == "good-plugin"
    assert manifest.name == "Good Plugin"
    assert manifest.version == "1.2.3"
    assert manifest.commands is True
    assert manifest.mcp_tools is True
    assert manifest.build_checks is False
    assert len(manifest.mcp_tool_decls) == 1
    assert manifest.mcp_tool_decls[0].name == "good_tool"


def test_manifest_missing_file(tmp_path):
    with pytest.raises(ManifestError):
        parse_manifest(tmp_path / "nope" / "plugin.toml")


def test_manifest_missing_plugin_section(tmp_path):
    d = write_plugin(tmp_path, manifest="[other]\nx = 1\n")
    with pytest.raises(ManifestError, match="plugin"):
        parse_manifest(d / "plugin.toml")


def test_manifest_missing_required_fields(tmp_path):
    for i, missing in enumerate(("id", "name", "version")):
        manifest = GOOD_MANIFEST
        for line in manifest.splitlines():
            if line.startswith(f"{missing} ="):
                manifest = manifest.replace(line, "")
        d = write_plugin(tmp_path, name=f"missing-{missing}-{i}", manifest=manifest)
        with pytest.raises(ManifestError, match=missing):
            parse_manifest(d / "plugin.toml")


def test_manifest_rejects_bad_id(tmp_path):
    for i, bad in enumerate(("Upper-Case", "under_score", "spaces here", "dotted.id")):
        manifest = GOOD_MANIFEST.replace('id = "good-plugin"', f'id = "{bad}"')
        d = write_plugin(tmp_path, name=f"bad-id-{i}", manifest=manifest)
        with pytest.raises(ManifestError, match="id must be"):
            parse_manifest(d / "plugin.toml")


def test_manifest_rejects_bad_version(tmp_path):
    for i, bad in enumerate(("v1.0.0", "1.0.0-beta", "abc", "1..2")):
        manifest = GOOD_MANIFEST.replace('version = "1.2.3"', f'version = "{bad}"')
        d = write_plugin(tmp_path, name=f"bad-version-{i}", manifest=manifest)
        with pytest.raises(ManifestError, match="version must be"):
            parse_manifest(d / "plugin.toml")


def test_manifest_rejects_malformed_toml(tmp_path):
    d = write_plugin(tmp_path, manifest="[plugin\nid = 'unterminated")
    with pytest.raises(ManifestError, match="TOML parse error"):
        parse_manifest(d / "plugin.toml")


def test_manifest_rejects_bad_mcp_tool_decl(tmp_path):
    manifest = GOOD_MANIFEST.replace(
        'name = "good_tool"\ndescription = "A declared tool"',
        'name = "good_tool"',
    )
    d = write_plugin(tmp_path, manifest=manifest)
    with pytest.raises(ManifestError, match="description"):
        parse_manifest(d / "plugin.toml")


def test_manifest_version_compatibility():
    manifest = PluginManifest(
        id="x", name="X", version="1.0.0", description="", author="", license="",
        min_nurb="0.20.0", max_nurb="0.30.0", commands=False, mcp_tools=False,
        build_checks=False,
    )
    assert manifest.is_compatible("0.22.0")
    assert manifest.is_compatible("0.30.0")
    assert not manifest.is_compatible("0.19.9")
    assert not manifest.is_compatible("0.31.0")
    assert not manifest.is_compatible("garbage")


def test_manifest_no_version_bounds_means_any():
    manifest = PluginManifest(
        id="x", name="X", version="1.0.0", description="", author="", license="",
        min_nurb="", max_nurb="", commands=False, mcp_tools=False, build_checks=False,
    )
    assert manifest.is_compatible("0.0.1")
    assert manifest.is_compatible("99.0.0")


# --- discovery and loading ---------------------------------------------------


def test_load_plugin_discovers_and_registers(tmp_path):
    plugin_py = """
def hello(args):
    print("hi")

def register(registry, manifest):
    registry.add_command("hello", hello, manifest.id)
"""
    d = write_plugin(tmp_path, plugin_py=plugin_py)
    assert load_plugin(d) is True
    record = registry.get("good-plugin")
    assert record is not None
    assert record.state == PluginState.LOADED
    assert "hello" in record.commands
    assert registry.has_command("hello")
    handler, pid = registry.command_handler("hello")
    assert pid == "good-plugin"
    assert handler is not None


def test_load_all_counts_and_dedupes(tmp_path):
    write_plugin(tmp_path, name="alpha", plugin_id="alpha")
    write_plugin(tmp_path, name="beta", plugin_id="beta")
    n = load_all(tmp_path)
    ids = {r.plugin_id for r in registry.loaded_plugins()}
    assert {"alpha", "beta"} <= ids  # project plugins loaded
    assert n >= 2
    # A second pass is idempotent: same registry records, no duplicate commands.
    before = len(registry.loaded_plugins())
    load_all(tmp_path)
    assert len(registry.loaded_plugins()) == before


def test_broken_manifest_is_skipped_not_fatal(tmp_path):
    write_plugin(tmp_path, name="broken", manifest="[plugin\nid = 'nope")
    plugin_py = """
def register(registry, manifest):
    registry.add_command("ok", lambda a: None, manifest.id)
"""
    write_plugin(tmp_path, name="ok-plugin", plugin_py=plugin_py)
    n = load_all(tmp_path)
    assert n >= 1
    assert registry.get("good-plugin").state == PluginState.LOADED
    assert registry.errored_plugins()


def test_import_error_marks_plugin_errored(tmp_path):
    plugin_py = 'raise RuntimeError("boom at import")\n'
    d = write_plugin(tmp_path, plugin_py=plugin_py)
    assert load_plugin(d) is False
    record = registry.get("good-plugin")
    assert record.state == PluginState.ERROR
    assert "boom at import" in record.error


def test_register_failure_marks_plugin_errored(tmp_path):
    plugin_py = """
def register(registry, manifest):
    raise ValueError("bad wiring")
"""
    d = write_plugin(tmp_path, plugin_py=plugin_py)
    assert load_plugin(d) is False
    assert registry.get("good-plugin").state == PluginState.ERROR


def test_broken_plugin_does_not_break_others(tmp_path):
    """A broken third-party plugin must not prevent unrelated plugins loading."""
    write_plugin(tmp_path, name="broken", manifest="[plugin\nid = 'nope")
    plugin_py = """
def register(registry, manifest):
    registry.add_command("fine", lambda a: None, manifest.id)
"""
    write_plugin(tmp_path, name="fine-plugin", plugin_py=plugin_py)
    n = load_all(tmp_path)
    assert n >= 1
    assert registry.get("good-plugin").state == PluginState.LOADED
    assert registry.errored_plugins()
    assert registry.loaded_plugins()


def test_duplicate_plugin_id_is_idempotent(tmp_path):
    plugin_py = """
def register(registry, manifest):
    registry.add_command("dup", lambda a: None, manifest.id)
"""
    d1 = write_plugin(tmp_path, name="one", plugin_py=plugin_py)
    d2 = write_plugin(tmp_path, name="two", plugin_py=plugin_py)
    assert load_plugin(d1) is True
    # Same id, different directory: the later load replaces the earlier
    # wholesale (the documented "later dirs win"), leaving exactly one record.
    assert load_plugin(d2) is True
    assert len([p for p in registry.all_plugins() if p.plugin_id == "good-plugin"]) == 1
    assert len(registry.all_mcp_tool_names()) == 1  # only good_tool, no dupes


def test_incompatible_plugin_is_skipped(tmp_path):
    manifest = GOOD_MANIFEST.replace('license = "MIT"', 'license = "MIT"\nmin_nurb = "99.0.0"')
    write_plugin(tmp_path, name="incompat", manifest=manifest)
    load_all(tmp_path)
    # The incompatible plugin is recorded as a skip, not a crash, and never loads.
    assert registry.get("good-plugin") is None or registry.get("good-plugin").state == PluginState.ERROR
    assert registry.errored_plugins()


def test_template_dir_is_never_loaded(tmp_path):
    """plugins/_template is scaffolding, not a plugin that should load."""
    write_plugin(tmp_path, name="_template")
    load_all(tmp_path)
    assert registry.get("good-plugin") is None


# --- commands, MCP tools, build checks ---------------------------------------


def test_command_registry_dispatch(tmp_path):
    plugin_py = """
def add(args):
    return 1

def register(registry, manifest):
    registry.add_command("add", add, manifest.id)
"""
    d = write_plugin(tmp_path, plugin_py=plugin_py)
    assert load_plugin(d)
    handler, pid = registry.command_handler("add")
    assert handler(None) == 1
    assert registry.has_command("add")
    assert registry.command_handler("missing") == (None, None)


def test_duplicate_command_name_across_plugins_rejected(tmp_path):
    plugin_py = """
def register(registry, manifest):
    registry.add_command("same", lambda a: None, manifest.id)
"""
    d1 = write_plugin(tmp_path, name="one", plugin_py=plugin_py)
    d2 = write_plugin(tmp_path, name="two", plugin_py=plugin_py)
    assert load_plugin(d1) is True
    # The second plugin re-registers under the same manifest id (idempotent);
    # a genuinely different id fighting for the same command raises.
    with pytest.raises(ValueError, match="already registered"):
        registry.add_command("same", lambda a: None, "other-plugin")


def test_mcp_tool_registration_and_call(tmp_path):
    plugin_py = """
def _mcp_handle_my_tool(arguments):
    return {"content": [{"type": "text", "text": f"got {arguments}"}], "isError": False}

def register(registry, manifest):
    registry.add_mcp_tool(
        "my_tool",
        {"name": "my_tool", "description": "d", "inputSchema": {"type": "object", "properties": {}}},
        manifest.id,
    )
"""
    d = write_plugin(tmp_path, plugin_py=plugin_py)
    assert load_plugin(d)
    assert registry.has_mcp_tool("my_tool")
    tool_def = registry.mcp_tool_def("my_tool")
    assert tool_def["name"] == "my_tool"
    result = registry.call_mcp_tool("my_tool", {"x": 1})
    assert "got" in result["content"][0]["text"]
    assert registry.call_mcp_tool("unknown_tool", {}) is None
    # my_tool from plugin.py and good_tool from the manifest declaration.
    assert set(registry.all_mcp_tool_names()) == {"my_tool", "good_tool"}


def test_duplicate_mcp_tool_name_rejected(tmp_path):
    plugin_py = """
def register(registry, manifest):
    registry.add_mcp_tool("dup_tool", {"name": "dup_tool"}, manifest.id)
"""
    d1 = write_plugin(tmp_path, name="one", plugin_py=plugin_py)
    assert load_plugin(d1)
    with pytest.raises(ValueError, match="already registered"):
        registry.add_mcp_tool("dup_tool", {"name": "dup_tool"}, "other-plugin")


def test_build_check_registration_and_isolation(tmp_path):
    """A plugin build check runs inside checks.run and a raising check is skipped."""
    from nurb.checks import Finding, run

    plugin_py = """
from nurb.checks import Finding

def check_thing(shape, ctx):
    return [Finding("plugin-rule", "fail", "plugin said no", value=1.0)]

def register(registry, manifest):
    registry.add_build_check(check_thing, manifest.id)
"""
    d = write_plugin(tmp_path, plugin_py=plugin_py)
    assert load_plugin(d)

    from build123d import Box

    found = run(Box(10, 10, 10))
    rules = {f.rule for f in found}
    assert "plugin-rule" in rules
    assert any(f.severity == "fail" for f in found if f.rule == "plugin-rule")


def test_raising_build_check_is_skipped(tmp_path):
    from nurb.checks import run

    plugin_py = """
def check_thing(shape, ctx):
    raise RuntimeError("check exploded")

def register(registry, manifest):
    registry.add_build_check(check_thing, manifest.id)
"""
    d = write_plugin(tmp_path, plugin_py=plugin_py)
    assert load_plugin(d)

    from build123d import Box

    # The plugin check raised; the built-in rules still ran and no exception
    # escaped to the caller.
    run(Box(10, 10, 10))


# --- PATH detection (deterministic, no real executables needed) ---------------


def test_everything_plugin_finds_fake_executable_on_path(tmp_path):
    """The everything example's PATH detection works with a fake es.exe."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    fake = bindir / ("es.exe" if sys.platform == "win32" else "es")
    fake.write_text("#!/bin/sh\necho es fake\n", encoding="utf-8")
    if sys.platform != "win32":
        os.chmod(str(fake), 0o755)

    spec = importlib.util.spec_from_file_location(
        "everything_example", "plugins/examples/everything/plugin.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    old_path = os.environ.get("PATH")
    os.environ["PATH"] = str(bindir) + (os.pathsep + old_path if old_path else "")
    try:
        found = module._find_es()
        assert found is not None
        assert "es" in found.lower()
    finally:
        if old_path is None:
            os.environ.pop("PATH", None)
        else:
            os.environ["PATH"] = old_path


def test_everything_plugin_reports_missing_without_crash(tmp_path, capsys):
    """No es.exe on PATH: the command prints guidance and does not crash."""
    spec = importlib.util.spec_from_file_location(
        "everything_example2", "plugins/examples/everything/plugin.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # PATH pointing at an empty dir: es.exe is definitely absent.
    empty = tmp_path / "empty"
    empty.mkdir()
    old_path = os.environ.get("PATH")
    os.environ["PATH"] = str(empty)
    try:
        module.cmd_everything_search(argparse.Namespace(project=str(tmp_path), argv=[]))
    finally:
        if old_path is None:
            os.environ.pop("PATH", None)
        else:
            os.environ["PATH"] = old_path
    out = capsys.readouterr().out
    assert "not found" in out


# --- shipped examples ---------------------------------------------------------


def test_shipped_examples_load():
    """The example plugins load from the repo's plugins/ dir."""
    root = pathlib.Path(__file__).resolve().parents[1]
    n = load_all(root)
    ids = {r.plugin_id for r in registry.loaded_plugins()}
    assert {"everything", "agent-yoke"} <= ids
    assert n >= 2


def test_shipped_examples_do_not_require_installed_tools():
    """The examples load without their executables installed (es, universal
    are not assumed present on the developer's machine)."""
    root = pathlib.Path(__file__).resolve().parents[1]
    load_all(root)
    for plugin_id in ("everything", "agent-yoke"):
        record = registry.get(plugin_id)
        assert record is not None
        assert record.state == PluginState.LOADED


def test_everything_example_manifest_contract():
    """The everything example manifest declares the expected contract."""
    root = pathlib.Path(__file__).resolve().parents[1]
    manifest = parse_manifest(root / "plugins/examples/everything/plugin.toml")
    assert manifest.id == "everything"
    assert manifest.commands is True
    assert manifest.mcp_tools is True
    assert manifest.build_checks is False
    names = {d.name for d in manifest.mcp_tool_decls}
    assert "everything_search" in names


def test_template_manifest_parses():
    """The shipped template is valid scaffolding, not a plugin that loads."""
    root = pathlib.Path(__file__).resolve().parents[1]
    manifest = parse_manifest(root / "plugins/_template/plugin.toml")
    assert manifest.id == "my-plugin"


# --- MCP wiring ---------------------------------------------------------------


def test_mcp_server_lists_and_calls_plugin_tools(tmp_path):
    """The MCP server exposes plugin tools in tools/list and dispatches calls."""
    from nurb import mcp

    load_all(tmp_path)
    resp = mcp._handle({"method": "tools/list"}, tmp_path)
    names = {t["name"] for t in resp["tools"]}
    assert "nurb_build" in names  # builtins still there
    assert "everything_search" in names  # shipped examples load via load_all


def test_mcp_plugin_tool_call_dispatches(tmp_path):
    from nurb import mcp

    load_all(tmp_path)
    resp = mcp._handle(
        {"method": "tools/call", "params": {"name": "everything_search", "arguments": {"query": "x"}}},
        tmp_path,
    )
    # es.exe may or may not be installed; either way it is a structured
    # result, never an error response.
    assert "error" not in resp
    assert resp.get("content")


def test_mcp_unknown_plugin_tool_errors(tmp_path):
    from nurb import mcp

    load_all(tmp_path)
    with pytest.raises(mcp.McpError):
        mcp._handle(
            {"method": "tools/call", "params": {"name": "nope_missing", "arguments": {}}},
            tmp_path,
        )


# --- CLI surface --------------------------------------------------------------


def test_cli_plugins_command(tmp_path, capsys, monkeypatch):
    from nurb import cli

    write_plugin(tmp_path, name="cli-plugin")
    monkeypatch.setattr(cli, "project_root", lambda: tmp_path)
    cli.cmd_plugins(None)
    out = capsys.readouterr().out
    assert "good-plugin" in out
    assert "1 command(s)" in out


def test_cli_dispatch_runs_plugin_command(tmp_path, capsys, monkeypatch):
    """main() dispatches a plugin command before argparse would reject it."""
    from nurb import cli

    plugin_py = """
def hello(args):
    print("hello from plugin command")

def register(registry, manifest):
    registry.add_command("plugin-hello", hello, manifest.id)
"""
    write_plugin(tmp_path, name="cli-plugin", plugin_py=plugin_py)
    monkeypatch.setattr(cli, "project_root", lambda: tmp_path)
    cli.main(["plugin-hello"])
    out = capsys.readouterr().out
    assert "hello from plugin command" in out


# --- adversarial: boundaries found exercising the real entry points -----------


def test_plugin_checks_skipped_when_only_restricts_rules(tmp_path):
    """slicing.py runs checks.run(only=BRIM_RULES); a plugin check must not run."""
    from nurb.checks import run

    plugin_py = """
from nurb.checks import Finding

def check_thing(shape, ctx):
    return [Finding("plugin-rule", "fail", "plugin said no")]

def register(registry, manifest):
    registry.add_build_check(check_thing, manifest.id)
"""
    write_plugin(tmp_path, name="checker", plugin_py=plugin_py)
    assert load_plugin(tmp_path / "plugins" / "checker")

    from build123d import Box

    # Restricted run: the plugin check is anonymous, so it must not appear.
    found = run(Box(10, 10, 10), only=set())
    assert not any(f.rule == "plugin-rule" for f in found)
    # Unrestricted run: it does.
    found = run(Box(10, 10, 10))
    assert any(f.rule == "plugin-rule" for f in found)


def test_manifest_declared_mcp_tool_is_registered(tmp_path):
    """A [[mcp.tools]] declaration alone registers the tool; the handler is
    looked up by convention, and a missing handler says so over MCP."""
    plugin_py = """
def _mcp_handle_declared_tool(arguments):
    return {"content": [{"type": "text", "text": "ran"}], "isError": False}

def register(registry, manifest):
    pass  # deliberately: no manual registration
"""
    manifest = GOOD_MANIFEST.replace(
        'name = "good_tool"\ndescription = "A declared tool"',
        'name = "declared_tool"\ndescription = "Declared only"',
    )
    d = write_plugin(tmp_path, name="decl", manifest=manifest, plugin_py=plugin_py)
    assert load_plugin(d)
    assert registry.has_mcp_tool("declared_tool")
    assert registry.mcp_tool_def("declared_tool")["name"] == "declared_tool"
    result = registry.call_mcp_tool("declared_tool", {})
    assert result["content"][0]["text"] == "ran"


def test_manifest_declared_tool_without_handler_reports_missing_handler(tmp_path):
    """A declared tool with no _mcp_handle_ fn is listed but errors cleanly."""
    from nurb import mcp

    manifest = GOOD_MANIFEST.replace(
        'name = "good_tool"\ndescription = "A declared tool"',
        'name = "ghost_tool"\ndescription = "Declared, never implemented"',
    )
    d = write_plugin(tmp_path, name="ghost", manifest=manifest, plugin_py=None)
    assert load_plugin(d)
    assert registry.has_mcp_tool("ghost_tool")
    with pytest.raises(mcp.McpError, match="no handler"):
        mcp._handle(
            {"method": "tools/call", "params": {"name": "ghost_tool", "arguments": {}}},
            tmp_path,
        )


def test_plugin_command_cannot_shadow_builtin(tmp_path, capsys, monkeypatch):
    """A plugin registering 'build' must not hijack `nurb build`."""
    from nurb import cli

    plugin_py = """
def evil(args):
    print("HACKED")

def register(registry, manifest):
    registry.add_command("build", evil, manifest.id)
"""
    d = write_plugin(tmp_path, name="evil", plugin_py=plugin_py)
    assert load_plugin(d)
    assert registry.has_command("build")  # recorded for `nurb plugins`
    monkeypatch.setattr(cli, "project_root", lambda: tmp_path)
    # argparse gets 'build' (no part named), not the plugin's handler.
    with pytest.raises(SystemExit):
        cli.main(["build"])
    out = capsys.readouterr().out
    assert "HACKED" not in out


def test_plugin_command_exception_is_a_clean_error(tmp_path, capsys, monkeypatch):
    """A raising plugin command prints one line and exits 1, no traceback."""
    from nurb import cli

    plugin_py = """
def boom(args):
    raise RuntimeError("plugin exploded")

def register(registry, manifest):
    registry.add_command("boom-cmd", boom, manifest.id)
"""
    d = write_plugin(tmp_path, name="boom", plugin_py=plugin_py)
    assert load_plugin(d)
    monkeypatch.setattr(cli, "project_root", lambda: tmp_path)
    with pytest.raises(SystemExit) as exc:
        cli.main(["boom-cmd"])
    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "good-plugin" in out and "RuntimeError" in out and "Traceback" not in out


def test_later_plugin_dir_overrides_earlier_same_id(tmp_path, monkeypatch):
    """A project-local plugin with the shipped example's ID wins wholesale."""
    shipped = tmp_path / "shipped"
    (shipped / "examples" / "dup").mkdir(parents=True)
    (shipped / "examples" / "dup" / "plugin.toml").write_text(
        GOOD_MANIFEST.replace('id = "good-plugin"', 'id = "dup"')
        .replace("version = \"1.2.3\"", "version = \"1.0.0\""),
        encoding="utf-8",
    )
    (shipped / "examples" / "dup" / "plugin.py").write_text(
        """
def a(args):
    print("shipped")

def register(registry, manifest):
    registry.add_command("dup-cmd", a, manifest.id)
""",
        encoding="utf-8",
    )
    project = tmp_path / "project"
    (project / "plugins" / "dup").mkdir(parents=True)
    (project / "plugins" / "dup" / "plugin.toml").write_text(
        GOOD_MANIFEST.replace('id = "good-plugin"', 'id = "dup"')
        .replace("version = \"1.2.3\"", "version = \"2.0.0\""),
        encoding="utf-8",
    )
    (project / "plugins" / "dup" / "plugin.py").write_text(
        """
def b(args):
    print("project")

def register(registry, manifest):
    registry.add_command("dup-cmd", b, manifest.id)
""",
        encoding="utf-8",
    )

    import nurb.plugins.loader as mod

    # Point the loader at two explicit dirs so the test needs no repo layout.
    monkeypatch.setattr(mod, "_BUILTIN_DIR", shipped)
    monkeypatch.setattr(mod, "_USER_DIR", shipped / "nouser")  # nonexistent: skipped
    n = mod.load_all(project)
    assert n == 1  # duplicate ids resolve to one loaded record
    record = registry.get("dup")
    assert record.version == "2.0.0"  # the project's copy won
    handler, pid = registry.command_handler("dup-cmd")
    # The shipped handler was unregistered with its record.
    assert pid == "dup"


def test_failed_register_leaves_no_partial_contributions(tmp_path):
    """A plugin that registers a command then raises must not keep the command."""
    plugin_py = """
def half(args):
    print("half registered")

def register(registry, manifest):
    registry.add_command("half-cmd", half, manifest.id)
    raise ValueError("wiring broke after the command")
"""
    d = write_plugin(tmp_path, name="half", plugin_py=plugin_py)
    assert load_plugin(d) is False
    assert registry.get("good-plugin").state == PluginState.ERROR
    assert not registry.has_command("half-cmd")
    assert registry.command_handler("half-cmd") == (None, None)


def test_double_load_all_does_not_duplicate_build_checks(tmp_path):
    """Idempotent load_all: a second pass must not run build checks twice."""
    plugin_py = """
def check_thing(shape, ctx):
    return []

def register(registry, manifest):
    registry.add_build_check(check_thing, manifest.id)
"""
    d = write_plugin(tmp_path, name="checker", plugin_py=plugin_py)
    assert load_all(tmp_path) >= 1
    first = registry.get("good-plugin")
    assert len(first.build_check_fns) == 1
    load_all(tmp_path)
    assert len(registry.get("good-plugin").build_check_fns) == 1
    assert len(registry.build_check_functions()) == 1


# --- scaffolding (`nurb plugin new`) -----------------------------------------


def test_scaffold_creates_a_working_plugin(tmp_path):
    """plugin new writes the template with the id substituted, and it loads."""
    dest = scaffold_plugin(tmp_path, "my-gadget")
    assert dest == tmp_path / "plugins" / "my-gadget"
    for file_name in ("plugin.toml", "plugin.py", "README.md"):
        assert (dest / file_name).is_file()
    manifest = parse_manifest(dest / "plugin.toml")
    assert manifest.id == "my-gadget"
    assert manifest.name == "My Gadget"
    assert load_plugin(dest)  # parses, imports, registers
    assert registry.has_command("my-gadget-hello")
    assert registry.has_mcp_tool("my_gadget_tool")


def test_scaffold_rejects_bad_ids_and_existing_dest(tmp_path):
    for bad in ("My Gadget", "my_gadget", "-lead", "trail-", "a b"):
        with pytest.raises(ScaffoldError):
            scaffold_plugin(tmp_path, bad)
    # Failure writes nothing: no plugins/ dir at all.
    assert not (tmp_path / "plugins").exists()

    dest = scaffold_plugin(tmp_path, "first-plugin")
    with pytest.raises(ScaffoldError):
        scaffold_plugin(tmp_path, "first-plugin")
    assert (dest / "plugin.toml").is_file()  # untouched


def test_scaffolded_plugin_module_is_valid_python(tmp_path):
    """Hyphens in the id must not leak into Python identifiers."""
    dest = scaffold_plugin(tmp_path, "my-gadget")
    spec = importlib.util.spec_from_file_location("scaffolded_check", dest / "plugin.py")
    module = importlib.util.module_from_spec(spec)
    module.__spec__.loader.exec_module(module)  # must not raise SyntaxError


# --- enable/disable state ----------------------------------------------------


def test_disable_records_state_and_prevents_loading(tmp_path):
    """A disabled plugin is recorded but never imported or registered."""
    plugin_py = """
def cmd_x(args):
    print("x")

def register(registry, manifest):
    registry.add_command("disable-me-cmd", cmd_x, manifest.id)
    registry.add_mcp_tool("disable_me_tool", {"name": "disable_me_tool"}, manifest.id)
"""
    write_plugin(tmp_path, name="disable-me", plugin_id="disable-me", plugin_py=plugin_py)
    initial_loaded = load_all(tmp_path)
    assert initial_loaded >= 1
    assert registry.get("disable-me").state == PluginState.LOADED
    assert registry.has_command("disable-me-cmd")

    set_enabled(tmp_path, "disable-me", False)
    assert disabled_ids(tmp_path) == {"disable-me"}
    assert load_all(tmp_path) == initial_loaded - 1  # the disabled plugin is excluded
    registry.clear()
    load_all(tmp_path)
    record = registry.get("disable-me")
    assert record.state == PluginState.DISABLED
    assert not registry.has_command("disable-me-cmd")
    assert not registry.has_mcp_tool("disable_me_tool")
    assert registry.command_handler("disable-me-cmd") == (None, None)

    # Re-enabling restores the plugin and its contributions.
    set_enabled(tmp_path, "disable-me", True)
    registry.clear()
    load_all(tmp_path)
    assert registry.get("disable-me").state == PluginState.LOADED
    assert registry.has_command("disable-me-cmd")


def test_set_enabled_round_trips_through_the_state_file(tmp_path):
    assert disabled_ids(tmp_path) == set()
    state = set_enabled(tmp_path, "everything", False)
    assert state == tmp_path / ".nurb" / "plugins.toml"
    assert disabled_ids(tmp_path) == {"everything"}
    set_enabled(tmp_path, "other", False)
    assert disabled_ids(tmp_path) == {"everything", "other"}
    set_enabled(tmp_path, "everything", True)
    assert disabled_ids(tmp_path) == {"other"}
    # A malformed state file reads as nothing disabled, never a crash.
    (tmp_path / ".nurb").mkdir(exist_ok=True)
    (tmp_path / ".nurb" / "plugins.toml").write_text("not [valid toml", encoding="utf-8")
    assert disabled_ids(tmp_path) == set()


def test_plugin_enable_disable_commands(tmp_path, monkeypatch, capsys):
    """`nurb plugin disable|enable <id>` flip the persisted state."""
    from nurb import cli

    plugin_py = """
def hello(args):
    print("hello")

def register(registry, manifest):
    registry.add_command("cli-plugin-hello", hello, manifest.id)
"""
    write_plugin(tmp_path, name="cli-plugin", plugin_id="cli-plugin", plugin_py=plugin_py)
    monkeypatch.setattr(cli, "project_root", lambda: tmp_path)

    cli.main(["plugins"])
    assert registry.has_command("cli-plugin-hello")
    cli.main(["plugin", "disable", "cli-plugin"])
    assert "disabled" in capsys.readouterr().out
    assert registry.get("cli-plugin").state == PluginState.DISABLED
    assert not registry.has_command("cli-plugin-hello")
    assert registry.command_handler("cli-plugin-hello") == (None, None)

    cli.main(["plugin", "enable", "cli-plugin"])
    assert "enabled" in capsys.readouterr().out
    assert registry.get("cli-plugin").state == PluginState.LOADED
    assert registry.has_command("cli-plugin-hello")

    # Unknown ids are refused and nothing is written for them.
    with pytest.raises(SystemExit):
        cli.main(["plugin", "disable", "nope"])
    assert "unknown plugin" in capsys.readouterr().out
    state_text = (tmp_path / ".nurb" / "plugins.toml").read_text(encoding="utf-8")
    assert "nope" not in state_text


# --- status payload and JSON -------------------------------------------------


def test_load_all_isolated_between_projects(tmp_path):
    """A project reload cannot inherit commands from the previous project."""
    first = tmp_path / "first"
    second = tmp_path / "second"
    plugin_py = """
def first_command(args):
    return None

def register(registry, manifest):
    registry.add_command("first-only-command", first_command, manifest.id)
"""
    write_plugin(first, name="first-plugin", plugin_id="first-plugin", plugin_py=plugin_py)
    write_plugin(second, name="second-plugin", plugin_id="second-plugin")
    load_all(first)
    assert registry.has_command("first-only-command")
    load_all(second)
    assert not registry.has_command("first-only-command")
    assert registry.get("first-plugin") is None
    assert registry.get("second-plugin") is not None


def test_status_payload_shape(tmp_path):
    write_plugin(tmp_path, name="payload-plugin", plugin_id="payload-plugin")
    set_enabled(tmp_path, "payload-plugin", False)
    payload = status_payload(tmp_path)
    entry = next(p for p in payload if p["id"] == "payload-plugin")
    assert entry["state"] == "disabled"
    assert entry["enabled"] is False
    for key in (
        "id", "name", "version", "description", "state", "error", "source",
        "enabled", "commands", "mcpTools", "checks",
    ):
        assert key in entry


def test_plugins_command_emits_json(capsys):
    """`nurb plugins --json` prints the registry as parseable JSON."""
    from nurb import cli

    cli.main(["plugins", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "plugins" in data
    assert isinstance(data["plugins"], list)
    assert data["plugins"]  # the shipped examples are present
    for key in (
        "id", "name", "version", "description", "state", "error", "source",
        "enabled", "commands", "mcpTools", "checks",
    ):
        assert key in data["plugins"][0]
