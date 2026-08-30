"""Plugin manifest parsing and validation.

A manifest is a TOML file named ``plugin.toml`` in a plugin directory.  Every
field is validated on load; malformed manifests raise ``ManifestError`` with
enough context to diagnose the problem.

Schema version 1 fields:

    [plugin]
    id              = "my-plugin"        # required, unique, lowercase-with-hyphens
    name            = "My Plugin"        # required, human-readable label
    version         = "1.0.0"            # required, dotted integers
    min_nurb        = "0.22.0"           # optional, oldest compatible nurb
    max_nurb        = ""                 # optional, newest compatible nurb
    description     = "Does X"          # optional, one-line summary
    author          = "Name"            # optional
    license         = "MIT"             # optional

    [capabilities]
    commands        = true               # plugin adds CLI commands
    mcp_tools       = true               # plugin adds MCP tools
    build_checks    = true               # plugin adds printability checks

    [[mcp.tools]]
    name            = "my_tool"          # required
    description     = "Does something"   # required
    # inputSchema is JSON-encoded in plugin.py via register_mcp_tool()
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


class ManifestError(Exception):
    """Raised when a plugin manifest is invalid."""

    def __init__(self, plugin_id: str, message: str, path: Path | None = None):
        self.plugin_id = plugin_id
        self.path = path
        super().__init__(f"plugin {plugin_id!r}: {message}")


@dataclass(frozen=True)
class McpToolDecl:
    """A declared MCP tool entry from the manifest."""

    name: str
    description: str


@dataclass(frozen=True)
class PluginManifest:
    """Validated plugin identity and capabilities."""

    id: str
    name: str
    version: str
    description: str
    author: str
    license: str
    min_nurb: str
    max_nurb: str
    commands: bool
    mcp_tools: bool
    build_checks: bool
    mcp_tool_decls: tuple[McpToolDecl, ...] = ()
    path: Path | None = None

    def is_compatible(self, nurb_version: str) -> bool:
        """Check whether this plugin works with the given nurb version.

        Version comparison is dotted-integer comparison, matching the format
        validation in parse_manifest. No third-party version library is
        needed for the three-part versions nurb and plugins use.
        """
        def parts(v: str) -> tuple[int, ...]:
            return tuple(int(p) for p in v.split(".") if p.isdigit())

        try:
            current = parts(nurb_version)
        except (TypeError, ValueError):
            return False
        if not current:
            return False
        if self.min_nurb:
            try:
                if current < parts(self.min_nurb):
                    return False
            except (TypeError, ValueError):
                return False
        if self.max_nurb:
            try:
                if current > parts(self.max_nurb):
                    return False
            except (TypeError, ValueError):
                return False
        return True


def _require(data: dict, key: str, section: str, plugin_id: str) -> str:
    """Return a required string field or raise ManifestError."""
    val = data.get(key)
    if val is None:
        raise ManifestError(plugin_id, f"missing required field [{section}] {key}")
    if isinstance(val, str):
        text = val
    elif isinstance(val, (int, float)):
        text = str(val)  # version = 1.0 is a mistake, but say what it became
    else:
        raise ManifestError(plugin_id, f"[{section}] {key} must be a string, got {type(val).__name__}")
    if not text.strip():
        raise ManifestError(plugin_id, f"missing required field [{section}] {key}")
    return text


def _parse_mcp_tools(raw: list, plugin_id: str) -> tuple[McpToolDecl, ...]:
    """Parse [[mcp.tools]] declarations."""
    decls = []
    for i, entry in enumerate(raw):
        if not isinstance(entry, dict):
            raise ManifestError(
                plugin_id,
                f"[[mcp.tools]] entry {i} must be a table, got {type(entry).__name__}",
            )
        name = entry.get("name", "")
        desc = entry.get("description", "")
        if not name or not isinstance(name, str):
            raise ManifestError(
                plugin_id,
                f"[[mcp.tools]] entry {i} missing string 'name'",
            )
        if not desc or not isinstance(desc, str):
            raise ManifestError(
                plugin_id,
                f"[[mcp.tools]] entry {i} missing string 'description'",
            )
        decls.append(McpToolDecl(name=name, description=desc))
    return tuple(decls)


def parse_manifest(path: Path) -> PluginManifest:
    """Parse and validate a ``plugin.toml`` file into a ``PluginManifest``.

    Raises ``ManifestError`` for any validation failure.
    """
    if not path.is_file():
        raise ManifestError("(unknown)", f"manifest not found: {path}", path)

    try:
        with open(path, "rb") as f:
            raw = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise ManifestError("(unknown)", f"TOML parse error: {exc}", path) from exc

    plugin_section = raw.get("plugin")
    if not plugin_section or not isinstance(plugin_section, dict):
        raise ManifestError("(unknown)", "missing [plugin] section", path)

    plugin_id = _require(plugin_section, "id", "plugin", "(unknown)")
    name = _require(plugin_section, "name", "plugin", plugin_id)
    version = _require(plugin_section, "version", "plugin", plugin_id)

    # Validate ID format: lowercase, alphanumeric with hyphens, no underscores.
    if not plugin_id.replace("-", "").isalnum() or plugin_id != plugin_id.lower():
        raise ManifestError(
            plugin_id,
            f"id must be lowercase alphanumeric with hyphens, got {plugin_id!r}",
            path,
        )

    # Validate version is dotted integers.
    parts_list = version.split(".")
    if not parts_list or not all(p.isdigit() for p in parts_list):
        raise ManifestError(
            plugin_id,
            f"version must be dotted integers (e.g. 1.0.0), got {version!r}",
            path,
        )

    caps = raw.get("capabilities", {})
    if not isinstance(caps, dict):
        caps = {}

    mcp_decls = ()
    mcp_section = raw.get("mcp")
    if isinstance(mcp_section, dict):
        raw_tools = mcp_section.get("tools", [])
        if raw_tools:
            mcp_decls = _parse_mcp_tools(raw_tools, plugin_id)

    return PluginManifest(
        id=plugin_id,
        name=name,
        version=version,
        description=str(plugin_section.get("description", "")),
        author=str(plugin_section.get("author", "")),
        license=str(plugin_section.get("license", "")),
        min_nurb=str(plugin_section.get("min_nurb", "")),
        max_nurb=str(plugin_section.get("max_nurb", "")),
        commands=bool(caps.get("commands", False)),
        mcp_tools=bool(caps.get("mcp_tools", False)),
        build_checks=bool(caps.get("build_checks", False)),
        mcp_tool_decls=mcp_decls,
        path=path.parent,
    )
