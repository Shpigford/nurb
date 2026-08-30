"""Per-project plugin enable/disable state.

The state file lives at ``<project>/.nurb/plugins.toml`` and holds one table:

    [plugins]
    disabled = ["everything"]

Plugins load by default; an id in ``disabled`` is recorded in the registry but
never imported or registered. Both the nurb CLI (``nurb plugin enable|disable``)
and the desktop app's Settings panel write this file, so the two surfaces
agree on what is off for a project. The file is engine-managed: writers
rewrite the whole file, so other keys are not preserved.
"""

from __future__ import annotations

import tomllib
from pathlib import Path


def state_path(project_root: Path | None) -> Path:
    """The state file for a project. Without a project root there is no state."""
    if project_root is None:
        return Path()
    return Path(project_root) / ".nurb" / "plugins.toml"


def disabled_ids(project_root: Path | None) -> set[str]:
    """The set of plugin ids the project has disabled. Never raises."""
    path = state_path(project_root)
    if not path.is_file():
        return set()
    try:
        with open(path, "rb") as f:
            raw = tomllib.load(f)
    except (tomllib.TOMLDecodeError, OSError):
        return set()
    section = raw.get("plugins")
    if not isinstance(section, dict):
        return set()
    ids = section.get("disabled")
    if not isinstance(ids, list):
        return set()
    return {str(item) for item in ids if isinstance(item, str)}


def set_enabled(project_root: Path | None, plugin_id: str, enabled: bool) -> Path:
    """Record whether a plugin is enabled for this project.

    Returns the state file path. ``enabled=True`` removes the id from the
    disabled set; ``enabled=False`` adds it. The file is rewritten sorted so
    the result is deterministic and diff-friendly.
    """
    root = Path(project_root) if project_root else Path()
    path = root / ".nurb" / "plugins.toml"
    disabled = disabled_ids(root)
    if enabled:
        disabled.discard(plugin_id)
    else:
        disabled.add(plugin_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    listing = ", ".join(f'"{item}"' for item in sorted(disabled))
    path.write_text(f"[plugins]\ndisabled = [{listing}]\n", encoding="utf-8")
    return path
