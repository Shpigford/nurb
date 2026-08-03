# nurb LLM Eval Suite Progress

## Status: Phase 5 Complete and rows current (fable re-run and first leg_cup row landed 2026-08-02; phase 6 scoped, not started)

## Quick Reference
- Research: `docs/evals/RESEARCH.md`
- Implementation: `docs/evals/IMPLEMENTATION.md`

---

## Phase Progress

### Phase 1: Scorer + first task, proven fair locally
**Status:** Complete
**Verified:** Yes — fresh-context verifier passed criteria 1-6 independently (pytest 12/12 at the time, grade CLI JSON, timeout at 10.07s wall, no card/printer.toml reads confirmed by grep and by reading checks.py, seed determinism). Its adversarial pass (criterion 7) found one real cheat: a closed-tunnel clip scored 1.0. Fixed with an open-top misfit check; the cheat geometry is now tests/solutions/roofed.py and scores 0.729 with the roof named. Post-fix: evals suite 13 passed, root suite 295 passed / 1 skipped.

#### Tasks Completed
- evals/ uv project (nurb editable path dep, pytest); `uv sync` clean.
- `src/nurb_evals/scoring.py` (gate-then-grade, weights lint 0.3 / dims 0.5 / flex 0.2), `grade.py` (subprocess + hard timeout, always JSON, exit 0).
- `tasks/cable_clip/`: task.py (seeded instance, instruction with every scored dim stated, frozen Context, misfits with 6 checks, flex probes +1/+2, materialize), fixture (printer.toml bambu_p1s, empty parts/).
- 8 reference solutions (good + 7 flawed) and 12 fairness tests.

#### Evidence
- `uv run pytest -q` → `12 passed in 14.88s` (this session).
- Grader smoke run: good=1.000, hardcoded=0.800, wrong_dim=0.717, no_channel=0.633, overhang=0.333, two_solids/raises=0.000 — every flaw caught in its intended stage, totals ordered as a user would rank the parts.
- Reference part builds in 16ms, 0 findings, volume matches analytic 1254.5mm3.

#### Decisions Made
- Grade result is a plain dict (JSON across the subprocess boundary), not the dataclass the plan sketched.
- Flex probes re-assert full misfits at the grown size, so a part wrong at defaults is also penalized in flex. Deliberate: it makes the functionally-broken clip (wrong_dim 0.717) score below the correct-but-decorative one (hardcoded 0.800), which is the right user-facing order. Stage columns overlap; the cascade report should say so.
- Floor-face assertion distinguishes channel floor from tab top by "interior in X" (not touching bbox extremes), because at bundle=9.6 their spans are both 10.0mm.

#### Blockers
None.

### Phase 2: Subscription-CLI runner (redesigned 2026-08-01: user decided rows run on harness subscriptions, not API keys)
**Status:** Complete
**Verified:** Yes — fresh-context verifier ran the suite (19/19 at the time), inspected the real-trial artifacts, independently re-graded haiku's part to the same 1.0, and exercised timeout/transcript/append mechanics live with a sleeping stub. Its first two findings were fixed and regression-tested (21 passed): usage parsers swallow JSON-valid non-object output, and a pre-existing trial directory is refused. A later code review found eight more integrity gaps; all are fixed with adversarial regressions, and the suite now passes 29/29 in CI-equivalent execution.

#### Tasks Completed
- Real subscription smoke trial: claude 2.1.220, haiku, low effort → score 1.000, 15 turns, 147s, usage captured; artifacts in evals/results/smoke-haiku-low/ (gitignored).
- `harness.py`: isolated Claude/Codex adapters, full JSON event transcripts, best-effort usage parsing, and harness version capture per row. `run.py` kills the entire harness process group at the wall-clock cap, so agent-spawned children cannot outlive a trial.
- `run.py`: required model/effort identity; per-trial materialize → isolated CLI on subscription → grade → JSONL row + kept transcript; wall-clock timeout as the turn cap; headless preamble overriding the skill's interactive directives; evals venv bin prepended to PATH so `nurb` resolves inside the trial.
- `materialize` now seeds AGENTS.md from the shipped nurb skill (same context a real project gets).
- Runner tests via a stub harness; full suite at 29 passed.
- Verified locally: claude 2.1.220 (`-p --output-format stream-json --safe-mode`, native `--effort` low..max, no `--max-turns` flag), codex 0.139.0 (`exec --json --ignore-user-config --ephemeral -s workspace-write`, `-c model_reasoning_effort=`).

#### Evidence
- `cd evals && uv sync --locked --dev && uv run pytest -q` → `29 passed in 101.80s`.
- Root CI command `uv run pytest -q -n auto` → `295 passed, 1 skipped in 38.62s`.
- Adversarial score matrix: good=1.000; wrong walls=0.7445; blocked channel=0.7445; offset hole=0.7445; forged-stdout candidate=0.000.
- Claude and Codex isolation/transcript flags parse successfully in the installed CLIs; runner help requires model and effort.

