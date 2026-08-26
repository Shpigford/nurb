---
name: leaderboard
description: Publish the nurb model leaderboard from merged benchmark submissions. Sanity-checks every run landed since the last regeneration, writes or refreshes the editorial verdicts, regenerates the benchmarks repo's REPORT.md and this repo's site/benchmarks.html, and opens the publish PRs. Use when the user says "update the leaderboard", "publish the benchmarks", "regenerate the benchmark page", or after merging submission PRs.
---

# nurb leaderboard

Two generated surfaces, one editorial layer, two repos. The benchmark (tasks, scorer, submissions, `REPORT.md`) lives in [Shpigford/nurb-benchmarks](https://github.com/Shpigford/nurb-benchmarks); the public page (`site/benchmarks.html`, behind nurb.dev/benchmarks) lives here. Both surfaces regenerate mechanically from that repo's `submissions/`; the verdict sentences and subscription labels live in its `src/nurb_evals/site.py` and are written by a person. Submission PRs are pure additions and merge freely; nothing reaches the public page until this skill runs. That gap is deliberate: it is where the sanity check and the verdicts happen, so publishing is an editorial act, not a side effect of merging.

## Step 0: Get the benchmarks checkout

Clone or update `Shpigford/nurb-benchmarks` somewhere outside this repo (for example `../nurb-benchmarks`, or a temp directory), on its main. Everything below that touches submissions, verdicts, or `REPORT.md` happens in that checkout; only the final `site/benchmarks.html` lands here.

## Step 1: Find what is new

The runs added since the page was last regenerated. In this repo, `git log -1 --format=%ci -- site/benchmarks.html` dates the last publish; in the benchmarks checkout, list the submission directories whose merge commits landed after it (`git log --since=<date> --diff-filter=A --name-only -- submissions/ | grep results.jsonl`).

Each directory under `submissions/` is one run: `<harness>-<model>-<effort>-<hex>/` holding `results.jsonl` plus per-trial gzipped transcripts and part sources. If nothing is new, say so and stop.

## Step 2: Sanity-check every new run

Work from the benchmarks checkout (its own uv project; `uv sync --locked` first if the venv is stale). For each new run directory:

- **Rows parse and carry full identity**: every line of `results.jsonl` has harness, harness_version, model, effort, seed, nurb_version, benchmark_version, a 12-char benchmark_revision, and timeout_s. A benchmark_revision that matches no revision the benchmark ever shipped is disqualifying (revisions from before the August 2026 repo split shipped from Shpigford/nurb's history).
- **Artifacts are complete and sanitized**: a `transcript.txt.gz` and the part source for every row; no `/Users/`, `/home/`, or usernames anywhere once decompressed (the suite's sanitization test enforces this too).
- **The parts are authored, not planted**: hash the submitted part files against `tests/solutions/` and against parts from other submissions. An exact match with a reference solution is disqualifying; matches across unrelated submissions are worth reading.
- **Spot-check by re-grading**: for at least one row per new run (and every row that looks too good), rebuild the trial project (`task.materialize`, drop the part in, restore the submitted `measurements.toml` for leg_cup) and run the grader. The committed score must reproduce exactly; grading is deterministic.
- **Read one transcript** per new contributor (`gzcat <trial>/transcript.txt.gz`): the headless preamble held (no `nurb dev`), the model actually iterated, and the session matches the row's timings.

A run that fails a check is removed with a PR comment saying which check and why, not silently. Suspicion is not proof: when a re-grade mismatches, check the benchmark_revision first; a row graded under an older shipped revision reproduces under that revision's scorer, not today's.

## Step 3: Verdicts

Every (harness, model, effort) combo on the board should have an entry in `VERDICTS` in the benchmarks repo's `src/nurb_evals/site.py`: which subscription it runs on, and one or two sentences a person with a printer can act on. Ground every claim in the rows and transcripts (findings, timings, the honesty tasks); never speculate. A new combo without a verdict renders numbers-only, which is acceptable for a day, not a policy. Capped or censored data is named as such ("hit the session limit"), never averaged into a claim.

## Step 4: Regenerate, look, publish

From the benchmarks checkout:

```bash
uv run python -m nurb_evals.report --write
uv run python -m nurb_evals.site --out <this-repo>/site/benchmarks.html
```

Open `site/benchmarks.html` in a browser and look at it before publishing: label collisions on the chart, a card wrapping badly, an empty state showing when rows exist. Screenshot, not DOM-query. Then two PRs, never straight to main: in nurb-benchmarks, the regenerated `REPORT.md` plus any verdict edits and removed runs; here, the regenerated `site/benchmarks.html`. Each PR body lists which runs were published and which were rejected with reasons. `uv run pytest -q tests/test_report.py tests/test_pricing.py tests/test_contribute.py` in the benchmarks checkout must be green; the full grading suite only guards scorer code, which this skill never touches.

The page deploys with `site/` however the site deploys; this skill's job ends at the merged PRs.
