# nurb LLM Eval Suite Implementation Plan

## Overview

Vertical slice first: one task, a provably fair scorer, then the Inspect harness, then a real 2-3 model comparison. The corpus (10 tasks) only gets written after the slice proves the scoring is fair. Everything lives in `evals/`, its own uv project with a path dependency on nurb — provider SDKs and inspect-ai never become nurb dependencies.

## Prerequisites

- nurb repo at current HEAD (branch `llm-model-eval-suite`); `uv` installed.
- Phase 2 needs Docker; Phase 3 needs at least an Anthropic API key.

## Phase Summary

1. Scorer + first task, proven fair locally (no API keys, no Docker).
2. Inspect AI harness: docker sandbox, react agent, scorer wrapper, headless preamble.
3. First real model comparison, report script, community submission docs.

---

## Phase 1: Scorer + first task, proven fair locally

### Objective

`evals/` project containing the gate-then-grade scorer, the `cable_clip` task (seeded dims, fixture project, assertion module), reference solutions (one good, several deliberately flawed), and a pytest suite proving each flaw is caught in the intended stage.

### Rationale

The whole benchmark's credibility rests on the scorer being fair and ungameable. Reference solutions are the negative controls ("the assertion has to be able to fail, or it is decoration"). This phase needs zero external services, so it's cheap to iterate.

### Tasks

- [ ] `evals/pyproject.toml`: uv project `nurb-evals`, deps `nurb` (editable path dep on `..`) + `pytest`.
- [ ] `evals/src/nurb_evals/scoring.py`: `grade(part_path, task, dims)` → `Grade` dataclass (gate fields, findings, misfits, flex problems, stage sub-scores, total). Weights: lint 0.3, dims 0.5, flex 0.2; gate failure → 0.0. Lint: each FAIL −0.5, WARN −0.25, floor 0. Dims: 1 − misfits/checks. Flex: 1 − problems/probes.
- [ ] `evals/src/nurb_evals/{candidate,grade}.py` (`python -m nurb_evals.grade <part> <task-dir> <seed>`): candidate code builds in a process-group-isolated worker and exports BREP files; the trusted scorer owns checks and the JSON verdict behind an outer hard timeout (default 60s). Timeout, crash, forged stdout, or missing BREP → score 0 JSON.
- [ ] `evals/tasks/cable_clip/task.py`: `instance(seed)` → seeded `bundle_diameter` (6.0-12.0, 0.5 steps), instruction text with every scored dimension stated, `measurements_toml` content; `misfits(shape, dims)` → (problems, checks_count) asserting bbox, channel-floor face (position + span, floors pattern), through-hole circular edges (radius, both Z planes), volume band; `CTX` (frozen `checks.Context()`, never from_card); `FLEX` probes (override `bundle_diameter` +1.0, assert channel span tracks; KERNEL-worded refusals are problems, part-worded ValueErrors allowed).
- [ ] `evals/tasks/cable_clip/fixture/`: `printer.toml` (profile `bambu_p1s`), `parts/` seeded empty; `materialize(seed, dest)` in task.py copies fixture + writes seeded `measurements.toml` (value + `how` provenance).
- [ ] `evals/tests/solutions/`: `good.py` (correct clip), `wrong_dim.py` (channel 1mm narrow), `no_channel.py` (solid block, right bbox), `hardcoded.py` (correct at defaults, ignores its parameter), `two_solids.py`, `raises.py`, `hangs.py` (infinite loop).
- [ ] `evals/tests/test_scoring.py`: fairness suite — good ≥ 0.99; each flaw penalized in its intended stage and totals ordered below good; `hangs.py` returns 0.0 within timeout + margin via the subprocess runner; JSON output is parseable and carries stage sub-scores.

### Success Criteria

- `cd evals && uv run pytest -q` passes.
- `uv run python -m nurb_evals.grade tests/solutions/good.py tasks/cable_clip 42` prints JSON with `score >= 0.99`.
- Same command on `wrong_dim.py` shows `dims < 1.0` and lower total; on `no_channel.py` shows dim failures despite correct bbox; on `hardcoded.py` shows `flex < 1.0`; on `two_solids.py` and `raises.py` shows `score == 0.0`; on `hangs.py` returns within ~70s with `score == 0.0`.
- Changing the seed changes `bundle_diameter` in both instruction and assertions consistently (one test proves it).
- Scorer never reads the candidate's card or fixture `printer.toml` (grep + test: muting via card `[accepted]` does not change the score).

### Files Likely Affected

