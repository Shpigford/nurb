"""The page is editorial over the same rows the report uses, so what it can claim
about a model is bounded by what that model actually ran."""

import math

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


def test_a_job_run_under_two_identities_pools_instead_of_losing_trials():
    """The report separates rows on harness version and benchmark revision; the card
    is coarser and must still carry every attempt. Grok ran the same jobs twice under
    two CLI versions, and folding by task alone silently kept one and dropped the
    other."""
    old = _row("cable_clip", 0.5)
    old["harness_version"] = "1.0.4 (old)"
    old["nurb_version"] = "0.19.2"
    new = [_row("cable_clip", 1.0), _row("cable_clip", 1.0)]

    ((_, tasks),) = site._combos(report.summarize([old] + new))
    pooled = tasks["cable_clip"]

    assert pooled["trials"] == 3
    assert sorted(pooled["scores"]) == [0.5, 1.0, 1.0]
    assert pooled["score"] == (0.5 + 1.0 + 1.0) / 3
    # Identity strings that no longer describe one group are dropped, not guessed.
    assert pooled["harness_version"] is None
    assert pooled["benchmark_revision"] == "abc123def456"


def test_every_submitted_trial_reaches_the_board():
    """The page promises every attempt shows as its own tick, so the count the cards
    render has to match the count on file."""
    paths = sorted(
        str(p) for p in site.SUBMISSIONS.iterdir() if (p / "results.jsonl").is_file()
    )
    summary = report.summarize(report.rows_from(paths))
    combos = site._combos(summary)
    rendered = sum(sum(r["trials"] for r in tasks.values()) for _, tasks in combos)
    assert rendered == sum(r["trials"] for r in summary)


def _placed_labels(points):
    """The chart's own geometry, read from the chart, so the check moves when it does."""
    width, height = site._CHART_BOX
    left, right, top, bottom = site._CHART_MARGINS
    pw, ph = width - left - right, height - top - bottom
    xmax = math.ceil(max(12.0, max(p["minutes"] for p in points) * 1.2) / 3) * 3

    def sx(minutes):
        return left + minutes / xmax * pw

    def sy(rate):
        return top + (1 - rate) * ph

    site._mark_anchors(points)
    sides = site._label_sides(points, sx, sy, left, width - right, top, height - bottom)
    for p in points:
        # Unlabeled dots still veto label space, so they ride along with lo/hi None.
        if id(p) in sides:
            _, _, lo, hi, dy = sides[id(p)]
        else:
            lo = hi = dy = None
        yield p, lo, hi, sy(p["rate"]) + (dy or 0), sx(p["minutes"]), sy(p["rate"])


def test_one_label_per_model_line():
    """Labeling every dot buried the top tenth of the chart the moment the board grew
    past a handful of rows; the label names the line, the dot letters carry effort."""
    paths = sorted(
        str(p) for p in site.SUBMISSIONS.iterdir() if (p / "results.jsonl").is_file()
    )
    combos = site._combos(report.summarize(report.rows_from(paths)))
    points = []
    for (harness, model, effort, _), tasks in combos:
        firsts, total, minutes, capped, dollars = site._stats(tasks)
        points.append({
            "harness": harness, "model": model, "effort": effort,
            "rate": firsts / total if total else 0.0, "minutes": minutes,
            "capped": capped, "dollars": dollars, "firsts": firsts, "total": total,
        })
    site._mark_anchors(points)
    labeled = [(p["harness"], p["model"]) for p in points if p["anchor"]]
    assert sorted(labeled) == sorted({(p["harness"], p["model"]) for p in points})


def test_no_two_labels_land_on_top_of_each_other():
    """Every good model bunches into the top tenth of the chart, so labels there have
    to move out of each other's way. An unreadable pile is the failure this catches;
    it appeared the first time seven combos scored above 90 percent."""
    paths = sorted(
        str(p) for p in site.SUBMISSIONS.iterdir() if (p / "results.jsonl").is_file()
    )
    combos = site._combos(report.summarize(report.rows_from(paths)))
    points = []
    for (harness, model, effort, _), tasks in combos:
        firsts, total, minutes, capped, dollars = site._stats(tasks)
        points.append({
            "harness": harness, "model": model, "effort": effort,
            "rate": firsts / total if total else 0.0, "minutes": minutes,
            "capped": capped, "dollars": dollars, "firsts": firsts, "total": total,
        })
    labels = list(_placed_labels(points))

    # What a reader sees is the backing rect, not the glyphs: a full label row tall
    # and padded past the text on both sides. Measure that, or a label can clear its
    # neighbour by a margin the renderer then spends on padding.
    pad = site._LABEL_PAD
    placed = [row for row in labels if row[1] is not None]
    overlaps = [
        (a["model"], a["effort"], b["model"], b["effort"])
        for i, (a, alo, ahi, ay, _, _) in enumerate(placed)
        for b, blo, bhi, by, _, _ in placed[i + 1:]
        if abs(ay - by) < site._LABEL_ROW and alo - pad < bhi + pad and blo - pad < ahi + pad
    ]
    assert not overlaps, f"labels overlapping on the chart: {overlaps}"

    buried = [
        (a["model"], a["effort"], b["model"], b["effort"])
        for a, alo, ahi, ay, _, _ in placed
        for b, _, _, _, bx, by in labels
        if a is not b and abs(by - ay) < site._LABEL_ROW and alo - 7 < bx < ahi + 7
    ]
    assert not buried, f"labels sitting on someone else's dot: {buried}"
