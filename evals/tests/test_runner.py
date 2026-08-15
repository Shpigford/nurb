"""The trial loop, proven without a subscription.

A stub harness stands in for claude/codex: same adapter shape, but its "agent" is a
one-line Python command. What these tests prove is the loop around the agent — fixture
materialized, part graded, row written, transcript kept — not any real model.
"""

import contextlib
import concurrent.futures
import json
import pathlib
import sys
import time

from nurb_evals import run as runner
from nurb_evals import scoring

EVALS = pathlib.Path(__file__).parents[1]
TASK = EVALS / "tasks" / "cable_clip"
SOLUTIONS = pathlib.Path(__file__).parent / "solutions"
GOOD = SOLUTIONS / "cable_clip" / "good.py"

task = scoring.load_task(TASK)
SEED = next(s for s in range(1000) if task.instance(s).dims["bundle"] == 8.0)


class Stub:
    """An 'agent' that plants a prepared solution, or nothing at all."""

    name = "stub"

    def __init__(self, source=None, part="cable_clip"):
        self.source = source
        self.part = part

    def environment(self, env):
        return contextlib.nullcontext(dict(env))

    def command(self, prompt, model=None, effort=None, instructions=None):
        assert instructions and instructions.startswith("#")
        if self.source is None:
            return ["python", "-c", "pass"]
        # Embed the solution's text rather than its path: the "agent" subprocess runs
        # with only the isolated nurb installation on its import and executable paths.
        text = pathlib.Path(self.source).read_text(encoding="utf-8")
        write = f"import pathlib; pathlib.Path('parts/{self.part}.py').write_text({text!r})"
        return ["python", "-c", write]

    def usage(self, stdout):
        return {"stub": True}


def test_a_trial_materializes_runs_and_grades(tmp_path):
    row = runner.trial(Stub(GOOD), TASK, SEED, 1, tmp_path)
    assert row["score"] == 1.0
    assert row["stages"] == {"lint": 1.0, "dims": 1.0, "flex": 1.0}
    assert row["usage"] == {"stub": True}
    project = tmp_path / "cable_clip" / "trial_1" / "project"
    assert (project / "measurements.toml").is_file()
    assert (project / "AGENTS.md").read_text().startswith("#"), "the shipped skill is seeded"
    assert (tmp_path / "cable_clip" / "trial_1" / "transcript.txt").exists()


def test_the_agent_project_is_not_inside_the_benchmark_checkout(tmp_path, monkeypatch):
    checkout = tmp_path / "benchmark"
    out = checkout / "results" / "stub"
    checkout.mkdir()
    (checkout / "grader-secret").write_text("task assertions", encoding="utf-8")
    monkeypatch.setenv("CONDUCTOR_WORKSPACE_PATH", str(checkout))

    class AncestorProbe(Stub):
        def environment(self, env):
            assert not any(name.startswith("CONDUCTOR_") for name in env)
            assert env["PWD"] not in str(out)
            return super().environment(env)

        def command(self, prompt, model=None, effort=None, instructions=None):
            script = (
                "import pathlib;"
                "here=pathlib.Path.cwd();"
                "print(any((p/'grader-secret').exists() for p in (here,*here.parents)));"
                f"pathlib.Path('parts/cable_clip.py').write_text({GOOD.read_text()!r})"
            )
            return ["python", "-c", script]

    row = runner.trial(AncestorProbe(GOOD), TASK, SEED, 1, out)
    assert row["score"] == 1.0
    slot = out / "cable_clip" / "trial_1"
    assert (slot / "transcript.txt").read_text(encoding="utf-8").strip() == "False"
    assert (slot / "project" / "parts" / "cable_clip.py").is_file()


