"""The nurb MCP server: nurb's own commands, exposed over the Model Context
Protocol as tools and the project's files as resources.

This is a stdio server speaking the MCP JSON-RPC framing (one JSON object per
line, the transport the official @modelcontextprotocol SDK clients use). It
exists so an MCP-capable agent can call nurb build,
check, inspect, verify, and export through the agent's own supported
mechanism, after the user enables it in the agent's mcp.json.

Two boundaries are structural, not policy:

- Every tool is literally the nurb CLI command for that name: the server
  builds the same argparse Namespace the command line would and calls the same
  cmd_* function, capturing its output. There is no second implementation to
  drift, and no hidden capability the CLI does not have.
- The server only ever acts inside the project directory it was given (or the
  one it infers from cwd, like every other nurb command). It reads no
  credentials, touches no agent configuration, and makes no network calls.
"""

import argparse
import contextlib
import io
import json
import os
import pathlib
import sys

from . import builder

NAME = "nurb-mcp"
VERSION = "0.1.0"

# The MCP protocol version this server speaks, from the protocol spec.
PROTOCOL_VERSION = "2025-06-18"


class McpError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def _text(content):
    return [{"type": "text", "text": content}]


def _tool(name, description, props=None, required=None):
    return {
        "name": name,
        "description": description,
        "inputSchema": {
            "type": "object",
            "properties": props or {},
            "required": required or [],
        },
    }


TOOLS = [
    _tool(
        "nurb_build",
        "Build a part (or all parts) of the nurb project and report dimensions and timing.",
        {"part": {"type": "string", "description": "Part name (without .py), default: all parts"}},
    ),
    _tool(
        "nurb_check",
        "Run the printability checks on a part and report findings.",
        {
            "part": {"type": "string", "description": "Part name, default: all parts"},
            "printer": {"type": "string", "description": "Printer profile to check against"},
        },
    ),
    _tool(
        "nurb_inspect",
        "Measure a built part: faces, normals, concave edges, each finding on its face.",
        {"part": {"type": "string", "description": "Part name, default: all parts"}},
    ),
    _tool(
        "nurb_verify",
        "Run the doctrine's verification list for the project.",
        {"part": {"type": "string", "description": "Part name, default: all parts"}},
    ),
    _tool(
        "nurb_export",
        "Export a part to print files in build/. Formats are space-separated: 3mf (default), stl, step, glb.",
        {
            "part": {"type": "string", "description": "Part name, default: all parts"},
            "formats": {"type": "string", "description": "Space-separated formats, default: 3mf"},
        },
    ),
    _tool(
        "nurb_rules",
        "Print the design doctrine: the rules every part in this project follows.",
    ),
    _tool(
        "nurb_api",
        "Print the vocabulary a part file gets: every name available to a @part function.",
    ),
    _tool(
        "nurb_new",
        "Create a new part file and its card in parts/.",
        {"name": {"type": "string", "description": "Part name (underscores, not hyphens)"}},
        ["name"],
    ),
    _tool(
        "nurb_diff",
        "What changed since the card was written: size, volume, faces, verdict.",
        {"part": {"type": "string", "description": "Part name, default: all parts"}},
    ),
    _tool(
        "nurb_card",
        "Regenerate a part card's AUTO block with current geometry facts.",
        {"part": {"type": "string", "description": "Part name, default: all parts"}},
    ),
    _tool(
        "nurb_extract",
        "Find duplication across sibling parts that could become a shared system.",
    ),
    _tool(
        "nurb_stress",
        "Static stress under a load: peak MPa, deflection, margin to breaking.",
        {
            "part": {"type": "string", "description": "Part name, default: all parts"},
            "kg": {"type": "number", "description": "Weight pressing down in kg (default: card's or 1)"},
            "at": {"type": "string", "description": "x,y,z where the weight sits"},
            "material": {"type": "string", "description": "PLA, PETG, ABS, ASA, Nylon, or PC (default: card's or PLA)"},
        },
    ),
    _tool(
        "nurb_scan",
        "Measure a mesh file in mm: overall size, face count, and whether a solid can be imported.",
        {
            "file": {"type": "string", "description": "Path to the mesh file (STL, OBJ, GLB, PLY)"},
            "units": {"type": "string", "description": "Override unit guess: mm, cm, m, or in"},
        },
        ["file"],
    ),
    _tool(
        "nurb_compare",
        "Measure deviation between a part and its target mesh, both directions.",
        {
            "part": {"type": "string", "description": "Part name, default: all parts"},
            "against": {"type": "string", "description": "One-off target file (overrides card)"},
        },
    ),
    _tool(
        "nurb_slice",
        "Slice with the installed slicer: print time and filament weight.",
        {
            "part": {"type": "string", "description": "Part name, default: all parts"},
            "printer": {"type": "string", "description": "Printer profile to slice for"},
        },
    ),
    _tool(
        "nurb_render",
        "Write a PNG of a part to build/renders/.",
        {
            "part": {"type": "string", "description": "Part name, default: all parts"},
            "section": {"type": "string", "description": "Section cut: axis (x/y/z), e.g. z, z:0.5, z:4mm"},
            "view": {"type": "string", "description": "Camera view: iso, front, back, left, right, top"},
        },
    ),
    _tool(
        "nurb_skill",
        "Print the agent skill file, or --sync to rewrite installed copies.",
        {"sync": {"type": "boolean", "description": "Rewrite installed skill copies from this package"}},
    ),
    _tool(
        "nurb_update",
        "Upgrade nurb to the latest version and re-sync the installed skill.",
    ),
]