All new, under `evals/`. No changes to `src/nurb/`.

---

## Phase 2: Subscription-CLI runner (replaces the original Inspect AI plan, 2026-08-01)

### Objective

A trial runner that drives installed agent CLIs (`claude`, `codex`, extensible to others) on the contributor's own subscription: materialize the fixture, hand the CLI the headless instruction, grade the part it writes, and append a JSONL result row per trial.

### Rationale

User decision: rows must be runnable on harness subscriptions, not API keys — that is how nurb's users actually run, it benchmarks the real product (model + harness + shipped skill), and it makes community rows effectively free. The runner loops trials itself, so the Inspect dependency disappears entirely.

### Tasks

- [ ] `src/nurb_evals/harness.py`: adapter registry. `claude`: safe mode plus streaming JSON and the shipped skill passed explicitly, with usage parsed from the final result event. `codex`: JSON events, workspace sandbox, ignored user config/rules, and an ephemeral `CODEX_HOME` containing only subscription auth.
- [ ] `src/nurb_evals/run.py` (`python -m nurb_evals.run --harness claude --model M --effort E --task tasks/cable_clip --seed N --trials 3 --timeout 900 --out DIR`): require model and effort; per trial, materialize the fixture into `DIR/trial_<n>/project`, run the CLI there with the evals venv's bin prepended to PATH (so `nurb` resolves), hard wall-clock timeout as the turn cap, grade `parts/cable_clip.py` via the Phase 1 subprocess grader, append a row (harness, harness version, benchmark versions and content revision, model, effort, seed, trial, score, stages, usage, durations, error) to `DIR/results.jsonl`, and keep the full JSON event transcript.
- [ ] Headless preamble prepended to the instruction: benchmarked non-interactively, no human, never `nurb dev`; `nurb build`/`check`/`inspect` are the only feedback.
- [ ] `materialize` also seeds `AGENTS.md` from the shipped `nurb` skill (what real projects get from `nurb new`).
- [ ] A stub harness (registered only by tests) that copies a known solution into place, so the whole loop is testable without a real CLI or subscription.
- [ ] One real smoke trial with `claude` on a small model at low effort.

### Success Criteria

- `uv run pytest -q` still passes, including runner-loop tests via the stub harness (score 1.0 row for the good solution, gate-failure row when no part file is written).
- One real `claude` smoke trial completes end to end on the subscription: results.jsonl row with score, stages, model, effort, usage, and a kept transcript.
- The command line above works as documented; effort and model are recorded in the row.

### Files Likely Affected

`evals/src/nurb_evals/{harness,run}.py`, `evals/tasks/cable_clip/task.py` (materialize), `evals/tests/`.

---

## Phase 3: First real comparison, report, community docs

### Objective

Run 2-3 real model+effort combos (3 trials each) on cable_clip via the subscription CLIs; a report script that turns results.jsonl into the leaderboard row format (score mean, cascade columns built/lint/dims/flex, pass@1, pass@3, tokens, wall time); `evals/README.md` documenting how a community member runs and submits a row.

### Tasks

- [ ] Run the matrix (suggest: claude flagship at high effort, claude small model, codex if authenticated).
- [ ] `evals/src/nurb_evals/report.py`: read results.jsonl files → markdown table with the agreed columns.
- [ ] `evals/README.md`: what this is, subscription-based cost expectations, how to run a row, how to PR results + transcripts, self-reported vs validated tiers, seeded spot-check policy.
- [ ] Fairness review: read the real transcripts; note any scoring unfairness (ambiguous instruction, assertion too strict/loose) as lessons before corpus work.

### Success Criteria

- A committed markdown report with ≥2 rows, each showing score, cascade, pass@1/pass@3, usage, wall time.
- README instructions reproduce a row end-to-end from a clean checkout (verified by following them literally).

---

## Phase 4: First function task (`bundle_holder`), multi-task runner

### Objective

The first task of the corpus's majority class: a function task that states the problem, the measured interfaces, and the printer, never the geometry. Plus the small runner generalization a second task forces (no hardcoded part path), fairness suite, adversarial verification, and a real trial matrix proving the task separates models where cable_clip could not.

### Rationale

Phase 3's recorded lesson: cable_clip does not separate strong models (haiku at low effort scores 1.0). The corpus design principle (RESEARCH.md, decided 2026-08-02) says function tasks are the majority class and the one where interpretation-strong models get to outmaneuver literal ones, so it is the class to prove out first. One task done exhaustively fair beats three done shallowly: every task so far has needed an adversarial iteration loop to become trustworthy.

