"""Plugin registry: the single source of truth for loaded plugins.

The registry holds every plugin that was successfully loaded, indexed by ID.
It also tracks contributions (CLI commands, MCP tools, build checks) and
provides lookup methods for the CLI, MCP server, and check runner.

The registry is a module-level singleton; nurb is a single-process tool so
there is no need for thread-safe locking.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Callable


class PluginState(enum.Enum):
    """Lifecycle state of a plugin."""

    UNLOADED = "unloaded"
    LOADED = "loaded"
    DISABLED = "disabled"  # found and valid, but off for this project
    ERROR = "error"


@dataclass
class PluginRecord:
    """Internal bookkeeping for one loaded plugin."""

    plugin_id: str
    name: str
    version: str
    description: str = ""
    state: PluginState = PluginState.UNLOADED
    module: Any = None
    error: str = ""
    source: str = ""  # the plugin directory it was loaded from
    commands: dict[str, Callable] = field(default_factory=dict)
    mcp_tools: dict[str, dict] = field(default_factory=dict)
    build_check_fns: list[Callable] = field(default_factory=list)


class PluginRegistry:
    """Manages loaded plugins and their contributions."""

    def __init__(self) -> None:
        self._plugins: dict[str, PluginRecord] = {}
        self._commands: dict[str, str] = {}  # command_name -> plugin_id
        self._mcp_tools: dict[str, str] = {}  # tool_name -> plugin_id
        self._build_checks: list[tuple[str, Callable]] = []  # (plugin_id, fn)

    def register(
        self,
        plugin_id: str,
        name: str,
        version: str,
        module: Any = None,
        source: str = "",
        state: PluginState = PluginState.LOADED,
    ) -> PluginRecord:
        """Register a plugin. Returns the record for further population.

        Idempotent for the same source and state (a second load_all pass must
        not duplicate contributions). A different source with the same ID, or
        a state change (enabled -> disabled), replaces the earlier record
        wholesale, dropping its stale contributions.
        """
        existing = self._plugins.get(plugin_id)
        if existing and existing.source == source and existing.state == state:
            return existing  # idempotent: same dir scanned again
        if existing:
            self.unregister(plugin_id)
        record = PluginRecord(
            plugin_id=plugin_id,
            name=name,
            version=version,
            module=module,
            state=state,
            source=source,
        )
        self._plugins[plugin_id] = record
        return record

    def mark_error(self, plugin_id: str, error: str) -> None:
        """Mark a plugin as failed. It stays in the registry for diagnostics."""
        record = self._plugins.get(plugin_id)
        if record:
            record.state = PluginState.ERROR
            record.error = error
        else:
            self._plugins[plugin_id] = PluginRecord(
                plugin_id=plugin_id,
                name=plugin_id,
                version="",
                state=PluginState.ERROR,
                error=error,
            )

    def unregister(self, plugin_id: str) -> None:
        """Remove a plugin and all its contributions."""
        record = self._plugins.pop(plugin_id, None)
        if record:
            for cmd_name in list(self._commands):
                if self._commands[cmd_name] == plugin_id:
                    del self._commands[cmd_name]
            for tool_name in list(self._mcp_tools):
                if self._mcp_tools[tool_name] == plugin_id:
                    del self._mcp_tools[tool_name]
            self._build_checks = [
                (pid, fn) for pid, fn in self._build_checks if pid != plugin_id
            ]

    def add_command(self, command_name: str, handler: Callable, plugin_id: str) -> None:
        """Register a CLI command from a plugin."""
        if command_name in self._commands:
            existing_pid = self._commands[command_name]
            if existing_pid != plugin_id:
                raise ValueError(
                    f"command {command_name!r} already registered by plugin {existing_pid!r}"
                )
            return  # idempotent: same plugin re-registering is a no-op
        self._commands[command_name] = plugin_id
        record = self._plugins.get(plugin_id)
        if record:
            record.commands[command_name] = handler

    def add_mcp_tool(self, tool_name: str, tool_def: dict, plugin_id: str) -> None:
        """Register an MCP tool from a plugin."""
        if tool_name in self._mcp_tools and self._mcp_tools[tool_name] != plugin_id:
            raise ValueError(
                f"MCP tool {tool_name!r} already registered by plugin {self._mcp_tools[tool_name]!r}"
            )
        self._mcp_tools[tool_name] = plugin_id
        record = self._plugins.get(plugin_id)
        if record:
            record.mcp_tools[tool_name] = tool_def

    def add_build_check(self, check_fn: Callable, plugin_id: str) -> None:
        """Register a build check function from a plugin.

        Idempotent: a second load_all pass over the same plugin must not run
        the check twice, so re-registering the same function is a no-op.
        """
        if (plugin_id, check_fn) not in self._build_checks:
            self._build_checks.append((plugin_id, check_fn))
        record = self._plugins.get(plugin_id)
        if record and check_fn not in record.build_check_fns:
            record.build_check_fns.append(check_fn)

    # -- Lookup methods --

    def get(self, plugin_id: str) -> PluginRecord | None:
        return self._plugins.get(plugin_id)

    def loaded_plugins(self) -> list[PluginRecord]:
        """All plugins in LOADED state."""
        return [r for r in self._plugins.values() if r.state == PluginState.LOADED]

    def errored_plugins(self) -> list[PluginRecord]:
        """All plugins in ERROR state, for diagnostics."""
        return [r for r in self._plugins.values() if r.state == PluginState.ERROR]

    def all_plugins(self) -> list[PluginRecord]:
        return list(self._plugins.values())

    def command_handler(self, command_name: str) -> tuple[Callable | None, str | None]:
        """Look up a command handler. Returns (handler, plugin_id) or (None, None)."""
        pid = self._commands.get(command_name)
        if pid:
            record = self._plugins.get(pid)
            if record and command_name in record.commands:
                return record.commands[command_name], record.plugin_id
        return None, None

    def has_command(self, command_name: str) -> bool:
        return command_name in self._commands

    def mcp_tool_def(self, tool_name: str) -> dict | None:
        """Look up an MCP tool definition by name."""
        pid = self._mcp_tools.get(tool_name)
        if pid:
            record = self._plugins.get(pid)
            if record and tool_name in record.mcp_tools:
                return record.mcp_tools[tool_name]
        return None

    def has_mcp_tool(self, tool_name: str) -> bool:
        return tool_name in self._mcp_tools

    def all_mcp_tool_defs(self) -> list[dict]:
        """Return all registered MCP tool definitions."""
        defs = []
        for tool_name, pid in self._mcp_tools.items():
            record = self._plugins.get(pid)
            if record and tool_name in record.mcp_tools:
                defs.append(record.mcp_tools[tool_name])
        return defs

    def all_mcp_tool_names(self) -> list[str]:
        return list(self._mcp_tools.keys())

    def call_mcp_tool(self, tool_name: str, arguments: dict) -> Any | None:
        """Dispatch an MCP tool call to the owning plugin's handler."""
        pid = self._mcp_tools.get(tool_name)
        if not pid:
            return None
        record = self._plugins.get(pid)
        if not record or not record.module:
            return None
        handler = getattr(record.module, f"_mcp_handle_{tool_name}", None)
        if handler:
            return handler(arguments or {})
        return None

    def build_check_functions(self) -> list[Callable]:
        """All registered build check functions, in registration order."""
        return [fn for _, fn in self._build_checks]

    def clear(self) -> None:
        """Remove all plugins. Used in tests and explicit reloads."""
        self._plugins.clear()
        self._commands.clear()
        self._mcp_tools.clear()
        self._build_checks.clear()

    def refresh(self) -> None:
        """Drop the current registry before a deliberate project reload."""
        self.clear()


# Module-level singleton.
registry = PluginRegistry()
