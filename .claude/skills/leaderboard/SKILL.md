---
name: leaderboard
description: Publish the nurb model leaderboard from merged benchmark submissions. Sanity-checks every run landed since the last regeneration, writes or refreshes the editorial verdicts, regenerates evals/REPORT.md and site/benchmarks.html, and opens the publish PR. Use when the user says "update the leaderboard", "publish the benchmarks", "regenerate the benchmark page", or after merging submission PRs.
---

# nurb leaderboard

Two generated surfaces, one editorial layer. `evals/REPORT.md` (audit tables) and `site/benchmarks.html` (the page behind nurb.dev/benchmarks) both regenerate mechanically from `evals/submissions/`; the verdict sentences and subscription labels live in `evals/src/nurb_evals/site.py` and are written by a person. Submission PRs are pure additions and merge freely; nothing reaches the public page until this skill runs. That gap is deliberate: it is where the sanity check and the verdicts happen, so publishing is an editorial act, not a side effect of merging.

## Step 1: Find what is new

The runs added since the page was last regenerated:

```bash
git log -1 --format=%H -- site/benchmarks.html
git diff --stat <that-commit>..HEAD -- evals/submissions/
```

Each new directory under `evals/submissions/` is one run: `<harness>-<model>-<effort>-<hex>/` holding `results.jsonl` plus per-trial transcripts and part sources. If nothing is new, say so and stop.

## Step 2: Sanity-check every new run

Work from `evals/` (its own uv project; `uv sync --locked` first if the venv is stale). For each new run directory:

- **Rows parse and carry full identity**: every line of `results.jsonl` has harness, harness_version, model, effort, seed, nurb_version, benchmark_version, a 12-char benchmark_revision, and timeout_s. A benchmark_revision that matches no revision this repo ever shipped is disqualifying.
- **Artifacts are complete and sanitized**: a transcript and the part source for every row; no `/Users/`, `/home/`, or usernames anywhere (the suite's sanitization test enforces this too).
- **The parts are authored, not planted**: hash the submitted part files against `evals/tests/solutions/` and against parts from other submissions. An exact match with a reference solution is disqualifying; matches across unrelated submissions are worth reading.
- **Spot-check by re-grading**: for at least one row per new run (and every row that looks too good), rebuild the trial project (`task.materialize`, drop the part in, restore the submitted `measurements.toml` for leg_cup) and run the grader. The committed score must reproduce exactly; grading is deterministic.
- **Read one transcript** per new contributor: the headless preamble held (no `nurb dev`), the model actually iterated, and the session matches the row's timings.

A run that fails a check is removed from the PR with a comment saying which check and why, not silently. Suspicion is not proof: when a re-grade mismatches, check the benchmark_revision first; a row graded under an older shipped revision reproduces under that revision's scorer, not today's.

## Step 3: Verdicts

Every (harness, model, effort) combo on the board should have an entry in `VERDICTS` in `evals/src/nurb_evals/site.py`: which subscription it runs on, and one or two sentences a person with a printer can act on. Ground every claim in the rows and transcripts (findings, timings, the honesty tasks); never speculate. A new combo without a verdict renders numbers-only, which is acceptable for a day, not a policy. Capped or censored data is named as such ("hit the session limit"), never averaged into a claim.

## Step 4: Regenerate, look, publish

```bash
cd evals
uv run python -m nurb_evals.report --write
uv run python -m nurb_evals.site
```

Open `site/benchmarks.html` in a browser and look at it before publishing: label collisions on the chart, a card wrapping badly, an empty state showing when rows exist. Screenshot, not DOM-query. Then a PR (never straight to main): the regenerated pair, any verdict edits, and a body that lists which runs were published and which were rejected with reasons. `uv run pytest -q` from `evals/` must be green.

The page deploys with `site/` however the site deploys; this skill's job ends at the merged PR.