### Task design (decided here, not re-litigated per file)

`bundle_holder`: a wall-mounted holder for a measured cable bundle, one M4 pan-head screw, prints support-free as it sits on a P1S. The instruction states the mechanical checks and nothing about shape:

- Orientation contract: prints flat as it sits (Z up), mounts with the flat back face at min-X against the wall, down stays -Z, bundle runs along Y.
- Retention gate: some position exists where a bundle-diameter cylinder running the full part length fits in free space and cannot move 1.0mm straight down or 1.0mm straight away from the wall without hitting the part (the wall blocks the fourth direction). Checked by seeded grid search over axis positions with is_inside sampling on the cylinder surface, coarse-then-refined.
- Mount gate: 4.4mm through-hole with axis along X through the back plate (paired circular rims, clear bore, plate at least 2.4mm), material seating the head, and an 8.4mm head-and-driver clearance cylinder open from the seat out of the part in +X.
- Material gradient: full dims credit at or below a stated volume, stepped credit at two stated higher thresholds (a stepped slope keeps the misfits list and flex machinery unchanged; continuous slopes can come later if steps prove too coarse). Thresholds derive from an analytic reference volume and are printed in the instruction, so nothing unstated is scored.
- Lint carries print-physics: support-free, min wall, stability all come from `checks.run` under the task's frozen Context.
- Flex probes bundle +1.0 and +2.0 as in cable_clip.

A closed tunnel is legitimate here (bundles thread along Y); design freedom includes using the wall itself as one side of the channel.

### Tasks

- [ ] `evals/tasks/bundle_holder/{task.py,fixture/}`: instance/misfits/flex_probes/materialize per the design above.
- [ ] `run.py`: derive the part path from the task directory name; drop the `PART_FILE` constant.
- [ ] Solutions move to `tests/solutions/cable_clip/` and `tests/solutions/bundle_holder/`; new references: good, shelf-without-lip (not retained), missing/blind hole, blocked head room, hardcoded parameter, bloated block (gates pass, volume ladder penalizes).
- [ ] Fairness tests: each flaw caught in its intended stage, totals ordered as a user would rank, seed drives instruction and assertions together, grading wall time bounded.
- [ ] Adversarial verification: a fresh-context agent told to cheat the scorer; every found cheat becomes a fixed negative control.
- [ ] Real trials on the subscription CLIs (haiku/low smoke first, then fable/high and codex if available); regenerate REPORT.md covering both tasks.
- [ ] CLAUDE.md: pointer to `evals/`, and fix the stale `--strict-ish` mention (verified against cli.py first).

### Success Criteria

- `cd evals && uv run pytest -q` passes, including the bundle_holder fairness suite.
- `uv run python -m nurb_evals.grade tests/solutions/bundle_holder/good.py tasks/bundle_holder <seed>` prints JSON with `score == 1.0`; each flawed reference scores below good with the flaw named in its intended stage.
- `python -m nurb_evals.run --task tasks/bundle_holder ...` grades the part at `parts/bundle_holder.py`; no cable_clip path remains hardcoded in run.py; a stub-harness runner test exercises a non-cable_clip task.
- Grading one bundle_holder part (default + both flex probes) completes in under 30s.
- At least one real subscription trial on bundle_holder completes end to end: plausible row, kept transcript, zero `nurb dev` attempts.
- Report output renders cable_clip and bundle_holder tables from one invocation.
- The adversarial pass ran; its findings (or the absence of any) are recorded in PROGRESS.md with the cheat geometries as negative controls.

### Files Likely Affected

`evals/tasks/bundle_holder/` (new), `evals/src/nurb_evals/run.py`, `evals/tests/` (solutions reorganized, new fairness tests), `evals/REPORT.md`, `CLAUDE.md`.

---

## Phase 5: First judgment task (`leg_cup`), measurement-flex probes

### Objective

The first task of the corpus's third class: a judgment task that measures measurement discipline — deriving geometry from `measured()` values and handling a dimension nobody can measure right now the way nurb's doctrine says to (record the guess as `provisional = true` with honest provenance), instead of baking a plausible number into the part file. Plus the scorer generalization it forces: flex probes that rebuild the candidate against a rewritten `measurements.toml`, and a task-level audit hook for paperwork checks that are not shape checks.

### Rationale