#### Decisions Made
- Inspect AI dropped entirely; the runner loops trials itself. RESEARCH.md carries the pivot rationale.
- Trials run on the host like any normal agent session (claude with permissions skipped in a throwaway dir, codex in its own workspace-write sandbox); containerization is a later hardening step, noted for the README.

#### Blockers
None.

#### Review Hardening
- [x] Isolate scorer verdicts from candidate-controlled stdout and module state.
- [x] Add adversarial checks for wall/tab dimensions, full-length channel, and hole placement/depth.
- [x] Isolate harness configuration, retain full Claude event transcripts, and require row identity including a content hash of the task, scorer, adapters, nurb package, and lockfile.
- [x] Run the eval suite in CI.

### Phase 3: First real comparison, report, community docs
**Status:** Complete
**Verified:** Yes — fresh-context verifier reproduced REPORT.md byte-identically from the raw rows and hand-checked the haiku row's arithmetic (mean, built 2/3 with the two-solid trial excluded from the gate, pass@1 0.67, tokens 33,125, wall 470s); ran both suites (36 evals + 295 root at the time); confirmed polished.py grades 1.0 and all four negative controls still fail with their intended messages; and followed the README literally to produce a real row end to end (haiku/low seed 7, score 1.0, 22 turns, 244s, transcript and project retained, report renders it). Its adversarial pass (3c) found one real cheat: a wall lopped to 55% height scored 1.0 because wall material was only probed at mid-depth. Fixed with channel-side near-top probes; the cheat geometry is now tests/solutions/short_wall.py with its own test; suite 37 passed; all 10 real trial parts re-graded identically, so the committed table is unaffected.

