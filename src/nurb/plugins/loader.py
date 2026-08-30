"""Plugin discovery and loading.

Scans plugin directories for subdirectories containing ``plugin.toml``.
Validates each manifest, imports ``plugin.py`` if present, and calls its
``register()`` function to let the plugin wire up commands and tools.

A broken plugin is logged and skipped; it never prevents other plugins from
loading or nurb from starting.
"""

from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path

from .manifest import ManifestError, parse_manifest
from .registry import PluginState, registry
from .state import disabled_ids

log = logging.getLogger(__name__)


def _builtin_dir() -> Path:
    """The shipped plugin directory: repo-root plugins/ in a source checkout.

    Resolved from this file's location rather than cwd, so it works regardless
    of where nurb is invoked from. When nurb is installed as a package the
    examples live next to the package data, so the parent of src/nurb is
    walked until a plugins/ directory with plugin.toml manifests is found.
    """
    here = Path(__file__).resolve()
    # src/nurb/plugins/loader.py -> repo root is three parents up
    root = here.parents[3] if here.parents else here.parent
    candidate = root / "plugins"
    if (candidate / "examples").is_dir():
        return candidate
    # Fall back to the package-adjacent location.
    for parent in here.parents:
        trial = parent / "plugins"
        if trial.is_dir() and not trial.name.startswith("."):
            return trial
    return candidate


_BUILTIN_DIR = _builtin_dir()
_USER_DIR = Path.home() / ".nurb" / "plugins"


def _plugin_dirs(project_root: Path | None = None) -> list[Path]:
    """Ordered list of plugin directories to scan. Later dirs win on ID collision."""
    dirs = []
    if _BUILTIN_DIR.is_dir():
        dirs.append(_BUILTIN_DIR)
    if project_root:
        proj_plugins = project_root / "plugins"
        if proj_plugins.is_dir():
            dirs.append(proj_plugins)
    if _USER_DIR.is_dir():
        dirs.append(_USER_DIR)
    # The repo-root plugins/ dir is both the builtin and the project dir in a
    # source checkout; scanning it twice re-imports every module for nothing.
    seen = []
    for d in dirs:
        resolved = d.resolve()
        if resolved not in seen:
            seen.append(resolved)
            yield d