def _run_command(fn, namespace):
    """Run one nurb CLI command with a Namespace, capturing its output. The
    command runs with the project as cwd, exactly like the CLI would, and the
    caller's cwd is restored afterwards. A nonzero CLI exit (SystemExit from
    --strict, for example) becomes an MCP error result, never a dead server."""
    project = pathlib.Path(namespace.project).resolve()
    if not (project / "parts").is_dir():
        raise McpError(-32602, f"{project} is not a nurb project (no parts/)")
    cwd = pathlib.Path.cwd()
    out, err = io.StringIO(), io.StringIO()
    try:
        os.chdir(project)
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            fn(namespace)
    except SystemExit as exc:
        return {"content": _text(out.getvalue() + err.getvalue()), "isError": exc.code not in (None, 0)}
    except Exception as exc:  # a broken part file must not kill the server
        return {
            "content": _text(out.getvalue() + err.getvalue() + f"\n{type(exc).__name__}: {exc}"),
            "isError": True,
        }
    finally:
        os.chdir(cwd)
    return {"content": _text(out.getvalue() + err.getvalue())}


def _call_tool(name, arguments, project):
    from . import cli

    args = arguments or {}
    namespace = argparse.Namespace(project=str(project))
    if name == "nurb_build":
        namespace.part = args.get("part")
        namespace.draft = False
        return _run_command(cli.cmd_build, namespace)
    if name == "nurb_check":
        namespace.part = args.get("part")
        namespace.printer = args.get("printer")
        namespace.strict = False
        return _run_command(cli.cmd_check, namespace)
    if name == "nurb_inspect":
        namespace.part = args.get("part")
        namespace.render = False
        namespace.limit = None
        return _run_command(cli.cmd_inspect, namespace)
    if name == "nurb_verify":
        namespace.part = args.get("part")
        namespace.report = False
        return _run_command(cli.cmd_verify, namespace)
    if name == "nurb_export":
        namespace.part = args.get("part")
        namespace.formats = args.get("formats") or "3mf"
        return _run_command(cli.cmd_export, namespace)
    if name == "nurb_rules":
        return _run_command(cli.cmd_rules, namespace)
    if name == "nurb_api":
        return _run_command(cli.cmd_api, namespace)
    if name == "nurb_new":
        namespace.name = args["name"]
        return _run_command(cli.cmd_new, namespace)
    if name == "nurb_diff":
        namespace.part = args.get("part")
        return _run_command(cli.cmd_diff, namespace)
    if name == "nurb_card":
        namespace.part = args.get("part")
        return _run_command(cli.cmd_card, namespace)
    if name == "nurb_extract":
        return _run_command(cli.cmd_extract, namespace)
    if name == "nurb_stress":
        namespace.part = args.get("part")
        namespace.kg = args.get("kg")
        namespace.at = args.get("at")
        namespace.hold = None
        namespace.pitch = None
        namespace.material = args.get("material")
        return _run_command(cli.cmd_stress, namespace)
    if name == "nurb_scan":
        namespace.file = pathlib.Path(args["file"])
        namespace.units = args.get("units")
        namespace.section = None
        namespace.tolerance = 0.1
        return _run_command(cli.cmd_scan, namespace)
    if name == "nurb_compare":
        namespace.part = args.get("part")
        namespace.against = args.get("against")
        namespace.units = None
        return _run_command(cli.cmd_compare, namespace)
    if name == "nurb_slice":
        namespace.part = args.get("part")
        namespace.printer = args.get("printer")
        namespace.nozzle = None
        namespace.layer = "0.20"
        namespace.filament = None
        namespace.plate = ""
        return _run_command(cli.cmd_slice, namespace)
    if name == "nurb_render":
        namespace.part = args.get("part")
        namespace.section = args.get("section")
        namespace.view = args.get("view")
        namespace.width = 800
        namespace.height = 600
        namespace.chrome = None
        return _run_command(cli.cmd_render, namespace)
    if name == "nurb_skill":
        namespace.sync = args.get("sync", False)
        return _run_command(cli.cmd_skill, namespace)
    if name == "nurb_update":
        return _run_command(cli.cmd_update, namespace)
    raise McpError(-32602, f"unknown tool: {name}")