Spec (cable_clip) and function (bundle_holder) classes are proven; judgment is the last class in the Corpus Design Principle and RESEARCH.md names refusal-to-guess as its planned first task. The mechanism is fair by construction: the escape hatch is taught in-context three ways (the doctrine via `nurb rules`, the shipped skill's pointer to it, and `measured()`'s own error message), and everything scored is stated in the instruction. Same rule as phase 4: one task done exhaustively fair, adversarial pass included.

### Task design (decided here)

`leg_cup`: a slip-over cup for a wobbly workbench leg. The leg cross-section is measured and on file (`leg_width`, `leg_depth`, both seeded); how much lift the leg needs was never measured and there is nobody to ask tonight — the instruction states a plausible band (2.0-5.0 mm) and tells the model to handle it the way the doctrine handles exactly this, under the name `lift`. Geometry is fully stated (pocket = leg + 0.4 clearance, walls 2.0, pocket depth 8.0, floor thickness = lift, prints as it sits, volume within 10% of what the stated features imply), so scoring stays exact; the judgment is the measurement handling.

Scoring mechanics:

- **Measurement-flex probes**: probe A rewrites `measurements.toml` with grown leg dims (lift set to a seeded in-band value, bounding-box Z checked against the band only, so an in-band inline guess passes A); probe B rewrites `lift` alone and checks height exactly (catching the inline guess). The rewritten file contains exactly the three stated names, and the instruction says so.
- **Audit hook**: `task.audit(part_path, inst)` checks the trial's `measurements.toml` records `lift` with `provisional = true` and a non-empty `how` (weight 3; merged into the dims denominator). Honesty of the text cannot be scored; its presence and the provisional marking can.
- **Continuous checks over point grids** (phase 4 lesson): pocket clearance is a virtual-leg boolean (a pocket-sized box from floor to above the rim must intersect nothing), the floor is a boolean requiring the full pocket-footprint slab below the floor face, walls are probed near the top at heights and offsets an edge break cannot reach.
- The `nurb check` provisional reminder is expected and stated as not counted; lint stays `checks.run` on the shape under the frozen Context.
- Designed score order, recorded deliberately: good > out_of_band (honest guess outside the stated band — self-flagging, fixed by one TOML edit) > fake_measured (right part, guess recorded as if measured) > guessed_inline (right part, lift baked into code) > hardcoded_all (ignores the file entirely) > wrong_pocket (broken geometry) > missing_lift (part reads `lift` that was never recorded: gate 0). In a judgment task, honest recording outranks guess accuracy; silent guessing ranks below both; broken geometry stays at the bottom per the phase 1 precedent.

### Tasks

- [ ] `scoring.py`: probe spec becomes `{"params": {...}, "measurements": str|None, "label": str}`; existing tasks' probes updated to the new shape. Optional `task.audit` hook merged into the dims stage.
- [ ] `candidate.py`: a probe carrying measurements text builds the part in a staged temp project (`parts/` + the rewritten `measurements.toml`), so `measured()` resolves against the probe's file.
- [ ] `evals/tasks/leg_cup/{task.py,fixture/}`: instance/context/misfits/audit/flex_probes/materialize per the design above.
- [ ] `tests/solutions/leg_cup/`: the seven references above; the lift-entry each solution would have written lives in the test's snippet map, since leg values are seeded.
- [ ] `evals/tests/test_leg_cup.py`: materialize-then-grade helper, fairness ordering, seed coherence, probe mechanics, audit unit checks.
- [ ] Adversarial verification: a fresh-context agent told to cheat; every found cheat becomes a fixed negative control.
- [ ] `evals/README.md`: judgment class documented; note that leg_cup grades in-project.
- [ ] Real subscription trials: deferred pending Josh's go-ahead (usage-limit policy), alongside the still-pending fable bundle_holder re-run.

### Success Criteria

- `cd evals && uv run pytest -q` passes, including the leg_cup fairness suite; root `uv run pytest -q -n auto` unaffected.
- Grading the good reference in a materialized project at a fixed seed scores 1.0; every flawed reference lands in the designed order above with the flaw named in its intended stage.
- Probe A passes and probe B fails for an in-band inline guess; both fail for hardcoded leg dims (proved by the reference grades).
- A part that never records `lift` but reads it fails the gate with `MeasurementError` in the error text.
- cable_clip and bundle_holder reference grades are byte-identical to their phase 4 values after the probe-spec change (no committed row shifts).
- Grading one leg_cup part completes in under 30s.
- The adversarial pass ran; findings recorded in PROGRESS.md with cheat geometries as negative controls.

### Files Likely Affected

