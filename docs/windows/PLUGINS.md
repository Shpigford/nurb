# nurb plugin system

A plugin is a directory containing a `plugin.toml` manifest and optionally a
`plugin.py` module. The manifest declares identity, capabilities, and version
constraints; the module provides the runtime implementations. This is the
nurb-side (Python engine) contract. The desktop app's extension registry is a
separate surface for launching external tools in a terminal panel; see
`docs/windows/EXTENSIONS.md`.

## What a plugin can do

- **CLI commands**: `nurb <command-name>` runs a function the plugin registered.
- **MCP tools**: the nurb MCP server (`nurb mcp`) lists the plugin's tools and
  dispatches calls to them, alongside the built-in `nurb_*` tools.
- **Build checks**: functions that run inside `nurb check`, producing
  `Finding` objects exactly like the built-in rules.

A plugin needs none of these: a manifest alone is a valid plugin that just
holds identity and metadata.

## Where plugins live

Three directories are scanned at startup, in this order (later wins on an ID
collision):

1. `plugins/` next to the nurb package (shipped examples and the template).
   The examples are nested one level: `plugins/examples/<name>/`.
2. `<project>/plugins/` for project-local plugins, where `<project>` is the
   nurb project root (the directory containing `parts/`).
3. `~/.nurb/plugins/` for user-installed plugins.

Directories starting with `_` or `.` are never loaded, which is why the
template (`plugins/_template`) is safe to ship.

## The manifest

`plugin.toml` is TOML. Every field is validated on load; a malformed manifest
is rejected with an error naming the field and the expected format.

```toml
[plugin]
id = "my-plugin"        # required: lowercase alphanumeric with hyphens
name = "My Plugin"      # required: human-readable label
version = "1.0.0"       # required: dotted integers
description = "Does X"  # optional: one-line summary
author = "You"          # optional
license = "MIT"         # optional
min_nurb = "0.22.0"     # optional: oldest nurb this works with
max_nurb = "0.99.0"     # optional: newest nurb this works with

[capabilities]
commands = true      # plugin adds CLI commands
mcp_tools = true     # plugin adds MCP tools
build_checks = false # plugin adds printability checks

[[mcp.tools]]        # optional: declare MCP tools
name = "my_tool"
description = "What my_tool does"
```

### Validation rules

- `id`: required, lowercase alphanumeric with hyphens, no underscores.
- `version`: required, dotted integers (`1.0.0`, `2.3`).
- `[capabilities]` is optional and defaults every flag to false.
- `[[mcp.tools]]` entries require both `name` and `description` as strings.
- Version bounds are compared as dotted integers; `min_nurb`/`max_nurb` are
  inclusive. A plugin outside the running nurb's version range is skipped with
  a recorded error, never loaded.

## The plugin module

`plugin.py` is imported after the manifest validates. It is expected to define
a `register(registry, manifest)` function:

```python
def cmd_hello(args):
    print("  hello from my-plugin")


def _mcp_handle_my_tool(arguments: dict) -> dict:
    return {"content": [{"type": "text", "text": "my_tool ran"}], "isError": False}


def register(registry, manifest):
    registry.add_command("my-plugin-hello", cmd_hello, manifest.id)
    registry.add_mcp_tool(
        "my_tool",
        {
            "name": "my_tool",
            "description": "What my_tool does",
            "inputSchema": {"type": "object", "properties": {}},
        },
        manifest.id,
    )
```

### CLI commands

`registry.add_command(name, handler, plugin_id)` registers a command handler.
The handler receives an `argparse.Namespace` with `.project` (the project root
as a string) and `.argv` (the raw arguments after the command name). Parse
`.argv` yourself; plugin commands are not argparse subcommands, so nurb cannot
declare their flags. The command is dispatched as `nurb <name>` before the
built-in parser runs.

### MCP tools

