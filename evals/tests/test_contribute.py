"""The contribution wizard, end to end against the stub harness.

The wizard's promise is that a contributor never types a model spelling, never
hand-sanitizes a transcript, and ends with a submission-ready directory. The test
drives the whole flow non-interactively the way an agent would, with the module's
paths redirected into a scratch tree so nothing touches the real submissions/.
"""

import concurrent.futures
import json
import os
import pathlib
import re
import shutil
import sys

import pytest

from nurb_evals import contribute
from nurb_evals import harness as harnesses
from test_runner import GOOD, SEED, Stub


def test_catalog_offers_real_ids():
    book = contribute.catalog()
    claude_ids = {m["id"] for m in book["claude"]}
    assert {"claude-fable-5", "claude-opus-5", "claude-sonnet-5"} <= claude_ids
    # Floating aliases would pool different models into one leaderboard row.
    assert not claude_ids & {"fable", "opus", "sonnet", "haiku"}
    for entries in book.values():
        for entry in entries:
            assert entry["default_effort"] in entry["efforts"]


def test_most_needed_ranks_empty_rows_first(tmp_path):
    sub = tmp_path / "submissions" / "claude-opus-high-abc123"
    sub.mkdir(parents=True)
    rows = [{"harness": "claude", "model": "claude-opus-5", "effort": "high"}] * 2
    (sub / "results.jsonl").write_text("\n".join(json.dumps(r) for r in rows))

    counts = contribute.board_counts(root=tmp_path)
    assert counts == {("claude", "claude-opus-5", "high"): 2}

    book = {
        "claude": [
            {"id": "claude-opus-5", "label": "Opus", "efforts": ["high"], "default_effort": "high"},
            {"id": "claude-sonnet-5", "label": "Sonnet", "efforts": ["high"], "default_effort": "high"},
        ],
        "codex": [{"id": "gpt", "label": "GPT", "efforts": ["medium"], "default_effort": "medium"}],
    }
    # sonnet has no rows yet; codex is not installed, so its empty row cannot win
    assert contribute.most_needed(book, counts, ["claude"])[1]["id"] == "claude-sonnet-5"
    # ties fall to menu order, which lists flagships first
    assert contribute.most_needed(book, {}, ["claude"])[1]["id"] == "claude-opus-5"
    assert contribute.most_needed(book, counts, []) is None


def test_wizard_offers_the_most_needed_pick(tmp_path, monkeypatch, capsys):
    """The first menu option answers harness, model, and effort in one keystroke
    with the combo holding the fewest pooled trials, so the paste-the-curl-line
    path produces the row the leaderboard actually needs."""
    root = tmp_path / "evals"
    (root / "tasks").mkdir(parents=True)
    real = contribute.EVALS
    os.symlink(real / "tasks" / "cable_clip", root / "tasks" / "cable_clip")
    (root / "models.toml").write_text(
        '[[stub]]\nid = "stub-model"\nlabel = "Stub Model"\n'
        'efforts = ["low", "high"]\ndefault_effort = "low"\n'
    )

    monkeypatch.setattr(contribute, "EVALS", root)
    which = contribute.shutil.which
    monkeypatch.setattr(
        contribute.shutil,
        "which",
        lambda name: "/usr/bin/true" if name == "stub" else which(name),
    )
    monkeypatch.setitem(harnesses.HARNESSES, "stub", Stub(GOOD))
    monkeypatch.setattr(contribute, "detected", lambda: [("stub", "1.0")])
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    answers = iter(["1", "1"])  # the most-needed pick; then one round
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    monkeypatch.setattr(
        sys,
        "argv",
        ["contribute", "--tasks", "cable_clip", "--seed", str(SEED), "--pr", "no"],
    )
    contribute.main()

    printed = capsys.readouterr().out
    assert "helps the board most" in printed
    assert "no runs on the board yet" in printed
    sub = next((root / "submissions").glob("stub-stub-model-low-*"))
    row = json.loads((sub / "results.jsonl").read_text().splitlines()[0])
    assert (row["model"], row["effort"]) == ("stub-model", "low")


def test_sanitize_scrubs_longest_first(tmp_path):
    pairs = contribute.replacements(tmp_path / "project")
    dirty = f"built at {tmp_path}/project/parts/x.py in {pathlib.Path.home()}"
    clean = contribute.sanitize(dirty, pairs)
    assert str(pathlib.Path.home()) not in clean and "<workspace>" in clean


def test_sanitize_drops_byte_arrays_that_hide_paths(tmp_path):
    home = str(pathlib.Path.home())
    encoded = ",".join(str(b) for b in home.encode())
    dirty = '{"output":[%s],"output_for_prompt":"%s"}' % (encoded, home)
    clean = contribute.sanitize(dirty, contribute.replacements(tmp_path / "project"))
    assert clean == '{"output":[],"output_for_prompt":"<home>"}'