def test_the_answer_key_checkout_is_not_discoverable_while_the_agent_runs(tmp_path):
    """The agent's nurb executable, Python, import path, and install metadata all
    belong to its throwaway runtime rather than the benchmark checkout."""

    class Peeker(Stub):
        def command(self, prompt, model=None, effort=None, instructions=None):
            script = (
                "import importlib.metadata, importlib.util, os, shutil, sys\n"
                f"checkout = {str(EVALS.parent)!r}\n"
                "dist = importlib.metadata.distribution('nurb')\n"
                "breadcrumbs = [shutil.which('nurb'), sys.executable, *sys.path, "
                "*os.environ['PATH'].split(os.pathsep), "
                "importlib.util.find_spec('nurb').origin, "
                "dist.read_text('direct_url.json')]\n"
                "print('LEAKED' if any(checkout in (p or '') for p in breadcrumbs) "
                "else 'hidden')\n"
                f"pathlib.Path('parts/cable_clip.py').write_text({GOOD.read_text()!r})\n"
            )
            return ["python", "-c", "import pathlib\n" + script]

    row = runner.trial(Peeker(GOOD), TASK, SEED, 1, tmp_path)
    assert row["score"] == 1.0
    transcript = (tmp_path / "cable_clip" / "trial_1" / "transcript.txt").read_text()
    assert "LEAKED" not in transcript
    assert transcript.strip() == "hidden"


def test_the_isolated_nurb_cli_builds_the_agent_project(tmp_path):
    class Builds(Stub):
        def command(self, prompt, model=None, effort=None, instructions=None):
            script = (
                "import pathlib,subprocess\n"
                f"pathlib.Path('parts/cable_clip.py').write_text({GOOD.read_text()!r})\n"
                "subprocess.run(['nurb', 'build', 'cable_clip'], check=True)\n"
            )
            return ["python", "-c", script]

    row = runner.trial(Builds(GOOD), TASK, SEED, 1, tmp_path)
    assert row["score"] == 1.0
    assert row["error"] is None


def test_trials_never_change_checkout_permissions(tmp_path, monkeypatch):
    chmod = runner.os.chmod

    def guarded(path, *args, **kwargs):
        if pathlib.Path(path).resolve().is_relative_to(EVALS.resolve()):
            raise AssertionError("a trial must not mutate shared checkout permissions")
        return chmod(path, *args, **kwargs)

    monkeypatch.setattr(runner.os, "chmod", guarded)
    assert runner.trial(Stub(GOOD), TASK, SEED, 1, tmp_path)["score"] == 1.0


def test_two_trials_can_run_concurrently(tmp_path):
    rendezvous = tmp_path / "rendezvous"
    rendezvous.mkdir()

    class Overlap(Stub):
        def __init__(self, marker):
            super().__init__(GOOD)
            self.marker = marker

        def command(self, prompt, model=None, effort=None, instructions=None):
            script = (
                "import pathlib,time\n"
                f"shared=pathlib.Path({str(rendezvous)!r})\n"
                f"(shared/{self.marker!r}).write_text('ready')\n"
                "deadline=time.monotonic()+20\n"
                "while len(list(shared.iterdir())) < 2 and time.monotonic() < deadline:\n"
                "    time.sleep(0.01)\n"
                "assert len(list(shared.iterdir())) == 2\n"
                f"pathlib.Path('parts/cable_clip.py').write_text({GOOD.read_text()!r})\n"
            )
            return ["python", "-c", script]

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(
            pool.map(
                lambda pair: runner.trial(pair[0], TASK, SEED, pair[1], tmp_path),
                ((Overlap("one"), 1), (Overlap("two"), 2)),
            )
        )
    assert [row["score"] for row in rows] == [1.0, 1.0]


def test_the_part_path_follows_the_task(tmp_path):
    """No task's file name is hardcoded in the runner: a second task grades the part
    at its own stated path."""
    bh_task = EVALS / "tasks" / "bundle_holder"
    bh = scoring.load_task(bh_task)
    seed = next(s for s in range(1000) if bh.instance(s).dims["bundle"] == 8.0)
    source = SOLUTIONS / "bundle_holder" / "good.py"
    row = runner.trial(Stub(source, part="bundle_holder"), bh_task, seed, 1, tmp_path)
    assert row["task"] == "bundle_holder"
    assert row["score"] == 1.0
    assert (tmp_path / "bundle_holder" / "trial_1" / "project" / "parts" / "bundle_holder.py").is_file()
    assert (tmp_path / "cable_clip" / "trial_1" / "project" / "parts" / "cable_clip.py").is_file() is False