`registry.add_mcp_tool(name, tool_def, plugin_id)` registers an MCP tool. The
`tool_def` is the full MCP tool object (`name`, `description`, `inputSchema`).
When an agent calls the tool, the registry looks up
`_mcp_handle_<tool_name>(arguments)` on the plugin module and returns its
result verbatim, so it must be a complete MCP result object
(`{"content": [...], "isError": bool}`).

### Build checks

`registry.add_build_check(fn, plugin_id)` registers a function called as
`fn(shape, ctx)` inside `checks.run`, alongside the built-in rules. It returns
a list of `nurb.checks.Finding` objects. A check that raises is skipped with a
warning; it never fails the part or the check run.

## Lifecycle

1. **Discovery**: the loader walks the three plugin directories for
   subdirectories containing `plugin.toml`.
2. **Validation**: the manifest is parsed; a broken manifest is recorded as an
   error and skipped.
3. **Compatibility**: if `min_nurb`/`max_nurb` exclude the running version, the
   plugin is skipped with a recorded reason.
4. **Loading**: `plugin.py` is imported (with its directory on `sys.path` for
   relative imports) and `register(registry, manifest)` is called.
5. **Runtime**: commands dispatch to handlers, MCP calls dispatch to
   `_mcp_handle_*`, build checks run inside `nurb check`.
6. **Failure isolation**: any failure at any step marks that plugin as errored
   in the registry and leaves every other plugin and nurb itself running.

## The registry

`nurb.plugins.registry` is the single source of truth: it holds every plugin
record (id, name, version, state, error, contributions) and the name-to-owner
maps for commands and MCP tools. Look up commands with
`registry.command_handler(name)`, MCP tool definitions with
`registry.mcp_tool_def(name)`, and dispatch MCP calls with
`registry.call_mcp_tool(name, arguments)`.

## Inspecting plugins

`nurb plugins` lists every loaded plugin, its version, state, and what it
contributes. Errored plugins are listed with their error, so a broken plugin is
visible rather than silently absent. `nurb plugins --json` emits the same view
as machine-readable JSON (one entry per plugin with id, name, version,
description, state, source, enabled, and its commands, mcp tools, and checks),
which is what the desktop Settings panel renders.

## Scaffolding a plugin

`nurb plugin new <id>` copies the shipped template (`plugins/_template/`) into
`<project>/plugins/<id>` and substitutes the id, the human name, and the sample
tool name so the result is a working plugin: it parses, imports, registers, and
appears in `nurb plugins`. The id must be lowercase alphanumeric with hyphens
(`my-plugin`); an existing destination is refused without touching it.

The template is never loaded itself: directories starting with `_` are skipped
by discovery, so the template can live in a shipped tree.

## Enabling and disabling

Plugins load by default. A project can switch one off without deleting it:

- `nurb plugin disable <id>` / `nurb plugin enable <id>`

The decision is persisted in `<project>/.nurb/plugins.toml` as a single table:

    [plugins]
    disabled = ["everything"]

Both the CLI and the desktop Settings panel write this file, so the two
surfaces agree. A disabled plugin is still validated and recorded (it shows as
`[disabled]` in `nurb plugins`, and the Settings toggle can switch it back on)
but it is never imported, so it cannot register commands, MCP tools, or build
checks. The change takes effect on the next load: immediately for the CLI,
on the next `/api/plugins` request or server restart for a running dev server.

## PATH detection

Example plugins that wrap an external executable discover it through
`shutil.which()`, never a hard-coded path. On Windows this resolves
`es.exe`, `universal`, and so on through `PATHEXT`. A plugin that cannot
find its executable reports guidance (how to install it) instead of crashing,
and its MCP tool returns an `isError: true` result.

## Testing plugins

The suite in `tests/test_plugins.py` covers manifest validation, discovery,
registration, command dispatch, MCP tool registration and calls, build checks,
PATH detection with fake executables, failure isolation, and the shipped
examples. A plugin author's tests never need the real external tool installed:
create a fake executable in a temp dir and put that dir on `PATH`.
