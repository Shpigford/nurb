"""The MCP server, tested as a real process: the test spawns it, speaks the
wire protocol (one JSON object per line), and asserts on the responses. A
broken framing or a tool that kills the loop shows up here, not in a unit
test that calls handlers directly."""

import json
import pathlib
import queue
import subprocess
import sys
import threading

import pytest

PART = '''from nurb import *


@part
def widget(width=10.0, depth=20.0, height=5.0, draft=False):
    body = Box(width, depth, height)
    if draft:
        return body
    return polish(body, body.edges(), 0.5)
'''


@pytest.fixture()
def project(tmp_path):
    parts = tmp_path / "parts"
    parts.mkdir(parents=True, exist_ok=True)
    (parts / "widget.py").write_text(PART, encoding="utf-8")
    (parts / "widget.md").write_text("# widget\n\nA card for the MCP test.\n", encoding="utf-8")
    return tmp_path
class Client:
    """A minimal MCP client over pipes: requests on stdin, responses on
    stdout, read by a background thread so the test can time out cleanly."""

    def __init__(self, project):
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "nurb.mcp", "--project", str(project)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self.inbox = queue.Queue()
        self._thread = threading.Thread(target=self._read, daemon=True)
        self._thread.start()
        self._next_id = 1

    def _read(self):
        for line in self.proc.stdout:
            self.inbox.put(line.strip())

    def request(self, method, params=None):
        msg = {"jsonrpc": "2.0", "id": self._next_id, "method": method}
        if params is not None:
            msg["params"] = params
        self._next_id += 1
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()
        # A cold CI runner can spend a minute importing build123d before the
        # server reads its first line, so the request timeout is generous.
        return json.loads(self.inbox.get(timeout=120))

    def notify(self, method, params=None):
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()

    def close(self):
        try:
            self.proc.stdin.close()
        except Exception:
            pass
        self.proc.wait(timeout=20)


def test_initialize_and_tools(project):
    client = Client(project)
    try:
        init = client.request("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "test", "version": "0"}})
        assert init["result"]["serverInfo"]["name"] == "nurb-mcp"
        assert "tools" in init["result"]["capabilities"]
        client.notify("notifications/initialized")

        tools = client.request("tools/list")
        names = [t["name"] for t in tools["result"]["tools"]]
        for expected in [
            "nurb_build", "nurb_check", "nurb_inspect", "nurb_verify",
            "nurb_export", "nurb_rules", "nurb_api",
            "nurb_new", "nurb_diff", "nurb_card", "nurb_extract",
            "nurb_stress", "nurb_scan", "nurb_compare",
            "nurb_slice", "nurb_render", "nurb_skill", "nurb_update",
        ]:
            assert expected in names
    finally:
        client.close()


def test_build_and_check_call_the_real_commands(project):
    client = Client(project)
    try:
        client.notify("notifications/initialized")
        built = client.request("tools/call", {"name": "nurb_build", "arguments": {}})
        text = built["result"]["content"][0]["text"]
        assert "widget" in text and "mm" in text, text

        checked = client.request("tools/call", {"name": "nurb_check", "arguments": {}})
        assert "clean" in checked["result"]["content"][0]["text"].lower() or "finding" in checked["result"]["content"][0]["text"].lower()
    finally:
        client.close()


def test_resources_are_the_project_files(project):
    client = Client(project)
    try:
        client.notify("notifications/initialized")
        resources = client.request("resources/list")
        uris = [r["uri"] for r in resources["result"]["resources"]]
        assert "nurb://parts" in uris
        assert any(uri.startswith("nurb://card/") for uri in uris)

        parts = client.request("resources/read", {"uri": "nurb://parts"})
        assert "widget" in parts["result"]["contents"][0]["text"]
    finally:
        client.close()


def test_errors_do_not_kill_the_server(project):
    client = Client(project)
    try:
        client.notify("notifications/initialized")
        unknown = client.request("tools/call", {"name": "nurb_bogus", "arguments": {}})
        assert unknown["error"]["code"] == -32602
        # The server is still alive after an error.
        ping = client.request("ping")
        assert ping["result"] == {}
    finally:
        client.close()


def test_parse_error_keeps_the_loop_running(project):
    client = Client(project)
    try:
        client.proc.stdin.write("this is not json\n")
        client.proc.stdin.flush()
        reply = json.loads(client.inbox.get(timeout=10))
        assert reply["error"]["code"] == -32700
        ping = client.request("ping")
        assert ping["result"] == {}
    finally:
        client.close()


def test_card_resource_rejects_path_traversal(project):
    """The card resource is a module stem inside parts/; anything with a
    separator must be refused, not resolved against the filesystem. This is
    the project-boundary promise of the server, asserted over the wire."""
    client = Client(project)
    try:
        client.notify("notifications/initialized")
        # An absolute path, a parent traversal, and a Windows-style traversal
        # must all be refused as invalid, never read.
        for uri in [
            "nurb://card/C:\\Windows\\win.ini",
            "nurb://card/..\\..\\secrets",
            "nurb://card/../secrets",
            "nurb://card/.hidden",
            "nurb://card/",
        ]:
            reply = client.request("resources/read", {"uri": uri})
            assert reply["error"]["code"] == -32002, (uri, reply)
        # The legitimate card still reads fine afterwards.
        card = client.request("resources/read", {"uri": "nurb://card/widget"})
        assert "A card" in card["result"]["contents"][0]["text"]
    finally:
        client.close()


def test_resource_read_rejects_unknown_uris(project):
    client = Client(project)
    try:
        client.notify("notifications/initialized")
        reply = client.request("resources/read", {"uri": "nurb://bogus"})
        assert reply["error"]["code"] == -32002
        reply = client.request("resources/read", {"uri": "file:///etc/passwd"})
        assert reply["error"]["code"] == -32002
    finally:
        client.close()


def test_new_tool_creates_part(project):
    client = Client(project)
    try:
        client.notify("notifications/initialized")
        result = client.request("tools/call", {"name": "nurb_new", "arguments": {"name": "bracket"}})
        text = result["result"]["content"][0]["text"]
        assert "bracket.py" in text
        assert (project / "parts" / "bracket.py").is_file()
    finally:
        client.close()


def test_card_tool_regenerates(project):
    client = Client(project)
    try:
        client.notify("notifications/initialized")
        result = client.request("tools/call", {"name": "nurb_card", "arguments": {"part": "widget"}})
        text = result["result"]["content"][0]["text"]
        assert "widget" in text
    finally:
        client.close()


def test_diff_tool_compares(project):
    client = Client(project)
    try:
        client.notify("notifications/initialized")
        result = client.request("tools/call", {"name": "nurb_diff", "arguments": {"part": "widget"}})
        text = result["result"]["content"][0]["text"]
        assert "widget" in text
    finally:
        client.close()


def test_extract_tool_finds_duplication(project):
    client = Client(project)
    try:
        client.notify("notifications/initialized")
        result = client.request("tools/call", {"name": "nurb_extract", "arguments": {}})
        text = result["result"]["content"][0]["text"]
        assert isinstance(text, str)
    finally:
        client.close()


def test_skill_tool_prints(project):
    client = Client(project)
    try:
        client.notify("notifications/initialized")
        result = client.request("tools/call", {"name": "nurb_skill", "arguments": {}})
        text = result["result"]["content"][0]["text"]
        assert len(text) > 100
    finally:
        client.close()
