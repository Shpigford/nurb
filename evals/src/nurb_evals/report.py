"""Turn results.jsonl rows into the leaderboard table.

One table row per task, benchmark revision, harness version, model, and effort: the
full identity a score belongs to. Stage columns are conditional the way MUSE reports its cascade:
`built` is the fraction of trials that passed the gate, and lint/dims/flex are means
over built trials only, so a gate failure does not masquerade as a lint problem. The
total score still averages over every trial, gate failures as zeros.
"""

import argparse
import json
import math
import pathlib
import sys

from . import pricing

# A pass is a near-perfect part: every stated dimension, no lint findings, honest
# parameters. Matches the fairness suite's bar for the reference solution.
PASS = 0.99


def rows_from(paths):
    for raw in paths:
        path = pathlib.Path(raw)
        if path.is_dir():
            path = path / "results.jsonl"
        with open(path, encoding="utf-8") as source:
            for line in source:
                if line.strip():
                    yield json.loads(line)


def built(row):
    # Past the gate, not merely built: a two-solid build carries built=true and a gate
    # error. Any positive score proves the gate; a zero score passed it only when the
    # part built and nothing errored (a graded part's error is always null).
    return row["score"] > 0.0 or (row.get("built", True) and row.get("error") is None)


def pass_at(k, n, c):
    """Unbiased pass@k estimator (Chen et al.) from c passes in n trials."""
    k = min(k, n)
    if n - c < k:
        return 1.0
    return 1.0 - math.comb(n - c, k) / math.comb(n, k)


def _mean(values):
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def _tokens(row):
    usage = row.get("usage") or {}
    if "input_tokens" in usage and "output_tokens" in usage:
        return usage["input_tokens"] + usage["output_tokens"]
    return None


def harness_version(row):
    """The harness version without its release channel.

    The Grok CLI reports "grok 1.0.5 (5115b46bc909)" and "grok 1.0.5 (5115b46bc909)
    [stable]" from the same binary, and it changed which one mid-run. A channel is
    not a version, so splitting a row on it invents a difference the table cannot
    even show: both render as "grok 1.0.5". The raw string stays in results.jsonl.
    """
    version = row.get("harness_version")
    return version.split(" [")[0].strip() if version else version


def summarize(rows):
    prices = pricing.load()
    groups = {}
    for row in rows:
        # The resolved ids are part of the identity: --model accepts floating
        # aliases, and two runs of "opus" months apart can be different models.
        # Rows recorded before the runner captured them carry an empty tuple and
        # pool by label alone, as they always did.
        key = (
            row["task"], row["harness"], harness_version(row),
            row["nurb_version"], row["benchmark_version"], row["benchmark_revision"],
            row["model"], row["effort"],
            tuple((row.get("usage") or {}).get("models") or ()),
        )
        groups.setdefault(key, []).append(row)

    out = []
    for key, trials in groups.items():
        (task, harness, version, nurb_version, benchmark_version, revision,
         model, effort, resolved) = key
        scores = [t["score"] for t in trials]
        ok = [t for t in trials if built(t)]
        passes = sum(s >= PASS for s in scores)
        n = len(trials)
        out.append({
            "task": task,
            "seeds": sorted({t["seed"] for t in trials}),
            "harness": harness,
            "harness_version": version,
            "nurb_version": nurb_version,
            "benchmark_version": benchmark_version,
            "benchmark_revision": revision,
            "model": model,
            "resolved": list(resolved),
            "effort": effort,
            "trials": n,
            "score": _mean(scores),
            "built": len(ok) / n,
            "lint": _mean([t["stages"]["lint"] for t in ok]),
            "dims": _mean([t["stages"]["dims"] for t in ok]),
            "flex": _mean([t["stages"]["flex"] for t in ok]),
            "pass@1": pass_at(1, n, passes),
            "pass@3": pass_at(3, n, passes),
            "tokens": _mean([_tokens(t) for t in trials]),
            "cost": _mean([pricing.trial_cost(t, prices) for t in trials]),
            "wall_s": _mean([t.get("harness_s") for t in trials]),
            # Killed at the wall clock, so the trial's duration is a floor, not a
            # measurement: anything averaging wall_s owes the reader this count.
            "capped": sum("wall-clock cap" in (t.get("error") or "") for t in trials),
            "scores": scores,
        })
    out.sort(key=lambda r: (r["task"], -r["score"]))
    return out


