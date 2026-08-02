# nurb leaderboard

Three model and effort combinations on the first two tasks, each 3 trials at seed 13, run 2026-08-02 on subscription CLIs against nurb 0.9.0 and re-graded under the content revisions shown below. Two tasks still do not rank models, but the spread below is the corpus design working: the spec task (cable_clip) measures execution and tops out fast, while the function task (bundle_holder) makes design judgment mechanical and separates the field. The full rows and sanitized transcripts are committed under [submissions](submissions/); see [README.md](README.md) for how to run and submit a row.

## bundle_holder (seed 13)

| harness | benchmark | model | effort | trials | score | built | lint | dims | flex | pass@1 | pass@3 | tokens | wall | trial scores |
|---|---|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| codex 0.139.0 | 0.9.0/0.1.0@1cd714991c83 | gpt-5.5 | medium | 3 | 0.933 | 1.00 | 1.00 | 1.00 | 0.67 | 0.67 | 1.00 | 1,003,614 | 365s | 1.000 / 0.800 / 1.000 |
| claude 2.1.220 | 0.9.0/0.1.0@1cd714991c83 | haiku | low | 3 | 0.253 | 1.00 | 0.25 | 0.36 | 0.00 | 0.00 | 0.00 | 36,462 | 534s | 0.133 / 0.133 / 0.492 |

A third task, `leg_cup`, is built and proven fair against its reference set but has no rows yet: it is the corpus's first judgment task, where the geometry is stated and what is graded on top is measurement discipline (the part must track a rewritten `measurements.toml`, and the one dimension nobody could measure has to be recorded as a provisional guess rather than baked into the code). See [README.md](README.md) for what that class measures.

A claude/fable/high row is pending: its trials ran before the screw-and-bundle coexistence rule was added to the instruction (a verification pass found a part scoring 1.0 with its screw through the bundle's seat), and this benchmark re-runs rather than re-scores when the instruction changes. Its three pre-rule trials scored 1.000 / 1.000 / 1.000 under the instruction they were given.

`benchmark` is nurb/evals@content-revision and separates rows whenever the tool, task, scorer, harness adapter, or locked dependencies change. `score` averages all trials with gate failures as zeros; `built` is the fraction of trials past the gate, and lint/dims/flex average built trials only. A pass is a score of at least 0.99. Stage columns overlap by design: a part wrong at the stated size is wrong at every probed size too, so it loses dims and flex together. `tokens` is input plus output as the harness reports them, and harnesses count differently (claude's input excludes cache reads, codex counts full per-turn context), so compare tokens within a harness only.

## cable_clip (seed 13)

| harness | benchmark | model | effort | trials | score | built | lint | dims | flex | pass@1 | pass@3 | tokens | wall | trial scores |
|---|---|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| claude 2.1.220 | 0.9.0/0.1.0@f65057a28754 | fable | high | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 24,358 | 409s | 1.000 / 1.000 / 1.000 |
| codex 0.139.0 | 0.9.0/0.1.0@f65057a28754 | gpt-5.5 | medium | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 427,410 | 142s | 1.000 / 1.000 / 1.000 |
| claude 2.1.220 | 0.9.0/0.1.0@f65057a28754 | haiku | low | 3 | 0.667 | 0.67 | 1.00 | 1.00 | 1.00 | 0.67 | 1.00 | 33,125 | 470s | 1.000 / 1.000 / 0.000 |

`benchmark` is nurb/evals@content-revision and separates rows whenever the tool, task, scorer, harness adapter, or locked dependencies change. `score` averages all trials with gate failures as zeros; `built` is the fraction of trials past the gate, and lint/dims/flex average built trials only. A pass is a score of at least 0.99. Stage columns overlap by design: a part wrong at the stated size is wrong at every probed size too, so it loses dims and flex together. `tokens` is input plus output as the harness reports them, and harnesses count differently (claude's input excludes cache reads, codex counts full per-turn context), so compare tokens within a harness only.

## Notes from these runs

- bundle_holder is a function task: it states the problem (a measured bundle, one M4 screw, a P1S) and grades functional gates on the B-rep plus a material gradient, never the shape. The models produced genuinely different designs; all of fable's and codex's held the bundle and took the screw under the instruction they ran with.
- codex's one 0.8 is a flex miss: its head-clearance slot design leaves under 100 mm2 of flat back face once the bundle grows 1mm, a real parametric flaw at exactly the stated minimum. Its retention there is two 3.3mm end fingers, which the grader accepts deliberately: blocking must span a third of the part's length, a line calibrated so honest minimal designs pass and a 1.4mm fingernail from the adversarial pass does not.
- haiku at low effort collapses on the function task (square "bore", sub-printable 0.5mm walls, blocked head paths) after scoring 1.000-when-it-built on the spec task. That contrast is the corpus design principle in one row: execution is not the same ability as design.
- The fable rows on both tasks were re-run after a benchmark bug fix, and its earlier 0.925s were the bug: it accepted its cosmetic sliver findings in the part's card exactly as the shipped doctrine teaches, its own `nurb check` then reported clean, and the card-ignoring grader still charged the WARN. Both instructions now state that the grader ignores card acceptances; told that, fable fixes the slivers in geometry and sweeps both tasks.
- The scorer survived an adversarial pass only after hardening: seven cheat geometries (hidden tunnel septa, single-fingernail retention, bores skinned over with voids at the old probe points) scored 0.925-1.0 against point probes and are all caught by the current feature-aware sections, printable-width blocking, and continuous virtual-screw boolean. All seven live in the fairness suite as regressions.