def test_an_agent_that_writes_nothing_scores_zero(tmp_path):
    row = runner.trial(Stub(None), TASK, SEED, 1, tmp_path)
    assert row["score"] == 0.0
    assert "no part file" in row["error"]


def test_rows_carry_the_matrix_identity(tmp_path):
    row = runner.trial(Stub(GOOD), TASK, SEED, 2, tmp_path, model="some-model", effort="high")
    assert (row["harness"], row["model"], row["effort"]) == ("stub", "some-model", "high")
    assert row["seed"] == SEED and row["trial"] == 2
    # The row pins whatever nurb is actually installed, never a literal that rots
    # on every release.
    import importlib.metadata

    assert row["nurb_version"] == importlib.metadata.version("nurb")
    assert row["benchmark_version"] == importlib.metadata.version("nurb-evals")
    assert len(row["benchmark_revision"]) == 12
    json.dumps(row)  # a row must survive the JSONL sink


def test_runner_source_changes_the_benchmark_revision(monkeypatch):
    before = scoring.benchmark_identity(TASK)["benchmark_revision"]
    run_path = pathlib.Path(runner.__file__).resolve()
    read_bytes = pathlib.Path.read_bytes

    def changed(path):
        content = read_bytes(path)
        return content + b"\n# changed runner\n" if path.resolve() == run_path else content

    monkeypatch.setattr(pathlib.Path, "read_bytes", changed)
    after = scoring.benchmark_identity(TASK)["benchmark_revision"]
    assert after != before


def test_a_preseeded_trial_directory_is_refused(tmp_path):
    """The cheat the verification pass found: plant a known-good part where the trial
    will grade, and a do-nothing agent earns a perfect, audit-plausible row."""
    import shutil

    import pytest

    planted = tmp_path / "cable_clip" / "trial_1" / "project" / "parts"
    planted.mkdir(parents=True)
    shutil.copy(GOOD, planted / "cable_clip.py")
    with pytest.raises(RuntimeError, match="fresh directory"):
        runner.trial(Stub(None), TASK, SEED, 1, tmp_path)


def test_timeout_kills_harness_descendants(tmp_path):
    class SpawnsChild(Stub):
        name = "spawns-child"

        def command(self, prompt, model=None, effort=None, instructions=None):
            child = (
                "import pathlib,time;"
                "pathlib.Path('child_started').write_text('yes');"
                "time.sleep(1.5);"
                "pathlib.Path('orphaned').write_text('yes')"
            )
            parent = (
                "import pathlib,subprocess,sys,time\n"
                f"subprocess.Popen([sys.executable, '-c', {child!r}])\n"
                "while not pathlib.Path('child_started').exists(): time.sleep(0.01)\n"
                "time.sleep(60)"
            )
            return ["python", "-c", parent]

    runner.trial(SpawnsChild(), TASK, SEED, 1, tmp_path, timeout=1.0)
    project = tmp_path / "cable_clip" / "trial_1" / "project"
    assert (project / "child_started").is_file(), "the child ran before the timeout"
    time.sleep(0.8)
    assert not (project / "orphaned").exists(), "the timeout must kill the whole process group"


def test_usage_parsers_swallow_json_that_is_not_an_object():
    from nurb_evals.harness import HARNESSES

    for garbage in ("[]", "null", "3", '"quoted"', "[]\nnull\n3"):
        assert HARNESSES["claude"].usage(garbage) == {}
        assert HARNESSES["codex"].usage(garbage) == {}


def test_the_preamble_forbids_the_interactive_directives():
    """The shipped skill tells agents to start `nurb dev` and hand over a URL; headless
    trials must override that or models burn the clock waiting on a viewer."""
    assert "nurb dev" in runner.PREAMBLE
    assert "never" in runner.PREAMBLE