def _cell(value, fmt="{:.2f}"):
    return "-" if value is None else fmt.format(value)


def table(summary):
    lines = []
    for task in sorted({r["task"] for r in summary}):
        rows = [r for r in summary if r["task"] == task]
        seeds = sorted({s for r in rows for s in r["seeds"]})
        lines.append(f"## {task} (seed {', '.join(map(str, seeds))})")
        lines.append("")
        lines.append("| harness | benchmark | model | effort | trials | score | built | lint | dims | flex | pass@1 | pass@3 | tokens | cost | wall | trial scores |")
        lines.append("|---|---|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|")
        for r in rows:
            # "2.1.220 (Claude Code)" and "codex-cli 0.139.0" both yield the number.
            tokens = (r["harness_version"] or "").split()
            version = next((t for t in tokens if any(c.isdigit() for c in t)), "?")
            lines.append("| " + " | ".join((
                f"{r['harness']} {version}",
                f"{r['nurb_version']}/{r['benchmark_version']}@{r['benchmark_revision']}",
                r["model"] or "-",
                r["effort"] or "-",
                str(r["trials"]),
                _cell(r["score"], "{:.3f}"),
                _cell(r["built"]),
                _cell(r["lint"]),
                _cell(r["dims"]),
                _cell(r["flex"]),
                _cell(r["pass@1"]),
                _cell(r["pass@3"]),
                _cell(r["tokens"], "{:,.0f}") if r["tokens"] is not None else "-",
                _cell(r["cost"], "${:.2f}"),
                _cell(r["wall_s"], "{:.0f}s"),
                " / ".join(f"{s:.3f}" for s in r["scores"]),
            )) + " |")
        lines.append("")
        lines.append(f"`benchmark` is nurb/evals@content-revision and separates rows whenever the tool, task, scorer, harness adapter, or locked dependencies change. `score` averages all trials with gate failures as zeros; `built` is the fraction of trials past the gate, and lint/dims/flex average built trials only. A pass is a score of at least {PASS}. Stage columns overlap by design: a part wrong at the stated size is wrong at every probed size too, so it loses dims and flex together. `tokens` is input plus output as the harness reports them, and harnesses count differently (claude's input excludes cache reads, codex counts full per-turn context), so compare tokens within a harness only. `cost` is the API-equivalent dollar cost of a trial at list prices, the mean across trials: subscription runs paid no invoice, so this is what the same tokens would have cost through the API. claude rows carry the CLI's own cache-aware figure; other harnesses derive from their token counts and the dated prices.toml, which folds any cached tokens in at the full input rate and so reads slightly high.")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


EVALS = pathlib.Path(__file__).parents[2]

HEADER = """\
# nurb leaderboard

Generated from the committed submissions by `python -m nurb_evals.report --write`, so it can never disagree with them; the reader-facing version is [nurb.dev/benchmarks](https://nurb.dev/benchmarks.html), built from the same rows. Matching rows pool across submissions, single runs included, and every row's transcripts and parts live under [submissions/](submissions/). See [README.md](README.md) to run one.
"""

EMPTY = """\
No rows yet. Run one on your own subscription:

```
curl -fsSL https://nurb.dev/bench.sh | sh
```
"""


def write(submissions=None, out=None):
    """Regenerate REPORT.md from the committed submissions. The contribute wizard
    calls this so a PR ships with the report its rows produce."""
    submissions = pathlib.Path(submissions or EVALS / "submissions")
    out = pathlib.Path(out or EVALS / "REPORT.md")
    summary = summarize(rows_from(sorted(submissions.glob("*/results.jsonl"))))
    body = table(summary) if summary else EMPTY
    out.write_text(HEADER + "\n" + body, encoding="utf-8")
    return out


def main():
    ap = argparse.ArgumentParser(description="results.jsonl rows to a leaderboard table")
    ap.add_argument("results", nargs="*", help="results.jsonl files or their directories")
    ap.add_argument(
        "--write", action="store_true", help="regenerate REPORT.md from the committed submissions"
    )
    args = ap.parse_args()
    if args.write:
        print(f"wrote {write()}")
        return
    if not args.results:
        ap.error("results paths required unless --write")
    sys.stdout.write(table(summarize(rows_from(args.results))))


if __name__ == "__main__":
    main()