def _candidate_dirs(plugin_dir: Path):
    """Directories inside a plugin dir that may hold a plugin.

    A plugin is a directory containing plugin.toml. The shipped dir also nests
    its examples one level down (plugins/examples/<name>/), so both direct
    children and plugins/examples/* are candidates.
    """
    for child in sorted(plugin_dir.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith("_") or child.name.startswith("."):
            continue  # template and hidden dirs are never loaded
        yield child
    examples = plugin_dir / "examples"
    if examples.is_dir():
        for child in sorted(examples.iterdir()):
            if not child.is_dir():
                continue
            if child.name.startswith("_") or child.name.startswith("."):
                continue
            yield child


def _import_plugin(plugin_dir: Path, plugin_id: str):
    """Import ``plugin.py`` from a plugin directory.

    Returns the imported module or None if no plugin.py exists.
    Raises on import errors (caller decides whether to skip).
    """
    plugin_py = plugin_dir / "plugin.py"
    if not plugin_py.is_file():
        return None
    module_name = f"nurb_plugin_{plugin_id}"
    spec = importlib.util.spec_from_file_location(module_name, plugin_py)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot create module spec for {plugin_py}")
    module = importlib.util.module_from_spec(spec)
    # Temporarily add the plugin directory to sys.path so relative imports work.
    plugin_dir_str = str(plugin_dir)
    old_path = sys.path.copy()
    if plugin_dir_str not in sys.path:
        sys.path.insert(0, plugin_dir_str)
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = old_path
    return module


def _nurb_version() -> str | None:
    """The running nurb version, or None if it cannot be determined."""
    import importlib.metadata

    try:
        return importlib.metadata.version("nurb")
    except importlib.metadata.PackageNotFoundError:
        return None


def load_plugin(plugin_dir: Path, disabled: set[str] | None = None) -> bool:
    """Load a single plugin from a directory. Returns True on success.

    ``disabled`` is the set of plugin ids this project has switched off. A
    disabled plugin is recorded (so the registry and `nurb plugins` still show
    it, and the Settings panel can switch it back on) but never imported or
    registered: a disabled plugin cannot add commands, tools, or checks.
    """
    manifest_path = plugin_dir / "plugin.toml"
    try:
        manifest = parse_manifest(manifest_path)
    except ManifestError as exc:
        log.warning("skipping broken plugin in %s: %s", plugin_dir, exc)
        registry.mark_error(f"{plugin_dir.name}:{manifest_path.name}", str(exc))
        return False
    except Exception as exc:
        log.warning("skipping plugin in %s: %s", plugin_dir, exc)
        registry.mark_error(f"{plugin_dir.name}:{manifest_path.name}", str(exc))
        return False

    # A disabled plugin is still validated (a broken manifest shows as error,
    # not as disabled) but never imported. Record it so the toggle surface
    # sees it; a second pass over the same disabled plugin is a no-op.
    if disabled and manifest.id in disabled:
        existing = registry.get(manifest.id)
        if existing and existing.source == str(plugin_dir) and existing.state == PluginState.DISABLED:
            return True
        record = registry.register(
            plugin_id=manifest.id,
            name=manifest.name,
            version=manifest.version,
            source=str(plugin_dir),
            state=PluginState.DISABLED,
        )
        record.description = manifest.description
        return True

    # Check nurb version compatibility.
    nurb_version = _nurb_version()
    if nurb_version and not manifest.is_compatible(nurb_version):
        log.info(
            "skipping incompatible plugin %s (requires nurb %s%s, have %s)",
            manifest.id,
            ">=" if manifest.min_nurb else "",
            manifest.min_nurb or manifest.max_nurb,
            nurb_version,
        )
        registry.mark_error(
            manifest.id,
            f"incompatible with nurb {nurb_version} (requires {manifest.min_nurb or '?'}..{manifest.max_nurb or 'any'})",
        )
        return False

    # A second load_all pass over the same directory must not re-import the
    # module: a fresh import produces fresh function objects, which would
    # duplicate build checks and re-run every registration. Same source and
    # already loaded means the record is current; report success.
    existing = registry.get(manifest.id)
    if existing and existing.source == str(plugin_dir) and existing.state == PluginState.LOADED:
        return True

    # Register the plugin identity. A different source with the same ID
    # replaces the earlier record, so a project-local plugin overrides a
    # shipped example; the registry handles that wholesale swap.
    record = registry.register(
        plugin_id=manifest.id,
        name=manifest.name,
        version=manifest.version,
        source=str(plugin_dir),
    )
    record.description = manifest.description

    # Import plugin.py if it exists.
    module = None
    if (plugin_dir / "plugin.py").is_file():
        try:
            module = _import_plugin(plugin_dir, manifest.id)
            record.module = module
        except Exception as exc:
            error_msg = f"import error: {exc}"
            log.warning("plugin %s failed to import: %s", manifest.id, exc)
            # A failed load must not leave half-registered contributions live.
            registry.unregister(manifest.id)
            registry.mark_error(manifest.id, error_msg)
            return False

    # Call the plugin's register() function if present.
    if module and hasattr(module, "register"):
        try:
            module.register(registry, manifest)
        except Exception as exc:
            error_msg = f"register() failed: {exc}"
            log.warning("plugin %s register() failed: %s", manifest.id, exc)
            registry.unregister(manifest.id)
            registry.mark_error(manifest.id, error_msg)
            return False

    # Manifest-declared MCP tools that the module did not itself register are
    # registered here: the [[mcp.tools]] table is the declaration contract,
    # and the handler is looked up by convention (_mcp_handle_<name>).
    for decl in manifest.mcp_tool_decls:
        if not registry.has_mcp_tool(decl.name):
            registry.add_mcp_tool(
                decl.name,
                {
                    "name": decl.name,
                    "description": decl.description,
                    "inputSchema": {"type": "object", "properties": {}},
                },
                manifest.id,
            )

    return True


def load_all(project_root: Path | None = None) -> int:
    """Discover and load all plugins from all configured directories.

    Each call is a complete snapshot for that project. The registry is a
    process-wide singleton, so clearing it here prevents a plugin loaded for a
    previously opened project from leaking into a project that does not have
    it. Direct ``load_plugin`` calls remain incremental for focused tests and
    embedders.
    """
    registry.refresh()
    disabled = disabled_ids(project_root)
    for plugin_dir in _plugin_dirs(project_root):
        for child in _candidate_dirs(plugin_dir):
            if not (child / "plugin.toml").is_file():
                continue  # not a plugin
            load_plugin(child, disabled=disabled)
    return len(registry.loaded_plugins())


def status_payload(project_root: Path | None = None) -> list[dict]:
    """The JSON view of the registry, for `nurb plugins --json` and /api/plugins.

    Includes every plugin the registry knows about: loaded, disabled, and
    errored, so a surface that renders toggles can show all of them.
    """
    load_all(project_root)
    disabled = disabled_ids(project_root)
    out = []
    for record in sorted(registry.all_plugins(), key=lambda r: r.plugin_id):
        out.append(
            {
                "id": record.plugin_id,
                "name": record.name,
                "version": record.version,
                "description": record.description,
                "state": record.state.value,
                "error": record.error,
                "source": record.source,
                "enabled": record.plugin_id not in disabled,
                "commands": sorted(record.commands),
                "mcpTools": sorted(record.mcp_tools),
                "checks": len(record.build_check_fns),
            }
        )
    return out
