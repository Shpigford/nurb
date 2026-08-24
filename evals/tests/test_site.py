"""The page is editorial over the same rows the report uses, so what it can claim
about a model is bounded by what that model actually ran."""

from nurb_evals import report, site


def _row(task, score, *, model="m", effort="high", harness="claude", wall=100.0, trials=1):
    return {
        "task": task, "seed": 13, "trial": trials, "harness": harness,
        "harness_version": "2.1.220 (Claude Code)", "model": model, "effort": effort,
        "nurb_version": "0.9.0", "benchmark_version": "0.1.0",
        "benchmark_revision": "abc123def456",
        "built": True, "score": score,
        "stages": {"lint": 1.0, "dims": score, "flex": score},
        "error": None, "harness_s": wall,
        "usage": {"input_tokens": 100, "output_tokens": 900},
    }


def test_answer_card_prefers_the_model_that_ran_every_job():
    """A clean sweep of half the board is a thinner claim than a near-clean sweep of
    all of it, so the short answer never points at an unfinished row."""
    partial = [_row("cable_clip", 1.0, effort="high")]
    complete = [_row(task, 1.0, effort="low") for task in site.JOBS]
    complete[-1]["score"] = 0.5

    combos = site._combos(report.summarize(partial + complete))
    cards = site._answers(combos)

    assert "at low effort" in cards
    assert "at high effort" not in cards


def test_answer_card_falls_back_to_a_partial_row_when_it_is_all_there_is():
    combos = site._combos(report.summarize([_row("cable_clip", 1.0, effort="high")]))
    assert "at high effort" in site._answers(combos)


def test_every_combo_on_the_board_has_a_verdict():
    """A combo without one renders numbers-only, which is a gap to fill, not a state
    to ship: the verdicts are the reason publishing is a separate step from merging."""
    paths = sorted(
        str(p) for p in site.SUBMISSIONS.iterdir() if (p / "results.jsonl").is_file()
    )
    combos = site._combos(report.summarize(report.rows_from(paths)))
    missing = [key[:3] for key, _ in combos if key[:3] not in site.VERDICTS]
    assert not missing, f"combos on the board with no verdict: {missing}"


def test_no_verdict_outlives_the_rows_it_describes():
    paths = sorted(
        str(p) for p in site.SUBMISSIONS.iterdir() if (p / "results.jsonl").is_file()
    )
    combos = site._combos(report.summarize(report.rows_from(paths)))
    on_board = {key[:3] for key, _ in combos}
    orphans = [key for key in site.VERDICTS if key not in on_board]
    assert not orphans, f"verdicts for combos with no rows: {orphans}"
