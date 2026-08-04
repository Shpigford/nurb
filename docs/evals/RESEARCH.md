# nurb LLM Eval Suite Research

## Overview

A repeatable benchmark measuring how well different LLMs (Claude family, GPT/Codex, Gemini, Grok, local models) design 3D-printable parts with nurb, so the project can publish a leaderboard and recommend models to hobbyist users. Research was conducted 2026-08-01 via parallel subagents (codebase, CAD-benchmark prior art, harness tooling); load-bearing harness claims were adversarially verified against live Inspect AI docs.

## Problem Statement

There are dozens of viable models times thinking/effort levels, and no objective way to tell a user which to run nurb with. Scoring must be mechanical (no human judging), cheap enough that community members can contribute rows, and resistant to gaming (memorized parts, card-muted lint rules).

## Recommended Approach

Three layers:

1. **Tasks**: original, tightly specified part-design tasks. Each is a directory: prompt, fixture project (`parts/`, `measurements.toml`, `printer.toml`), seeded parametric dimensions (assertions are parametric, defeating memorization), and an assertion module in the `tests/test_notch_fit.py` style (literal ground truth, feature extraction by coordinate plane, a misfit *list*). Every scored dimension appears in the prompt; nothing unstated is scored.
2. **Scorer**: gate-then-grade. Gate: builds within timeout, exactly 1 solid. Candidate code runs in an isolated worker that exports BREP geometry; the trusted scorer imports those BREP files and owns `checks.run`, task assertions, and the JSON verdict. This prevents a candidate from forging stdout or mutating the check registry. Grade: `checks.run` under a **frozen Context owned by the task** (never `from_card` — a model writing its own card can mute rules via `[accepted]`/`min_wall`), dimensional assertions, and a parameter-honesty probe (override a parameter, assert geometry tracks — catches hardcoded dimensions). Graded partial credit (roughly lint 0.3 / dims 0.5 / flex 0.2) reduces variance versus pass/fail, so 3 trials suffice.
3. **Runner**: drive the agent CLIs people actually use (`claude -p`, `codex exec`, later gemini/opencode/amp), authenticated by each contributor's own subscription rather than API keys. Decided 2026-08-01, superseding the original Inspect AI recommendation: nurb's users run harness subscriptions, so this measures the real product (model + harness + shipped skill) and makes a community row effectively free. Verified locally: `claude` 2.1.220 has streaming JSON transcripts and native `--effort` (low/medium/high/xhigh/max); `codex` 0.139.0 has `exec -m <model> -c model_reasoning_effort=<level> --json -s workspace-write`. Harnesses run without contributor customizations: Claude safe mode receives the shipped skill explicitly, while Codex gets an ephemeral home containing only subscription auth. Model and effort are required row identity. No `--max-turns` exists in current Claude, so the per-trial wall-clock timeout is the cap. The runner loops trials itself (no Inspect dependency); results are JSONL rows plus full JSON event transcripts. Tradeoffs accepted: scores conflate model with harness version (record both, pin in the row), and trials run on the contributor's machine like any normal agent session rather than in a managed sandbox. The Inspect AI findings stay below for a possible future API-matrix companion table.

### Cost model (the binding constraint)

Core set: 10 tasks × 3 trials = 30 runs per leaderboard row (a row is a model+effort combo). Maintainer runs only ~8 reference rows (~240 runs per refresh); the community submits other rows as PRs of self-contained Inspect `.eval` logs. Two tiers: self-reported (logs present, CI-validated format) and validated (maintainer re-ran a seeded random 2-3 tasks, scores matched). Hard turn cap (~20) and per-task token budget bound worst-case spend; tokens-spent and cost are leaderboard columns.

## Key Codebase Facts

- Headless build API: `builder.load/build` (`src/nurb/builder.py:43,104`) — per-call module isolation, returns `(shape, params, ms)`; `checks.run(shape, ctx, only)` (`checks.py:67`) returns sorted `Finding` dataclasses (FAIL/WARN, value, where); `Context` fields are all thresholds (`checks.py:33-53`); `checks.printer(root, name)` (`checks.py:600`).
- No build timeout exists; `builder.load` executes candidate code in-process → eval grading must run in a subprocess.
- Assertion patterns to lift: `tests/test_notch_fit.py:60-87` (floors/misfits), `tests/test_examples.py` (bbox, face-count, parametric formula sweeps), `cli._flex` (`cli.py:287`) with `KERNEL = ("Failed creating a chamfer", "Failed creating a fillet", "BRep_API")`.
- The shipped skill (`src/nurb/skill.md`, ~9.6KB) + doctrine (`nurb rules`, ~26KB) is the effective system prompt; several directives assume an interactive user and live viewer, so the eval needs a headless preamble.
- No eval infrastructure exists anywhere in the repo. Note: CLAUDE.md mentions `nurb verify --strict-ish`, but no such flag exists in code (only `nurb check --strict`, `cli.py:673`).