#### Tasks Completed
- Real matrix on subscription CLIs, seed 13 x 3 trials each: claude/fable/high (0.950), claude/haiku/low (0.667, one two-solid gate failure), codex/gpt-5.5/medium (1.000). Model names sanity-checked one-shot before launching (codex's configured gpt-5.6-sol is rejected by CLI 0.139.0; gpt-5.5 works).
- `report.py`: results.jsonl → markdown leaderboard (mean score, MUSE-style conditional cascade built/lint/dims/flex, unbiased pass@1/pass@3, tokens, wall time), grouped by full row identity including harness and benchmark revisions. 8 tests.
- Rows now record `built`; the report's gate column requires past-the-gate (a two-solid build is built=true with a gate error) and infers it for rows written before the field existed.
- `evals/README.md` (what a row is, cost expectations, run + submit, tiers, spot-check policy) and `evals/REPORT.md` (the committed 3-row leaderboard with notes from the runs).
- Fairness review found and fixed a real scorer bug (see Lessons); the chamfered trial part is now `tests/solutions/polished.py`, a permanent positive control. All 9 trial parts re-graded under the fixed scorer and rows rewritten (usage/timing untouched); only fable's scores changed.

#### Evidence
- Matrix rows + full transcripts in `evals/results/{claude-fable-high,claude-haiku-low,codex-gpt-5.5-medium}/` (gitignored; report committed).
- `cd evals && uv run pytest -q` → 36 passed (was 29; +6 report, +1 polished control). Root `uv run pytest -q -n auto` → 295 passed, 1 skipped.
- Re-grade log: fable 0.633/0.558/0.558 → 1.0/0.925/0.925 (0.925s are a real sliver WARN from its chamfers); haiku and codex rows unchanged by the fix.
- Transcript checks: zero `nurb dev` attempts in all 10 transcripts (headless preamble held); codex parts differ from each other and from good.py (authored, not planted).

#### Decisions Made
- Scorer fix over instruction fix: the instruction only forbids chamfers inside the channel, and the shipped skill (seeded into the project) teaches polishing outside edges, so the wall/tab/hole checks now probe material at heights an edge break cannot reach instead of demanding exact top-face spans. Amending the instruction to forbid chamfers would have made the task fight nurb's own doctrine.
- Re-grade rather than re-run: the instruction text never changed, so the kept transcripts and parts stay valid; only the grading was corrected.
- Cascade columns are conditional: lint/dims/flex average built trials only; total score averages everything with gate failures as zeros. The footnote travels with every table, including the cross-harness token-counting caveat.
- Pass threshold 0.99; pass@k via the Chen et al. unbiased estimator.

#### Blockers
None.

### Phase 4: First function task (bundle_holder), multi-task runner
**Status:** Complete (one leaderboard row pending: fable/bundle_holder re-run under the coexistence instruction, deferred to spare Josh's usage limits)
**Verified:** Yes — fresh-context verifier independently passed criteria 1-7 (56-test suite, reference and flawed-control grades with flaws in intended stages, no hardcoded task path, 8.6s grading, real fable trial audited including a transcript sweep for `nurb dev` attempts, report/REPORT.md number match, all seven adversarial cheats dead at <= 0.75, root suite 295 passed). Its own adversarial spot-check (criterion 8) found one new 1.0 cheat, the screw-through-the-seat part; fixed with the screw/bundle coexistence rule, adopted as tests/solutions/bundle_holder/screw_in_seat.py (now 0.6666), suite 57 passed.

#### Tasks Completed
- `tasks/bundle_holder/`: instance/misfits/flex_probes/materialize. Retention on mesh cross-sections (nurb's builder tessellates, trimesh sections, shapely erosion by the bundle radius); mount as bore-candidate circles plus probe walks; volume ladder with thresholds stated in the instruction.
- `scoring.py`: misfit entries may be `(message, weight)`; strings stay weight 1, cable_clip unchanged.
- `run.py`: part path derived from the task directory name; `PART_FILE` constant gone. Stub harness parameterized; a runner test covers a non-cable_clip task.
- Solutions reorganized into `tests/solutions/{cable_clip,bundle_holder}/`; six bundle_holder references (good, shelf_only, no_hole, blocked_head, hardcoded tunnel, bloated brick) and an 11-test fairness suite.
- shapely/networkx/rtree added to evals deps only (trimesh's optional path stack); nurb's four dependencies untouched.
- CLAUDE.md: evals/ pointer added to Layout; stale `--strict-ish` mention removed (verified no such flag in cli.py).
- README.md: task-classes section, multi-task run commands.

#### Evidence
- `cd evals && uv run pytest -q` → 49 passed in 158s (was 37).
- Root `uv run pytest -q -n auto` → 295 passed, 1 skipped in 35.56s.
- Grade CLI at seed 13 (bundle 8.0): good 1.0, bloated 0.9 (volume ladder only), hardcoded 0.8 (dims 1.0, flex 0), blocked_head 0.7333, shelf_only 0.6666, no_hole 0.6 — every flaw caught in its intended stage, strict user-facing order, grading ~5s per part.
- Real smoke trial (claude/haiku/low, seed 13): 0.525 at run time, 0.3916 under the final hardened scorer (its 0.5mm walls are sub-printable, so the foil rule now refuses them as retention too) — the penalties are a square 4.4mm "bore" slot cut at the part's Y-edge, sub-min_wall walls, and the mount. haiku one-shot cable_clip at 1.0, so the function task separates where the spec task could not. Transcript's only `nurb dev` mention is the model restating the prohibition; its opening summary enumerates every stated check correctly, so the instruction is followable by a small model.
- Adversarial pass (fresh-context agent told to cheat): seven cheats, four at a perfect 1.0 (hidden tunnel septum between sampling stations; retention from a 1.4mm finger at one station; bore skinned over with slots at the exact probe points; both combined) and three at 0.925 where only a min_wall WARN objected (0.09mm sealing membranes, 0.15mm foil lip, a 0.9mm wall between the head probe's 1.0mm steps). Hardened with feature-aware stations (a section lands inside every distinct mesh-vertex-Y gap), blocking on morphologically opened sections along at least a third of the length, and a continuous virtual-screw boolean (4.0 shank + 8.1 head as one gapless solid swept over seat depths). All seven cheats now score 0.39-0.67 with the right misfit named and live as parametrized regressions; all six reference controls kept their exact scores; grading stays 5-11s.
- Real-trial fairness round: codex's trial 2 held the bundle with two honest 3.3mm end fingers (44% of length) after its head slot bisected the lip — the initial half-length rule rejected it, so HOLD became one third (the fingernail cheat is 12%). Its rows stand as recorded (re-grade matches: 1.0 / 0.8 / 1.0; the 0.8 is a genuine flex miss, back face shrinking under 100mm2 at grown bundles). fable's identical 0.925x3 exposed the card-acceptance trap: it accepted its cosmetic slivers per the shipped doctrine, its own `nurb check` then reported clean, and the frozen-context grader (which must ignore cards) still charged the WARN. Phase 3's fable cable_clip 0.925s were the same trap (cards say `[accepted] sliver`). Both instructions now state that the grader ignores card acceptances; fable's rows on both tasks are re-running under the corrected instruction; codex and haiku never used acceptances, so their rows stand.
- Two scorer bugs found and fixed during control grading: the eroded search-window rim read as phantom blocking material (shelf_only and hardcoded both scored 1.0 until candidate centers were clipped to the part's neighborhood), and edge bounding boxes come from the mesh once retention has tessellated the shape (bore rims widened to ~0.9 in X; axis test now uses the circle's plane normal).

#### Decisions Made
- Phase 4 scope decided here (the plan ended at Phase 3): the first function task, because the recorded lesson is that cable_clip cannot separate strong models and the corpus principle makes function tasks the majority class. One task done exhaustively fair over several done shallowly; every task so far has needed an adversarial iteration loop.
- Scoring contract extended minimally: a misfit entry may be `(message, weight)` instead of a bare string; strings keep weight 1, so cable_clip is untouched. Function tasks need functional gates to outweigh finish checks.
- Working the arithmetic showed the recorded stage-overlap lesson does most of the ordering work: a part that fails a functional gate at the default size fails both flex probes too, which is what puts broken-function parts below a correct-but-decorative one without extreme weights.
- The material-volume gradient is excluded from flex re-assertion (the task hands flex probes dims with the thresholds cleared): flex measures parameter honesty, and double-charging a size-independent volume miss would rank a fat-but-working holder below a hardcoded one.
- Retention is checked on mesh cross-sections with 2D morphology (tessellate via nurb's builder, sections along Y, shapely erosion by the bundle radius), because probing OCCT point-membership over a position grid is two orders of magnitude too slow. shapely is an evals-only dependency; nurb's own dependency budget is untouched.

#### Final matrix (all committed rows re-verified against the final scorer)
- bundle_holder: codex/gpt-5.5/medium 0.933 (1.0/0.8/1.0), haiku/low 0.253 (0.133/0.133/0.492); fable/high pending re-run (its 1.000x3 trials predate the coexistence rule, and two of those parts violate it, so re-scoring them would be unfair in the other direction; the run was stopped mid-flight at Josh's request to spare usage limits and REPORT.md marks the row pending). cable_clip: fable 1.000 (x3, re-run), codex 1.000, haiku 0.667 (unchanged phase 3 rows). The function task spreads the field where the spec task tops out, which was the phase's purpose.
- fable's three bundle_holder parts have distinct hashes, differ from good.py, and trial 1 designs its own J-channel with `measured()` and a derived screw-height stack-up: authored, not planted.
- Final suites: evals 64 passed in 306s; root 295 passed, 1 skipped in 40s. REPORT.md regenerated from committed, sanitized submissions for both tasks with per-run notes.

#### Blockers

### Phase 5: First judgment task (leg_cup), measurement-flex probes
**Status:** Complete
**Verified:** Yes — fresh-context verifier passed all seven criteria independently (both suites, the designed ladder reproduced exactly with each flaw in its intended stage, all six earlier cheats at or below 0.95, the probe A/B asymmetry, the MeasurementError gate, and 8.4s grading). For criterion 6 it did better than asked: finding no phase-4-era recording of cable_clip reference scores to compare against, it monkeypatched the scorer back to the pre-phase-5 probe contract and re-graded all 15 references under both, 0 mismatches in score or stages. Its adversarial pass (which mapped the union of the material probes rather than guessing) found one 1.0 cheat and one 0.925 near miss; both are fixed and kept as controls (see Evidence).

#### Tasks Completed
- `scoring.py`: probe specs are now `{"params", "measurements", "label"}` dicts (both existing tasks updated to the new shape); optional `task.audit(part_path, inst, book)` hook merges paperwork checks into the dims stage, `book` being the measurements file snapshotted before the first build.
- `candidate.py`: a probe carrying measurements text builds a copy of the part inside a staged scratch project holding the rewritten `measurements.toml`, so `measured()` resolves against the probe's file.
- `tasks/leg_cup/`: instance (seeded leg_width 18-30 x leg_depth 14-24, forced distinct; two seeded in-band probe lifts), instruction stating every scored dimension plus the doctrine-referenced paperwork check, misfits with continuous booleans (virtual-leg clearance, floor slab, and the three-piece wall cover, all held 1.1mm clear of edges so a doctrine chamfer is never charged), audit (lift entry exists, provisional = true, non-empty how; weight 3 of 15), two measurement-flex probes (A grows the legs with height judged by the band so an in-band inline guess passes; B moves lift alone and checks height exactly), materialize (legs on file, lift deliberately absent, AGENTS.md seeded).
- 8 references in `tests/solutions/leg_cup/` + fairness suite; paperwork-flawed references reuse good.py with different lift entries written by the test (the graded artifact is part + measurements edit).
- Adversarial pass and hardening: six cheats scored 1.0 against the first scorer, all now dead and kept as parametrized negative controls (see Evidence).
- README.md: judgment class documented, leg_cup run command added, and the residual trust boundary written down (a part that detects the grading process and exports different geometry survives a re-run; out of the threat model because the graded agent never sees the grader and a contributor who does could forge rows outright, so the defense is that submitted parts are published and readable).
#### Evidence
- Ladder at seed 13, every flaw named in its intended stage: good 1.0, polished 1.0 (doctrine-chamfered rim positive control), out_of_band 0.9334 (band, honest, tracks), fake_measured 0.9 (audit only), guessed_inline 0.8 (audit + lift probe), hardcoded_all 0.7 (audit + both probes), wrong_pocket 0.6333 (bbox/floor/ring + both probes), missing_lift 0.0 (gate, MeasurementError naming lift).
- `uv run pytest tests/test_leg_cup.py -q` → 18 passed in 63s (~5s per grading, criterion <30s met).
- Adversarial pass (fresh-context agent told to cheat): six cheats at a perfect 1.0. Four geometric (four 2.2mm posts planted under the four rim point probes with the rest of the top 1.14mm of wall gone; walls thinned to 1.05mm above the ring boolean's 1.1mm inset; a pocket lofted 0.07mm shut between the floor face and the mouth plus a 0.5mm hole drilled through the "solid" floor, all inside the 10% volume band; walls severed from the floor by hairline slits in the 0.1mm plane between the slab and ring booleans). Two paperwork (a part appending its own provisional [lift] entry at import, and lift as a keyword default with honest paperwork, caught only by probe B). Two more at 0.925 where only a sliver WARN objected. Hardened: `_missing()` booleans throughout, the wall now covered in three overlapping pieces (inner ring from the floor plane up, four corner-trimmed outer slabs, and a sub-rim horizontal section that must return exactly one closed loop), slab and ring overlapping at the floor plane, leg clearance slack 0.05 → 0.02, boolean leak tolerance 1.0mm3 → 0.05mm3, and the audit reading the measurements file as it stood before the first build. All six now score 0.63-0.90 with the closing check named, and live as parametrized regressions.
- Verification round: the verifier's own adversarial pass found the lift clamp at a clean 1.0 (`lift = max(measured("lift"), 3.5)` next to an honest, in-band `value = 2.0`, so the recorded number and the built one were never once compared) and a hollow-bottom cup at 0.925 (an undercut groove under the walls, which no dimensional check reached because the bottom of the part was covered by nothing). Fixed: the audit now also requires the built lift to equal the recorded value, and the floor slab widened from the pocket footprint to the whole footprint, so one boolean carries both the solid floor and the flat bottom. Both live as controls at 0.9 and 0.6583, and every other rung of the ladder is unchanged.
- Final ladder at seed 13: good 1.0, polished 1.0, out_of_band 0.9334, fake_measured 0.9, self_recorded 0.9, recorded_but_hardcoded 0.9, clamped_lift 0.9, guessed_inline 0.8, rim_posts 0.7667, thin_walls 0.7667, hardcoded_all 0.7, severed_walls 0.6916, hollow_bottom 0.6583, wrong_pocket 0.6333, kitchen_sink 0.6333, missing_lift 0.0.
- Final suites: evals 84 passed in 398s (was 64 at the start of the phase); root `uv run pytest -q -n auto` 295 passed, 1 skipped in 44s. cable_clip and bundle_holder reference grades proven identical under the old and new probe contracts, so no committed row moves.
#### Decisions Made
- Phase 5 scope decided here (the plan ended at Phase 4): the judgment class's refusal-to-guess task, named in RESEARCH.md, because it is the last unproven class and forces the one scorer generalization still missing (measurement-flex probes). Design in IMPLEMENTATION.md Phase 5.
- Designed score order recorded deliberately: in a judgment task, honest recording outranks guess accuracy (out_of_band above fake_measured), silent guessing ranks below both, broken geometry at the bottom per the phase 1 precedent. The paperwork check is stated by reference to the doctrine, which the model holds in context three ways (nurb rules, seeded AGENTS.md, measured()'s own error message); the instruction names the nurb check reminder without leaking the provisional mechanism, applying the card-acceptance lesson (state what the grader ignores) without giving the judgment away.
- Point-probe walls check replaced with a continuous ring boolean before the adversarial pass, applying the recorded lesson directly. It was not enough: the four point probes left to cover the top 1.1mm were exactly where the cheater built, which is the lesson restated (a boolean that stops short hands the adversary the remainder).
- The two infrastructure cheats split on whether the graded agent could reach them. The self-recording paperwork cheat is reachable (a model could plausibly write measurements from its part file), so the audit now reads the pre-build snapshot. Exported-B-rep tampering and grading-process detection are not reachable (the agent never sees the grader) and are unfixable against a contributor who owns the machine and could forge rows anyway; `os._exit` closes the atexit variant for free, and the boundary is documented in README.md rather than papered over.
#### Blockers

### Phase 6: Print-physics function task (shelf_bracket)
**Status:** Not Started (scoped 2026-08-02; design sketch and criteria in IMPLEMENTATION.md Phase 6)
**Verified:** No

#### Tasks Completed
#### Evidence
#### Decisions Made
- Scoped as pure content: no scorer changes expected, since phase 5 completed the contract. The task makes print physics the binding constraint, with two honest escapes (gusset geometry, print-friendly orientation) that must both score 1.0.
#### Blockers

### Orphaned-candidate fix (queued during the fable rows, landed after)
~20 leaked `hangs.py` candidate processes from earlier sessions were found spinning on CPU (killed by hand). The queued diagnosis (grade.py's outer kill) turned out wrong on inspection: candidates run in their own sessions precisely so the scorer can kill them selectively, so no ancestor's process-group kill can reach them, from grade.py or anywhere else. The landed fix is in the candidate itself: a watchdog thread exits the process the moment its parent is gone (`getppid()` becomes 1 or changes), which covers every death of the stack above it, including an interrupted test run. Regression: a wrapper spawns the candidate on hangs.py and dies immediately; the orphan must be gone within 20s (it exits in ~3).

### Fable rows (run 2026-08-02 with Josh's go-ahead)
- bundle_holder re-run under the coexistence instruction: 1.000 x 3 (~12.7 min and ~12k tokens per trial). The pending row is closed; REPORT.md now shows fable 1.000 / codex 0.933 / haiku 0.253.
- leg_cup first row: 1.000 x 3, the cheapest row yet (~13k tokens, ~3.5 min per trial). Audited like a cheater before trusting it: three distinct authored parts, none matching good.py, all reading measured() for all three names; all three measurements.toml files record lift honestly (provisional = true, real provenance notes like "measure the real gap at the bench and update"); zero `nurb dev` attempts in any transcript; trial 1 independently re-graded to the same 1.0.
- Sanitized transcripts, parts, and (for leg_cup) measurements.toml copied under `submissions/claude-fable-high/`; leak scan clean; REPORT.md regenerated with all three task tables.

### Unattributed working-tree changes (2026-08-02, flagged to Josh)
Between the last pre-commit suite run and the "commit it" commit, changes appeared in the tree that this session did not author: candidate.py's `_stage` upgraded to copy the whole candidate project (so parts can import root-level helpers; my version copied the part file alone), a matching `test_measurement_probes_preserve_project_helpers`, and a handful of tests elsewhere. Reviewed after the fact: sound, better than what they replaced, and green in the full suites. Presumed to be Josh or a parallel session; recorded here because they shipped in commit fe31200 without in-session review.

---

## Session Log

- 2026-08-01: Research completed (three parallel subagents + adversarial verification of Inspect claims). Docs written. Phase 1 built, verified, and hardened: the verifier's adversarial pass found the closed-tunnel cheat, now fixed and regression-tested. Root pytest scoped to tests/ so it stops collecting evals/.
- 2026-08-02: Review hardening completed. Candidate code moved behind a BREP worker boundary; scorer assertions now cover constituent X dimensions, full channel length, and centered full-depth hole; harnesses run without contributor customizations and keep full event streams; row identity is mandatory; eval tests run in their own CI job.
- 2026-08-02: Workspace review fixes completed. The one-solid gate now applies to flex builds; both tasks continuously verify the stated bore diameter; harness timeouts kill descendant processes; rows carry a content-hashed benchmark identity; the published leaderboard now links 15 sanitized transcripts and three result files under `submissions/`. All 15 published candidates re-graded at unchanged scores under the hardened scorer.
- 2026-08-02: Phase 3. Real 3-row matrix run on subscriptions; the first grading exposed the top-face-span scorer bug (fable's doctrine-following chamfers cost 3 dims checks + all flex), fixed with probe-based checks and a positive control; all trials re-graded; report.py, README.md, REPORT.md written. Verifier passed all criteria and found the half-height-wall cheat; fixed, short_wall.py added, table unchanged. Suites: evals 37 passed, root 295 passed / 1 skipped.

- 2026-08-02: Phase 4. bundle_holder function task built and proven fair: 6 reference controls in designed order, adversarial pass found 7 cheats (4 at 1.0), all killed structurally (feature-aware stations, opened-section blocking over a third of length, continuous virtual-screw boolean) and kept as regressions. Real matrix: fable 1.000, codex 0.933, haiku 0.253 on bundle_holder. Two fairness rulings from real trials: HOLD lowered to 1/3 for codex's honest two-finger design, and the card-acceptance trap fixed in both instructions with fable's rows re-run (its 0.925s on both tasks were the trap; corrected, it sweeps). Runner generalized to per-task part paths and per-task trial slots; solutions reorganized per task; REPORT.md now covers both tasks.

- 2026-08-02 (late): Leaderboard grown to five models on all three tasks (fable, opus, sonnet at high; haiku at low; gpt-5.5 at medium; 45 committed trials). leg_cup separates on honesty exactly as designed: four models record the provisional guess correctly, haiku writes its guess as if measured (its three trials land on the fake_measured and hardcoded rungs of the designed ladder). sonnet's bundle_holder exposed the retention vertex-explosion scorer bug (two trials wrongly zeroed by the grading cap); fixed score-neutrally and rows re-graded per the phase 3 precedent. opus twice ran out the 900s harness cap with already-perfect parts on disk; sonnet spent the full cap on every bundle_holder trial and its working-but-unprintable cradles (50deg overhangs, 0.86mm wall, tipping) are the function-without-print-physics story. Benchmarks page and REPORT regenerated; verdicts updated.
- 2026-08-02: Phase 5 verified. The verifier passed every criterion and found the lift clamp (paperwork and geometry never cross-checked) plus a hollow-bottomed cup (the part's bottom was covered by no check at all); both fixed, both kept as controls, ladder otherwise unchanged. Evals suite 84 passed, root 295 passed / 1 skipped.
- 2026-08-02: Phase 5. leg_cup built as the corpus's first judgment task: geometry stated, the lift dimension deliberately unmeasured, and measurement discipline scored by measurement-rewriting flex probes plus a paperwork audit. Scorer generalized (probe specs carry measurements text, candidate stages a scratch project so measured() resolves against the probe's file, optional task.audit merges into dims). Adversarial pass found six cheats at 1.0, four geometric and two paperwork; all killed structurally and kept as regressions, with the harness-level residue documented rather than chased.

## Files Changed

- evals/tasks/leg_cup/{task.py,fixture/} (new, phase 5); evals/tests/test_leg_cup.py + tests/solutions/leg_cup/ (11 references incl. 6 adversarial cheats)
- evals/src/nurb_evals/scoring.py (probe specs, audit hook, measurements snapshot), candidate.py (staged measurement builds, os._exit), evals/tasks/{cable_clip,bundle_holder}/task.py (probe shape), evals/README.md (judgment class, trust boundary)
- docs/evals/RESEARCH.md, IMPLEMENTATION.md, PROGRESS.md (new)
- evals/pyproject.toml, evals/src/nurb_evals/{__init__,candidate,scoring,grade,harness,run}.py (new)
- evals/tasks/cable_clip/task.py, fixture/printer.toml, fixture/parts/.gitkeep (new)
- evals/tests/{test_scoring,test_runner}.py and adversarial/reference solutions (new)
- pyproject.toml (root): [tool.pytest.ini_options] testpaths = ["tests"], so root CI does not collect evals/
- .github/workflows/test.yml: dedicated evals job running from `evals/`
- evals/src/nurb_evals/report.py, evals/tests/test_report.py, evals/README.md, evals/REPORT.md, evals/tests/solutions/{polished,short_wall}.py (new, phase 3)
- evals/tasks/cable_clip/task.py (wall/tab/hole checks rewritten probe-based), evals/src/nurb_evals/run.py (rows record built)
- evals/tasks/bundle_holder/{task.py,fixture/} (new, phase 4); evals/tests/test_bundle_holder.py (new); evals/tests/solutions/ reorganized per task, 13 bundle_holder references incl. 7 adversarial cheats
- evals/src/nurb_evals/scoring.py (weighted misfits), run.py (per-task part path and trial slots), evals/pyproject.toml (shapely/networkx/rtree), evals/README.md (task classes, multi-task rows), evals/REPORT.md (two-task leaderboard)
- evals/tasks/cable_clip/task.py + bundle_holder/task.py instructions (grader ignores card acceptances)
- CLAUDE.md (evals/ pointer in Layout; stale --strict-ish removed)

## Architectural Decisions

- Corpus splits into spec tasks (execution fidelity, ~3), function tasks (problem + interfaces stated, functional gates + quality gradients scored, the majority), and judgment tasks; taste is never in the core score. Rationale and detail in RESEARCH.md's Corpus Design Principle (decided with Josh, 2026-08-02).

- Scorer context is owned by task.py, never read from the candidate's card or fixture printer.toml — card muting must be ineffective by construction.
- Candidate builds run in a process-group-isolated worker and cross into the trusted scorer only as BREP geometry; an outer subprocess retains the hard timeout for BREP imports and checks.
- Graded partial credit (lint 0.3 / dims 0.5 / flex 0.2 behind a build gate) so 3 trials give stable means.

## Lessons Learned

- **Iterated booleans on curved sections compound vertices without bound.** bundle_holder's retention intersects 113 per-station fit polygons; on boxy parts they are near-identical rectangles and the accumulated region stays small, but sonnet's tube cradle made every section a slightly-different tessellated curve and the region reached 1.2 million vertices, grinding retention past the grading cap so two legitimate trials were zeroed for grader slowness. Fix at the source, not the symptom: snap section polygons to a micron grid (three orders below every scored tolerance) so near-duplicate vertices collapse instead of compounding, and prepare geometries before batch predicates. Proof of score-neutrality is mandatory: exact fairness-suite scores plus re-grading every committed part, inside materialized projects (a bare re-grade of a measured()-reading part fails the gate on the missing file and looks like drift).
- **A grading cap is a fairness surface.** Any part that grades slower than the cap scores zero indistinguishably from a part that is wrong, and the parts that grade slowest are systematically the curved, organic designs one model family favors. When a strong model posts zeros with empty misfit lists, suspect the grader's wall clock before the model.
- **A continuous check that stops short is a point-probe check.** leg_cup's walls were a boolean from the start, applying the phase 4 lesson, and the cheater still swept it: the boolean stopped 1.1mm below the rim to stay clear of doctrine chamfers, four point probes covered the remainder, and the cheat built four posts under exactly those four points. Every gap a continuous check leaves for tolerance is where the next cheat lives. Fix: cover the remainder with a different continuous measure rather than samples (here a horizontal section that must come back as one closed loop, which tolerates a chamfer's thinning but not a wall's absence), and overlap adjacent booleans instead of insetting both away from their shared plane.
- **A judgment task has to cross-check the paperwork against the part.** leg_cup graded the recorded lift for existence, provisional marking, and provenance, and graded the geometry for being in the stated band, but never compared the two: a part clamping its lift into the band scored 1.0 while its own file recorded a different number, which is the doctrine's failure mode (a value that looks measured and is not) wearing the paperwork meant to prevent it. Whenever a task scores a file and a shape separately, one check has to tie them together.
- **Map the union of the probes, do not guess at them.** The verification pass that found the most listed every region the material checks cover and looked at what was left over, which surfaced that the entire bottom of the part was unchecked: a cup standing on a hollow groove passed every dimensional check and lost only a sliver WARN. Faces the instruction states but no check reads are where the next cheat lives, and they are findable by arithmetic rather than imagination.
- **Grade the paperwork as it stood before the part ran.** A judgment task's audit reads files the candidate can write: a cheat appended its own provisional entry at import time and scored full marks for measurement discipline the submission generated itself. Snapshot anything scored outside the geometry before the first build.
- **Name the trust boundary instead of chasing it.** The verification pass reached the harness itself (rewriting exported B-reps from an atexit hook, detecting the grading process from argv). Both need knowledge of the grader that a graded agent never has, and anyone who does have it can forge result rows directly, so hardening the process buys nothing a published, readable part file does not. Take the free fix (`os._exit` so no exit hooks run), write the boundary into README, and spend the effort on cheats a model could actually produce.
- **Point probes lose to adversaries; continuous geometry wins.** The cheater beat every finite probe set: material between stations, slots at the exact probe points, walls between step positions. The fixes that killed all seven cheats share one shape: make the check continuous or feature-aware (sections at every mesh-vertex gap, morphological opening, a boolean sweep of the actual screw solid). When a check samples, ask what fits between the samples.
- **The instruction must say what the grader ignores.** The frozen context ignores card `[accepted]` blocks by anti-gaming design, but the shipped doctrine teaches accepting cosmetic findings, and `nurb check` then reports clean: fable did exactly that on both tasks and lost lint points while its own tools said zero findings. If the grader deviates from what the model's feedback loop shows, the instruction has to state the deviation, or the benchmark punishes doctrine-following.
- **Function tasks probe functional honesty, not parameter plumbing.** A hardcoded U-channel with a tall back plate wedges a grown bundle between plate face and lip corner and passes the flex probes, because it genuinely still holds the bundle: the stated contract is functional and the part meets it. Only a design whose function actually breaks at the probed sizes (a snug tunnel) is a valid flex negative control. Decorative-parameter detection in the strict sense belongs to spec tasks.
- **Erosion-based searches must keep their window rim out of reach.** Negative-buffering a free region erodes at the search window's own boundary too, and a sampler near that rim reads it as blocking material: both shelf_only and hardcoded scored 1.0 until candidate centers were clipped to the part's neighborhood. Any future erosion search needs window margin > erosion radius + probe shift, plus a clip.
- **Tessellating a shape changes what its edges report.** After `shape.mesh()` (inside any tessellation), `edge.bounding_box()` comes from the triangulation: an exact Y-Z circle widens to ~0.9 in X from chord sagitta, silently breaking axis tests that ran fine before the retention check tessellated. Classify edges by their geometry (`edge.normal()`), never by post-mesh bounding boxes.

- **Adversarial verification of the scorer is not optional.** A fresh-context agent told to cheat found in one pass what the fairness suite missed: every existence assertion needs a matching void assertion (the floor existing says nothing about the channel being open). It paid again in phase 3: probe-based checks need probes at every extent the instruction states (mid-height wall probes said nothing about wall height, so a half-height wall scored 1.0). When adding a task, ask "what part satisfies every check while ignoring the request?" and add that part as a negative control.
- **Stage scores overlap by design.** A part wrong at defaults also fails flex (it is wrong at every size). This double-penalty produces the right user-facing order (functionally-broken < correct-but-decorative); do not "fix" it by deduplicating, but say so wherever the cascade columns are explained.
- **cable_clip does not separate strong models.** haiku at low effort scores 1.000 in one try, which is fine for the slice (it proves the pipeline, not the ranking) but means the corpus needs harder tasks — chamfer interactions, overhang traps, the refusal-to-guess task — before rows are comparable at the top.
- **Verify the runner like a cheater, not like a user.** Both verification passes paid for themselves: the pre-seeded trial directory would have minted perfect rows with audit-plausible artifacts. Every anti-gaming fix gets a regression test written from the cheat itself.
- **The evals venv is its own world.** Run everything from evals/ (`cd` drift silently runs the root project's environment, which cannot import nurb_evals), and root pytest must stay scoped to tests/.
- **`uv --project` does not change process cwd.** CI must set `working-directory: evals`; otherwise pytest reads the root configuration and silently runs the wrong suite.
- **Assertions must survive the doctrine the eval itself ships.** The scorer seeded AGENTS.md with a skill that teaches chamfering outside edges, then identified walls/tab/hole by exact top-face spans, which a 1mm chamfer shrinks: the flagship following the doctrine scored below the small model ignoring it, identically on all three trials. Identical failure signatures across independent trials of a strong model mean "look at the scorer first". Fix: measure like a machinist (material probes at heights an edge break cannot reach), and keep the doctrine-following part as a positive control next to the negative ones.
- **Real trials leak the contributor's machine into the sandbox.** Codex read the globally installed nurb skill at ~/.agents/skills (same content as the seeded AGENTS.md, so harmless here) and followed the editable install back into the repo checkout, which also contains the reference solutions and task assertions. Reading assertions gains nothing by design (everything scored is stated in the instruction), but a model that finds tests/solutions/good.py could copy it. Containerized trials, or at least a non-editable nurb install for trial venvs, is the hardening step; validated-tier spot-checks at fresh seeds are the current mitigation.
- **Harness token numbers are not comparable across harnesses.** Claude's input_tokens excludes cache reads (tens of tokens per trial); codex reports full per-turn context (hundreds of thousands). The report says so under every table; never rank on the tokens column across harnesses.