def test_real_adapters_build_the_documented_commands():
    from nurb_evals.harness import HARNESSES

    claude = HARNESSES["claude"].command("do it", model="opus", effort="high")
    assert claude[:2] == ["claude", "-p"] and "do it" in claude
    assert "--dangerously-skip-permissions" in claude
    assert ["--output-format", "stream-json"] == claude[
        claude.index("--output-format"):claude.index("--output-format") + 2
    ]
    assert "--safe-mode" in claude and "--strict-mcp-config" in claude
    assert ["--model", "opus"] == claude[claude.index("--model"):claude.index("--model") + 2]
    assert ["--effort", "high"] == claude[claude.index("--effort"):claude.index("--effort") + 2]

    codex = HARNESSES["codex"].command("do it", model="gpt-5", effort="high")
    assert codex[:3] == ["codex", "exec", "do it"]
    assert "-c" in codex and "model_reasoning_effort=high" in codex
    assert "--ignore-user-config" in codex and "--ignore-rules" in codex
    assert "--ephemeral" in codex
    assert ["-s", "workspace-write"] == codex[codex.index("-s"):codex.index("-s") + 2]


def test_codex_runs_with_only_subscription_auth_in_its_home(tmp_path):
    from nurb_evals.harness import HARNESSES

    source = tmp_path / "source"
    source.mkdir()
    (source / "auth.json").write_text('{"token": "test"}', encoding="utf-8")
    (source / "AGENTS.md").write_text("personal instructions", encoding="utf-8")
    (source / "config.toml").write_text("personal = true", encoding="utf-8")

    with HARNESSES["codex"].environment({"CODEX_HOME": str(source)}) as env:
        clean = pathlib.Path(env["CODEX_HOME"])
        assert clean != source
        assert {path.name for path in clean.iterdir()} == {"auth.json"}
        assert (clean / "auth.json").read_text(encoding="utf-8") == '{"token": "test"}'
    assert not clean.exists()


def test_claude_usage_parses_the_result_json():
    from nurb_evals.harness import HARNESSES

    stdout = json.dumps(
        {"type": "result", "total_cost_usd": 0.12, "num_turns": 7,
         "usage": {"input_tokens": 100, "output_tokens": 200}}
    )
    usage = HARNESSES["claude"].usage(stdout)
    assert usage == {"total_cost_usd": 0.12, "num_turns": 7, "input_tokens": 100, "output_tokens": 200}
    assert HARNESSES["claude"].usage("not json") == {}


def test_claude_usage_parses_the_final_stream_event():
    from nurb_evals.harness import HARNESSES

    stdout = "\n".join(
        (
            json.dumps({"type": "assistant", "message": {"content": "working"}}),
            json.dumps(
                {
                    "type": "result",
                    "total_cost_usd": 0.2,
                    "num_turns": 4,
                    "usage": {"input_tokens": 50, "output_tokens": 80},
                }
            ),
        )
    )
    assert HARNESSES["claude"].usage(stdout) == {
        "total_cost_usd": 0.2,
        "num_turns": 4,
        "input_tokens": 50,
        "output_tokens": 80,
    }


def test_runner_requires_the_complete_row_identity():
    import pytest

    with pytest.raises(SystemExit):
        runner.parser().parse_args(["--harness", "claude", "--seed", str(SEED)])
    args = runner.parser().parse_args(
        [
            "--harness",
            "claude",
            "--seed",
            str(SEED),
            "--model",
            "haiku",
            "--effort",
            "low",
        ]
    )
    assert (args.model, args.effort) == ("haiku", "low")
    for trials in ("0", "-1"):
        with pytest.raises(SystemExit):
            runner.parser().parse_args(
                [
                    "--harness", "claude", "--seed", str(SEED),
                    "--model", "haiku", "--effort", "low", "--trials", trials,
                ]
            )