def _resources(project):
    return [
        {
            "uri": "nurb://parts",
            "name": "project parts",
            "description": "The part files in parts/, one per line.",
        },
        {
            "uri": "nurb://doctrine",
            "name": "design doctrine",
            "description": "The rules every part follows.",
        },
    ] + [
        {
            "uri": f"nurb://card/{path.stem}",
            "name": f"card for {path.stem}",
            "description": "The part's card (its notes file), when it exists.",
        }
        for path in builder.find_parts(project)
        if path.with_suffix(".md").is_file()
    ]


def _read_resource(uri, project):
    if uri == "nurb://parts":
        names = "\n".join(p.stem for p in builder.find_parts(project)) or "(no parts yet)"
        return {"contents": [{"uri": uri, "mimeType": "text/plain", "text": names}]}
    if uri == "nurb://doctrine":
        doctrine = pathlib.Path(__file__).parent / "doctrine.md"
        return {
            "contents": [{"uri": uri, "mimeType": "text/markdown", "text": doctrine.read_text(encoding="utf-8")}],
        }
    if uri.startswith("nurb://card/"):
        part = uri.removeprefix("nurb://card/")
        # A part name is a module stem: no separators, no dot-leading names.
        # Anything else would resolve outside parts/ (nurb://card/..\..\x.md
        # reads an arbitrary .md file), which is the one thing this server
        # promises not to do.
        if (
            not part
            or part in (".", "..")
            or part.startswith(".")
            or "/" in part
            or "\\" in part
        ):
            raise McpError(-32002, f"invalid card resource: {part!r}")
        card = (project / "parts" / f"{part}.md").resolve()
        if not card.is_file() or card.parent != (project / "parts").resolve():
            raise McpError(-32002, f"no card for {part}")
        return {"contents": [{"uri": uri, "mimeType": "text/markdown", "text": card.read_text(encoding="utf-8")}]}
    raise McpError(-32002, f"unknown resource: {uri}")


def _handle(message, project):
    """Dispatch one decoded MCP message, returning a response object or None
    for notifications."""
    method = message.get("method")
    if method == "initialize":
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": NAME, "version": VERSION},
        }
    if method in ("notifications/initialized", "notifications/cancelled"):
        return None
    if method == "ping":
        return {}
    if method == "tools/list":
        from .plugins import registry

        return {"tools": TOOLS + registry.all_mcp_tool_defs()}
    if method == "tools/call":
        from .plugins import registry

        name = message.get("params", {}).get("name", "")
        arguments = message.get("params", {}).get("arguments")
        # A plugin tool is dispatched by the plugin registry; a builtin tool
        # keeps its existing path. A name in neither set errors below.
        if registry.has_mcp_tool(name):
            result = registry.call_mcp_tool(name, arguments)
            if result is not None:
                return result
            # The tool is listed (its manifest declared it) but the plugin
            # registered no handler for it. "unknown tool" would be a lie,
            # so say what is actually missing.
            raise McpError(-32602, f"plugin tool {name!r} has no handler")
        return _call_tool(name, arguments, project)
    if method == "resources/list":
        return {"resources": _resources(project)}
    if method == "resources/read":
        return _read_resource(message.get("params", {}).get("uri", ""), project)
    raise McpError(-32601, f"method not found: {method}")


def serve(project):
    """The stdio loop: read one JSON object per line, answer requests, ignore
    notifications, keep the server alive across tool failures."""
    project = pathlib.Path(project).resolve()
    from .plugins import load_all

    load_all(project)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
            request_id = message.get("id")
            response = _handle(message, project)
        except json.JSONDecodeError as exc:
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": f"parse error: {exc}"}}) + "\n")
            sys.stdout.flush()
            continue
        except McpError as exc:
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": request_id, "error": {"code": exc.code, "message": exc.message}}) + "\n")
            sys.stdout.flush()
            continue
        except Exception as exc:  # never let one bad request kill the server
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": request_id, "error": {"code": -32603, "message": str(exc)}}) + "\n")
            sys.stdout.flush()
            continue
        if response is not None:
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": request_id, "result": response}) + "\n")
            sys.stdout.flush()


def main(argv=None):
    from .cli import project_root

    parser = argparse.ArgumentParser(prog="nurb mcp", description="serve nurb's commands over the Model Context Protocol (stdio)")
    parser.add_argument("--project", help="the nurb project to serve (default: the nearest project from cwd)")
    args = parser.parse_args(argv)
    project = pathlib.Path(args.project) if args.project else project_root()
    serve(project)


if __name__ == "__main__":
    main()