`evals/tasks/leg_cup/` (new), `evals/src/nurb_evals/{scoring,candidate}.py`, `evals/tasks/{cable_clip,bundle_holder}/task.py` (probe shape), `evals/tests/` (new suite + solutions), `evals/README.md`.

---

## Phase 6: Print-physics function task (`shelf_bracket`)

### Objective

The corpus's fourth task and second function task: one where print physics is the binding constraint rather than a lint afterthought. The obvious shape for the stated problem carries an unprintable overhang, and the score separates models that design around physics (a gusseted or chamfered transition, or an orientation chosen so the part prints as it sits) from models that emit the textbook shape and eat the FAIL.

### Rationale

Phase 5 closed the machinery: three classes proven, scorer contract complete (weighted misfits, parameter and measurement probes, audit hook), so this phase is pure content. Print physics is the pick because it is nurb's actual differentiator (no other CAD benchmark scores printability at all, per RESEARCH.md) and nothing in the corpus yet forces a model to reckon with it: cable_clip and leg_cup print trivially, and bundle_holder's support-free constraint has not been the thing any real trial failed on. One task, exhaustively fair, adversarial round included; the phase 4 and 5 records say every task needs one.

### Task design (sketch; the executing session pins the checks)

`shelf_bracket`: a wall bracket holding a small shelf ledge of stated depth clear of the wall, mounted with two screws, on the P1S. Stated: the mounting interface (screw spacing and diameters, back-plate contact), the ledge's working surface (depth, width, height above the lower screw, flatness, load-bearing span as a continuous boolean), support-free printing as it sits, and the material gradient. Not stated: the shape between wall and ledge, or how the part sits on the bed.

Design intents to preserve while pinning checks:

- The naive shape (flat back plate, horizontal ledge at 90 degrees, printed upright) must genuinely fail lint via the frozen Context's overhang rule, and at least two honest escapes must exist: geometry (a 45-degree gusset or chamfered transition under the ledge) and orientation (modelled so it sits print-friendly, e.g. on its side, with the mounting contract expressed in the part's own frame). Both escapes score full marks; the task must not privilege one.
- The mounting and ledge gates are stated relative to the part's own frame (back face, ledge normal), never the bed, so orientation freedom does not rotate the functional checks out from under the part. bundle_holder's orientation contract is the pattern to adapt, loosened to leave the bed pose free.
- Functional checks stay continuous (booleans against ledge-sized and screw-sized volumes); phase 5's lesson about mapping the union of the probes applies from the start, not after the adversary reports.
- Two chamfered edges need room between them (CLAUDE.md): the gusset-plus-polish combination is where OCCT's chamfer collisions live, so the reference set needs a polished positive control from day one.

### Tasks

- [ ] `evals/tasks/shelf_bracket/{task.py,fixture/}`: instance (seeded ledge depth/width and screw spacing), instruction, misfits, flex probes; no scorer changes expected.
- [ ] Reference set: good (gusseted), good (reoriented), polished positive control, the naive 90-degree overhang (lint FAIL, dims clean), plus the usual gate/dims/flex negatives.
- [ ] Fairness suite in the established shape; designed score order recorded before grading.
- [ ] Adversarial round by a fresh-context agent; map the probe-coverage union first (phase 5 lesson); every cheat becomes a control.
- [ ] Fresh-context verification against these criteria.
- [ ] Real trials only with Josh's go-ahead.

### Success Criteria

- `cd evals && uv run pytest -q` passes with the shelf_bracket suite; root suite unaffected.
- The naive-overhang reference loses lint points under the frozen Context while passing dims, and both honest escapes (gusset, reorientation) score 1.0.
- Every flawed reference lands in a recorded designed order with the flaw named in its intended stage; seed drives instruction and assertions together.
- Existing task reference grades unchanged (no scorer edits, or proven score-neutral if any).
- Grading one part completes in under 30s; the adversarial round ran and its findings are recorded with cheat geometries as controls.

---

## Post-Implementation

- [ ] Corpus: the remaining core tasks after phase 6 (chamfer-heavy spec task, an assembly task, more function tasks toward the ten of the research's core set).
- [ ] Consider publishing at three or four tasks rather than waiting for ten: three classes with honest confidence intervals is a defensible benchmark, community rows cost contributors nothing, and later tasks benefit from public scrutiny. Josh's call.
- [ ] CI format-validation for community PRs; leaderboard rendering (site/ vs separate repo, open since RESEARCH.md).

## Notes

Phase granularity: three phases because each has a distinct external dependency boundary (none / Docker / API keys+money), and each ends independently verifiable.
