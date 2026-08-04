"""The agent CLIs a row can be run on.

A row is measured through a harness's own CLI on the contributor's own subscription,
because that is how nurb is actually used: the score belongs to the model, the harness,
and the shipped skill together. An adapter is a command line and a usage parser,
nothing more; anything smarter belongs to the harness itself.

Usage parsing is best-effort on purpose. A harness that stops reporting cost still
produces a score; the row just carries less metadata.
"""

import contextlib
import json
import os
import pathlib
import shutil
import subprocess
import tempfile


class ClaudeCode:
    """claude -p, print mode. --effort is native (low, medium, high, xhigh, max).

    Permissions are skipped because the trial runs unattended in a throwaway project
    directory; that is the same trust model as any headless agent run on this machine.
    """

    name = "claude"

    def environment(self, env):
        return contextlib.nullcontext(dict(env))

    def command(self, prompt, model=None, effort=None, instructions=None):
        cmd = [
            "claude",
            "-p",
            prompt,
            "--output-format",
            "stream-json",
            "--verbose",
            "--safe-mode",
            "--strict-mcp-config",
            "--no-session-persistence",
            "--dangerously-skip-permissions",
        ]
        if instructions:
            cmd += ["--append-system-prompt", instructions]
        if model:
            cmd += ["--model", model]
        if effort:
            cmd += ["--effort", effort]
        return cmd

    def usage(self, stdout):
        result = None
        for line in reversed(stdout.splitlines()):
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict) and (event.get("type") == "result" or "usage" in event):
                result = event
                break
        if result is None:
            return {}
        keep = {}
        for key in ("total_cost_usd", "num_turns", "duration_ms"):
            if key in result:
                keep[key] = result[key]
        tokens = result.get("usage") or {}
        if not isinstance(tokens, dict):
            return keep
        for key in ("input_tokens", "output_tokens"):
            if key in tokens:
                keep[key] = tokens[key]
        return keep


class Codex:
    """codex exec, non-interactive mode, in codex's own workspace-write sandbox."""

    name = "codex"

    @contextlib.contextmanager
    def environment(self, env):
        source = pathlib.Path(
            env.get("CODEX_HOME", pathlib.Path.home() / ".codex")
        ).expanduser().resolve()
        auth = source / "auth.json"
        if not auth.is_file():
            raise RuntimeError(f"codex subscription auth not found at {auth}")
        with tempfile.TemporaryDirectory(prefix="nurb-codex-home-") as raw:
            home = pathlib.Path(raw)
            os.symlink(auth, home / "auth.json")
            clean = dict(env)
            clean["CODEX_HOME"] = str(home)
            yield clean

    def command(self, prompt, model=None, effort=None, instructions=None):
        cmd = [
            "codex",
            "exec",
            prompt,
            "--json",
            "--skip-git-repo-check",
            "--ignore-user-config",
            "--ignore-rules",
            "--ephemeral",
            "-s",
            "workspace-write",
        ]
        if model:
            cmd += ["-m", model]
        if effort:
            cmd += ["-c", f"model_reasoning_effort={effort}"]
        return cmd

    def usage(self, stdout):
        # JSONL events; the token_count event carries the totals when present.
        for line in reversed(stdout.splitlines()):
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict):
                continue
            info = event.get("info") or event.get("usage") or {}
            if isinstance(info, dict):
                tokens = {
                    k: info[k]
                    for k in ("input_tokens", "output_tokens", "total_tokens")
                    if k in info
                }
                if tokens:
                    return tokens
        return {}


HARNESSES = {h.name: h for h in (ClaudeCode(), Codex())}


def version(name):
    """The harness's own version string, recorded on every row: two runs of the same
    model through different harness versions are different rows."""
    if shutil.which(name) is None:
        return None
    try:
        done = subprocess.run([name, "--version"], capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return (done.stdout or done.stderr).strip().splitlines()[0] or None
