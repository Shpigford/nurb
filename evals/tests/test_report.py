"""The report is arithmetic over rows; every column has to be checkable by hand."""

import json
import pathlib

import pytest

from nurb_evals import report


def _row(score, *, built=True, lint=1.0, dims=1.0, flex=1.0, trial=1, seed=13,
         model="m", effort="high", harness="claude", tokens=(100, 900), wall=100.0,
         error=None, benchmark_revision="abc123def456"):
    row = {
        "task": "cable_clip", "seed": seed, "trial": trial, "harness": harness,
        "harness_version": "2.1.220 (Claude Code)", "model": model, "effort": effort,
        "nurb_version": "0.9.0", "benchmark_version": "0.1.0",
        "benchmark_revision": benchmark_revision,
        "built": built, "score": score,
        "stages": {"lint": lint, "dims": dims, "flex": flex},
        "error": error, "harness_s": wall,
        "usage": {"input_tokens": tokens[0], "output_tokens": tokens[1]} if tokens else {},
    }
    return row


def test_pass_at_k_is_the_unbiased_estimator():
    assert report.pass_at(1, 3, 3) == 1.0
    assert report.pass_at(1, 3, 1) == pytest.approx(1 / 3)
    assert report.pass_at(3, 3, 1) == 1.0
    assert report.pass_at(3, 3, 0) == 0.0
    assert report.pass_at(3, 1, 1) == 1.0, "k clamps to the trial count"


def test_stage_means_condition_on_the_gate():
    rows = [
        _row(1.0, trial=1),
        _row(0.0, trial=2, built=False, lint=0.0, dims=0.0, flex=0.0, error="2 solids"),
    ]
    (summary,) = report.summarize(rows)
    assert summary["score"] == 0.5
    assert summary["built"] == 0.5
    assert summary["lint"] == 1.0, "the gate failure's zero stages stay out of lint"
    assert summary["pass@1"] == 0.5
    assert summary["pass@3"] == 1.0
    assert summary["tokens"] == 1000
    assert summary["wall_s"] == 100.0


def test_built_means_past_the_gate_not_merely_geometry():
    two_solids = _row(0.0, built=True, error="2 solids, expected exactly 1")
    assert report.built(two_solids) is False
    for row, expect in (
        (_row(0.729), True),
        (_row(0.0, error="claude exited 1"), False),
        (_row(0.0, error=None), True),
    ):
        del row["built"]
        assert report.built(row) is expect, "rows from before the field infer it"


def test_identity_separates_groups_and_ranking_is_by_score():
    rows = [
        _row(0.5, model="small"),
        _row(1.0, model="big"),
        _row(0.9, model="big", effort="low"),
    ]
    summary = report.summarize(rows)
    assert [(r["model"], r["effort"]) for r in summary] == [
        ("big", "high"), ("big", "low"), ("small", "high"),
    ]


def test_identity_separates_benchmark_revisions():
    summary = report.summarize([
        _row(1.0, benchmark_revision="aaaaaaaaaaaa"),
        _row(0.5, benchmark_revision="bbbbbbbbbbbb"),
    ])
    assert len(summary) == 2
    assert {r["benchmark_revision"] for r in summary} == {"aaaaaaaaaaaa", "bbbbbbbbbbbb"}


def test_table_is_markdown_with_one_line_per_group(tmp_path):
    sink = tmp_path / "results.jsonl"
    with open(sink, "w", encoding="utf-8") as out:
        for trial in (1, 2, 3):
            out.write(json.dumps(_row(1.0, trial=trial)) + "\n")
    text = report.table(report.summarize(report.rows_from([tmp_path])))
    assert "## cable_clip (seed 13)" in text
    assert "| claude 2.1.220 | 0.9.0/0.1.0@abc123def456 | m | high | 3 | 1.000 | 1.00 |" in text
    assert "1.000 / 1.000 / 1.000" in text
    assert "gate failures as zeros" in text, "the column semantics travel with the table"


def test_missing_usage_and_wall_render_as_dashes():
    (summary,) = report.summarize([_row(1.0, tokens=None, wall=None)])
    assert summary["tokens"] is None
    text = report.table([summary])
    line = next(l for l in text.splitlines() if l.startswith("| claude"))
    assert "| - | - |" in line


def test_committed_submission_artifacts_are_complete_and_sanitized():
    submissions = pathlib.Path(__file__).parents[1] / "submissions"
    rows = 0
    for result_file in sorted(submissions.glob("*/results.jsonl")):
        for line in result_file.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            rows += 1
            assert row["nurb_version"] and row["benchmark_version"]
            assert len(row["benchmark_revision"]) == 12
            transcript = (
                result_file.parent / row["task"] / f"trial_{row['trial']}" / "transcript.txt"
            )
            source = (
                result_file.parent / row["task"] / f"trial_{row['trial']}"
                / "project" / "parts" / f"{row['task']}.py"
            )
            assert source.is_file() and source.read_text(encoding="utf-8").strip()
            for artifact in (transcript, source):
                text = artifact.read_text(encoding="utf-8")
                assert "/Users/" not in text and "/home/" not in text
                assert "joshpigford" not in text.lower() and "shpigford" not in text.lower()
    # rows == 0 is a legal state: the board was reset before first deploy and fills
    # from community and maintainer runs of the released pipeline.


def test_committed_report_matches_the_submissions(tmp_path):
    """REPORT.md is generated, never hand-edited, so submissions and report can
    never drift; the wizard regenerates it with every staged contribution."""
    regenerated = report.write(out=tmp_path / "REPORT.md").read_text(encoding="utf-8")
    committed = (pathlib.Path(__file__).parents[1] / "REPORT.md").read_text(encoding="utf-8")
    assert committed == regenerated, "REPORT.md is stale: run python -m nurb_evals.report --write"


def test_site_page_renders_from_the_committed_submissions():
    """The benchmarks page is generated from the same rows as the report, so it can
    never disagree with it. Structure is asserted, not numbers: rows will change."""
    from nurb_evals import site
    from nurb_evals.report import rows_from, summarize

    paths = sorted(
        str(p) for p in site.SUBMISSIONS.iterdir() if (p / "results.jsonl").is_file()
    )
    page = site.render(summarize(rows_from(paths)))
    for token in ("{jobs}", "{cards}", "{trial_count}", "{job_count}"):
        assert token not in page
    for title, _ in site.JOBS.values():
        assert title in page
    # With rows on file the page shows per-part times; with none, the empty state.
    assert "min/part" in page or "No rows on file yet" in page
    committed = (site.SITE).read_text(encoding="utf-8")
    assert committed == page, "site/benchmarks.html is stale: run python -m nurb_evals.site"
