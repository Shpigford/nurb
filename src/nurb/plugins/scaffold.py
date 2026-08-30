"""`nurb plugin new`: scaffold a plugin from the shipped template.

Copies ``plugins/_template/`` into ``<project>/plugins/<name>`` and
substitutes the id, the human name, and the sample tool name so the result
is a working plugin, not a rename of a placeholder. The template is never
loaded by the loader (underscore-prefixed directories are skipped), so it can
stay a template in a shipped tree.
"""

from __future__ import annotations

import re
from pathlib import Path

from .loader import _BUILTIN_DIR

# Same rule the manifest validator enforces: lowercase alphanumeric with
# hyphens, no leading or trailing hyphen, no underscores.
_ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class ScaffoldError(Exception):
    """Raised when a plugin cannot be scaffolded; message says why."""


def scaffold_plugin(project_root: Path | None, name: str) -> Path:
    """Create a new plugin from the template. Returns the created directory.

    ``name`` is the plugin id (``my-plugin`` style). Raises ``ScaffoldError``
    with a specific reason for a bad id, a missing template, or an existing
    destination; nothing is written in those cases.
    """
    plugin_id = (name or "").strip().lower()
    if not _ID_RE.match(plugin_id):
        raise ScaffoldError(
            f"plugin id must be lowercase alphanumeric with hyphens (e.g. my-plugin), got {name!r}"
        )

    template = _BUILTIN_DIR / "_template"
    if not template.is_dir():
        raise ScaffoldError(f"plugin template not found at {template}")

    root = Path(project_root) if project_root else Path()
    dest = root / "plugins" / plugin_id
    if dest.exists():
        raise ScaffoldError(f"{dest} already exists; choose another id or remove it first")

    dest.mkdir(parents=True)
    title = plugin_id.replace("-", " ").title()
    # Tool names and their handler functions must be valid Python identifiers,
    # so hyphens in the id become underscores there (MCP tool names are
    # snake_case; CLI command names keep the hyphens).
    tool_name = plugin_id.replace("-", "_") + "_tool"
    # Longest strings first so "my-plugin-hello" is replaced before the bare
    # "my-plugin" it contains.
    replacements = (
        ("my-plugin-hello", f"{plugin_id}-hello"),
        ("my_tool", tool_name),
        ("my-plugin", plugin_id),
        ("My Plugin", title),
    )
    for file_name in ("plugin.toml", "plugin.py", "README.md"):
        source = template / file_name
        if not source.is_file():
            continue
        text = source.read_text(encoding="utf-8")
        for old, new in replacements:
            text = text.replace(old, new)
        (dest / file_name).write_text(text, encoding="utf-8")
    return dest
