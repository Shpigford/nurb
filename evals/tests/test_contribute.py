"""The contribution wizard, end to end against the stub harness.

The wizard's promise is that a contributor never types a model spelling, never
hand-sanitizes a transcript, and ends with a submission-ready directory. The test
drives the whole flow non-interactively the way an agent would, with the module's
paths redirected into a scratch tree so nothing touches the real submissions/.
"""

import json
import os
import pathlib
import shutil
import sys

import pytest

from nurb_evals import contribute
from nurb_evals import harness as harnesses
from test_runner import GOOD, SEED, Stub


def test_catalog_offers_real_ids():
    book = contribute.catalog()
    assert {m["id"] for m in book["claude"]} >= {"fable", "opus", "sonnet", "haiku"}
    for entries in book.values():
        for entry in entries:
            assert entry["default_effort"] in entry["efforts"]


def test_sanitize_scrubs_longest_first(tmp_path):
    pairs = contribute.replacements(tmp_path / "project")
    dirty = f"built at {tmp_path}/project/parts/x.py in {pathlib.Path.home()}"
    clean = contribute.sanitize(dirty, pairs)
    assert str(pathlib.Path.home()) not in clean and "<workspace>" in clean


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

    from nurb_evals import site

    monkeypatch.setattr(contribute, "EVALS", root)
    monkeypatch.setattr(site, "SITE", root / "benchmarks.html")
    monkeypatch.setattr(contribute.shutil, "which", lambda name: "/usr/bin/true")
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
        ],
    )
    contribute.main()

    sub = root / "submissions" / "stub-stub-model-low"
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
    # The wizard regenerates the published page itself, so a PR ships with the
    # benchmarks.html its rows produce and the stale-page test passes as opened.
    page = (root / "benchmarks.html").read_text(encoding="utf-8")
    assert "stub-model" in page
    assert "stub-model" in (root / "REPORT.md").read_text(encoding="utf-8")

    printed = capsys.readouterr().out
    assert "Staged in THIS checkout" in printed and str(root) in printed
    assert "benchmark row: stub-stub-model-low" in printed
    assert "skip if you have push access" in printed