def test_next_trial_continues_numbering(tmp_path):
    (tmp_path / "cable_clip" / "trial_1").mkdir(parents=True)
    (tmp_path / "cable_clip" / "trial_2").mkdir()
    assert contribute.next_trial(tmp_path, "cable_clip") == 3
    assert contribute.next_trial(tmp_path, "leg_cup") == 1


def test_wizard_runs_and_stages_a_sanitized_submission(tmp_path, monkeypatch, capsys):
    root = tmp_path / "evals"
    (root / "tasks").mkdir(parents=True)
    real = contribute.EVALS
    shutil.copy(real / "models.toml", root / "models.toml")
    os.symlink(real / "tasks" / "cable_clip", root / "tasks" / "cable_clip")

    monkeypatch.setattr(contribute, "EVALS", root)
    which = contribute.shutil.which
    monkeypatch.setattr(
        contribute.shutil,
        "which",
        lambda name: "/usr/bin/true" if name == "stub" else which(name),
    )
    monkeypatch.setitem(harnesses.HARNESSES, "stub", Stub(GOOD))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "contribute",
            "--harness", "stub",
            "--model", "stub-model",
            "--effort", "low",
            "--tasks", "cable_clip",
            "--seed", str(SEED),
            "--pr", "no",
        ],
    )
    contribute.main()

    # One directory per run, unique so ten runs (or three at once) never collide.
    subs = list((root / "submissions").glob("stub-stub-model-low-*"))
    assert len(subs) == 1
    sub = subs[0]
    assert re.fullmatch(r"stub-stub-model-low-[0-9a-f]{6}", sub.name)
    rows = [
        json.loads(line)
        for line in (sub / "results.jsonl").read_text().splitlines()
        if line.strip()
    ]
    assert len(rows) == 1 and rows[0]["score"] == 1.0
    assert rows[0]["model"] == "stub-model" and rows[0]["effort"] == "low"
    part = sub / "cable_clip" / "trial_1" / "project" / "parts" / "cable_clip.py"
    assert part.is_file()
    assert (sub / "cable_clip" / "trial_1" / "transcript.txt").exists()
    for staged in sub.rglob("*"):
        if staged.is_file():
            assert str(pathlib.Path.home()) not in staged.read_text(errors="replace")

    printed = capsys.readouterr().out
    # The last line on screen always carries the run's progress, so a person
    # glancing at a long run never has to count finished trials by hand.
    assert "░░░░░░░░░░░░░░░░░░ 0/1" in printed
    assert "██████████████████ 1/1" in printed
    assert "Staged in this checkout" in printed and str(root) in printed
    assert f"benchmark run: {sub.name}" in printed
    assert f"git add evals/submissions/{sub.name}" in printed
    assert "skip if you have push access" in printed


def test_wizard_asks_for_rounds_and_says_why(tmp_path, monkeypatch, capsys):
    """With a terminal and no --trials, the wizard asks how many rounds and gives
    the reason (more rounds, steadier average). The typed number IS the round
    count: answering 2 runs exactly two rounds."""
    root = tmp_path / "evals"
    (root / "tasks").mkdir(parents=True)
    real = contribute.EVALS
    shutil.copy(real / "models.toml", root / "models.toml")
    os.symlink(real / "tasks" / "cable_clip", root / "tasks" / "cable_clip")

    monkeypatch.setattr(contribute, "EVALS", root)
    which = contribute.shutil.which
    monkeypatch.setattr(
        contribute.shutil,
        "which",
        lambda name: "/usr/bin/true" if name == "stub" else which(name),
    )
    monkeypatch.setitem(harnesses.HARNESSES, "stub", Stub(GOOD))
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    answers = iter(["2"])  # the answer is the round count itself
    asked = []

    def scripted(prompt=""):
        asked.append(prompt)
        return next(answers)

    monkeypatch.setattr("builtins.input", scripted)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "contribute",
            "--harness", "stub",
            "--model", "stub-model",
            "--effort", "low",
            "--tasks", "cable_clip",
            "--seed", str(SEED),
            "--pr", "no",
        ],
    )
    contribute.main()

    printed = capsys.readouterr().out
    assert any("How many rounds" in prompt for prompt in asked)
    assert "steadier average" in printed, "the wizard explains why rounds matter"
    sub = next((root / "submissions").glob("stub-stub-model-low-*"))
    rows = [
        json.loads(line)
        for line in (sub / "results.jsonl").read_text().splitlines()
        if line.strip()
    ]
    assert len(rows) == 2, "two rounds were asked for, two rows exist"