## Prior Art (what the design steals)

- **CADTests** (arxiv 2605.07807): executable assertions against the B-rep correlate with expert judgment far better than Chamfer/IoU/VLM judges; underspecified prompts make reference meshes wrong. Validates the assertion-based approach.
- **CADGenBench** (HF): validity as a gate that zeroes everything; validated-vs-self-reported leaderboard tiers.
- **MUSE** (arxiv 2605.28579): report the failure cascade (built / valid / lint-clean / dims-correct) as separate columns — that's where models diverge.
- **CadEval/cadqueryeval**: n=1 sampling is the known weakness; distance metrics miss small chamfers/fillets — include chamfer-bearing tasks deliberately.
- **Contamination**: DeepCAD/Thingiverse-derived corpora are memorized; original measured parts + seeded parametric dims defeat this.
- **Error Bars paper** (arxiv 2411.00640): paired per-task comparisons, mean ± 95% CI, don't force temperature 0 on reasoning models.
- Nobody benchmarks build123d or printability-as-a-metric. Open field.

## Corpus Design Principle (decided 2026-08-02, after phase 3)

The benchmark measures two abilities, and they need different task classes. Deterministic does not mean literal: physics and function are deterministic judges of a better solution, so creative latitude can be scored mechanically as long as the task states problems instead of parts.

- **Spec tasks** (cable_clip is one; roughly 3 of 10): every dimension stated, zero interpretation. They measure execution fidelity, the floor. Assertions state functional truths of the geometry, never the literal construction: phase 3 proved the difference when the flagship chamfered outside edges per the shipped doctrine (the objectively better printed part) and top-face-span assertions scored it below a literal small model. "Nothing unstated is scored" cuts both ways.
- **Function tasks** (the majority): specify the problem, the measured interfaces, and the printer, not the geometry. "This 8mm bundle holds against a wall, you have an M4 screw, it prints on a P1S as it sits." Score functional gates that are mechanical on the B-rep (a void that retains an 8mm cylinder laterally, an M4 clearance hole with head room, support-free, one solid, zero findings) plus quality gradients with real slopes (material volume, overhang area, minimum wall, print-time proxy). A cleverer design legitimately wins the gradients without a human deciding it was clever. This class is where interpretation-strong models get to outmaneuver literal ones.
- **Judgment tasks** (the planned refusal-to-guess / measured() task): judgment, still mechanically checkable.
- **Taste stays out of the core score.** Aesthetic ranking does not mechanize, and CADTests found VLM/LLM judges correlate poorly with experts on exactly this. If wanted later, it is a separate arena-style community-vote track, clearly labeled as a different measurement, never a column in the leaderboard score.

## Risks and Challenges

- OCCT builds can hang → subprocess + timeout is mandatory, not optional.
- Score drift when nurb rules change (e.g. the `floating` rule landed one commit back) → pin nurb version per leaderboard generation; sentinel subset for regression checks.
- Small task count → wide confidence intervals; publish them honestly.
- Community log fabrication → logs are self-contained trajectories + seeded spot-check re-runs.

## Open Questions

- Which 9 tasks follow the first one — the class mix is decided (see Corpus Design Principle); the concrete parts are not. Candidates: chamfer-heavy spec task, overhang trap, an assembly, plus function tasks around real measured objects.
- Whether the leaderboard site lives in `site/` or a separate repo — Phase 3+ concern.

## References

Inspect AI: https://inspect.aisi.org.uk/ (reasoning.html, metrics.html, sandboxing.html) · Harbor/terminal-bench: https://www.tbench.ai/news/announcement-2-0 · CADTests: https://arxiv.org/html/2605.07807 · CADGenBench: https://github.com/huggingface/cadgenbench · MUSE: https://arxiv.org/abs/2605.28579 · cadqueryeval: https://github.com/danwahl/cadqueryeval · Error bars: https://arxiv.org/pdf/2411.00640 · aider leaderboards: https://aider.chat/docs/leaderboards/