def test_wizard_runs_trials_in_parallel(tmp_path, monkeypatch):
    """--parallel runs trials concurrently: a barrier that only releases when all
    four trials are in flight at once would deadlock a sequential loop. Repeating a
    task keeps allocating new slots instead of assigning two workers the same one."""
    import threading

    root = tmp_path / "evals"
    (root / "tasks" / "cable_clip").mkdir(parents=True)
    shutil.copy(contribute.EVALS / "models.toml", root / "models.toml")
    monkeypatch.setattr(contribute, "EVALS", root)
    monkeypatch.setitem(harnesses.HARNESSES, "stub", Stub(GOOD))
    which = contribute.shutil.which
    monkeypatch.setattr(
        contribute.shutil,
        "which",
        lambda name: "/usr/bin/true" if name == "stub" else which(name),
    )

    barrier = threading.Barrier(4, timeout=30)

    def fake_trial(
        h, task_dir, seed, n, out, model=None, effort=None, timeout=None,
        cancel_event=None,
    ):
        barrier.wait()
        task = pathlib.Path(task_dir).name
        slot = out / task / f"trial_{n}"
        (slot / "project" / "parts").mkdir(parents=True)
        (slot / "transcript.txt").write_text("ok", encoding="utf-8")
        (slot / "project" / "parts" / f"{task}.py").write_text("# part", encoding="utf-8")
        return {
            "task": task, "seed": seed, "trial": n, "harness": h.name,
            "model": model, "effort": effort, "score": 1.0,
            "stages": {}, "error": None,
        }

    monkeypatch.setattr(contribute, "completed_trial", fake_trial)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "contribute",
            "--harness", "stub",
            "--model", "stub-model",
            "--effort", "low",
            "--trials", "2",
            "--parallel", "4",
            "--tasks", "cable_clip,cable_clip",
            "--seed", str(SEED),
            "--pr", "no",
        ],
    )
    contribute.main()

    sub = next((root / "submissions").glob("stub-stub-model-low-*"))
    rows = [json.loads(line) for line in (sub / "results.jsonl").read_text().splitlines() if line.strip()]
    assert sorted(r["trial"] for r in rows) == [1, 2, 3, 4]
    for n in (1, 2, 3, 4):
        assert (sub / "cable_clip" / f"trial_{n}" / "transcript.txt").is_file()


def test_trial_failure_cancels_an_earlier_slow_future():
    """Completion order matters: the first submitted job waits for cancellation,
    while the second fails and must be observed immediately to release it."""
    import threading

    cancel_event = threading.Event()
    first_started = threading.Event()

    def waits_for_cancel():
        first_started.set()
        assert cancel_event.wait(timeout=2), "later failure was hidden behind this future"
        raise concurrent.futures.CancelledError

    def fails():
        assert first_started.wait(timeout=2)
        raise RuntimeError("trial failed")

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(waits_for_cancel), pool.submit(fails)]
        with pytest.raises(RuntimeError, match="trial failed"):
            contribute._wait_for_trials(futures, cancel_event)
    assert cancel_event.is_set()


def test_open_pr_drives_git_and_gh_end_to_end(tmp_path, monkeypatch):
    """The wizard owns the submission: branch from origin's main, commit only this
    run's directory, push, PR. Faked git/gh log every invocation and pr create
    returns the URL."""
    import os

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "log"
    (bin_dir / "git").write_text(
        '#!/bin/sh\necho "git $@" >> %s\nexit 0\n' % log, encoding="utf-8"
    )
    (bin_dir / "gh").write_text(
        '#!/bin/sh\necho "gh $@" >> %s\n'
        'case "$1 $2" in "pr create") echo "https://github.com/Shpigford/nurb/pull/999";; esac\nexit 0\n' % log,
        encoding="utf-8",
    )
    for f in bin_dir.iterdir():
        f.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")

    url, problem = contribute.open_pr("stub-stub-model-low-abc123", tmp_path)
    assert problem is None
    assert url == "https://github.com/Shpigford/nurb/pull/999"
    logged = log.read_text(encoding="utf-8")
    for needle in (
        "git fetch origin main",
        "git checkout -b bench-stub-stub-model-low-abc123 FETCH_HEAD",
        "git add evals/submissions/stub-stub-model-low-abc123",
        "git commit -m benchmark run: stub-stub-model-low-abc123",
        "git push -u origin bench-stub-stub-model-low-abc123",
        "gh pr create --repo Shpigford/nurb --base main --head bench-stub-stub-model-low-abc123 --title benchmark run: stub-stub-model-low-abc123",
    ):
        assert needle in logged
