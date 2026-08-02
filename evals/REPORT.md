# nurb leaderboard

Three model and effort combinations across the three task classes, each row 3 trials at seed 13, run 2026-08-02 on subscription CLIs against nurb 0.9.0 and graded under the content revisions shown below. The spread is the corpus design working: the spec task (cable_clip) measures execution and tops out fast, the function task (bundle_holder) makes design judgment mechanical and separates the field, and the judgment task (leg_cup) measures measurement discipline the way nurb's doctrine defines it. The full rows and sanitized transcripts are committed under [submissions](submissions/); see [README.md](README.md) for how to run and submit a row.

## bundle_holder (seed 13)

| harness | benchmark | model | effort | trials | score | built | lint | dims | flex | pass@1 | pass@3 | tokens | wall | trial scores |
|---|---|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| claude 2.1.220 | 0.9.0/0.1.0@6c5a63bbdc84 | fable | high | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 36,535 | 610s | 1.000 / 1.000 / 1.000 |
| codex 0.139.0 | 0.9.0/0.1.0@1cd714991c83 | gpt-5.5 | medium | 3 | 0.933 | 1.00 | 1.00 | 1.00 | 0.67 | 0.67 | 1.00 | 1,003,614 | 365s | 1.000 / 0.800 / 1.000 |
| claude 2.1.220 | 0.9.0/0.1.0@1cd714991c83 | haiku | low | 3 | 0.253 | 1.00 | 0.25 | 0.36 | 0.00 | 0.00 | 0.00 | 36,462 | 534s | 0.133 / 0.133 / 0.492 |

`benchmark` is nurb/evals@content-revision and separates rows whenever the tool, task, scorer, harness adapter, or locked dependencies change. `score` averages all trials with gate failures as zeros; `built` is the fraction of trials past the gate, and lint/dims/flex average built trials only. A pass is a score of at least 0.99. Stage columns overlap by design: a part wrong at the stated size is wrong at every probed size too, so it loses dims and flex together. `tokens` is input plus output as the harness reports them, and harnesses count differently (claude's input excludes cache reads, codex counts full per-turn context), so compare tokens within a harness only.

## cable_clip (seed 13)

| harness | benchmark | model | effort | trials | score | built | lint | dims | flex | pass@1 | pass@3 | tokens | wall | trial scores |
|---|---|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| claude 2.1.220 | 0.9.0/0.1.0@f65057a28754 | fable | high | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 24,358 | 409s | 1.000 / 1.000 / 1.000 |
| codex 0.139.0 | 0.9.0/0.1.0@f65057a28754 | gpt-5.5 | medium | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 427,410 | 142s | 1.000 / 1.000 / 1.000 |
| claude 2.1.220 | 0.9.0/0.1.0@f65057a28754 | haiku | low | 3 | 0.667 | 0.67 | 1.00 | 1.00 | 1.00 | 0.67 | 1.00 | 33,125 | 470s | 1.000 / 1.000 / 0.000 |

`benchmark` is nurb/evals@content-revision and separates rows whenever the tool, task, scorer, harness adapter, or locked dependencies change. `score` averages all trials with gate failures as zeros; `built` is the fraction of trials past the gate, and lint/dims/flex average built trials only. A pass is a score of at least 0.99. Stage columns overlap by design: a part wrong at the stated size is wrong at every probed size too, so it loses dims and flex together. `tokens` is input plus output as the harness reports them, and harnesses count differently (claude's input excludes cache reads, codex counts full per-turn context), so compare tokens within a harness only.

## leg_cup (seed 13)

| harness | benchmark | model | effort | trials | score | built | lint | dims | flex | pass@1 | pass@3 | tokens | wall | trial scores |
|---|---|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| claude 2.1.220 | 0.9.0/0.1.0@c2f1130c6f0d | fable | high | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 12,852 | 211s | 1.000 / 1.000 / 1.000 |

`benchmark` is nurb/evals@content-revision and separates rows whenever the tool, task, scorer, harness adapter, or locked dependencies change. `score` averages all trials with gate failures as zeros; `built` is the fraction of trials past the gate, and lint/dims/flex average built trials only. A pass is a score of at least 0.99. Stage columns overlap by design: a part wrong at the stated size is wrong at every probed size too, so it loses dims and flex together. `tokens` is input plus output as the harness reports them, and harnesses count differently (claude's input excludes cache reads, codex counts full per-turn context), so compare tokens within a harness only.

## Notes from these runs

- bundle_holder is a function task: it states the problem (a measured bundle, one M4 screw, a P1S) and grades functional gates on the B-rep plus a material gradient, never the shape. The models produced genuinely different designs; all of fable's and codex's held the bundle and took the screw.
- fable's bundle_holder row is a re-run under the screw-and-bundle coexistence rule (a verification pass had found a part scoring 1.0 with its screw through the bundle's seat, and this benchmark re-runs rather than re-scores when the instruction changes). Its three earlier trials also scored 1.000 under the instruction they were given.
- codex's one 0.8 is a flex miss: its head-clearance slot design leaves under 100 mm2 of flat back face once the bundle grows 1mm, a real parametric flaw at exactly the stated minimum. Its retention there is two 3.3mm end fingers, which the grader accepts deliberately: blocking must span a third of the part's length, a line calibrated so honest minimal designs pass and a 1.4mm fingernail from the adversarial pass does not.
- haiku at low effort collapses on the function task (square "bore", sub-printable 0.5mm walls, blocked head paths) after scoring 1.000-when-it-built on the spec task. That contrast is the corpus design principle in one row: execution is not the same ability as design.
- leg_cup grades the refusal to guess: one dimension is deliberately unmeasured, the part has to track a rewritten measurements.toml, and the guess has to be recorded as provisional with provenance rather than baked into the code. fable did it right in all three trials, independently authored parts each reading measured("lift") against an honestly provisional entry with notes like "measure the real gap at the bench and update". It was also the cheapest row so far (about 13k tokens and 3.5 minutes per trial), which suggests the task is easy to do right once a model's instinct is to follow the doctrine; the interesting rows will be the models whose instinct is to guess.
- The fable rows on cable_clip and bundle_holder were first run before a benchmark bug fix, and its 0.925s were the bug: it accepted its cosmetic sliver findings in the part's card exactly as the shipped doctrine teaches, its own `nurb check` then reported clean, and the card-ignoring grader still charged the WARN. Both instructions now state that the grader ignores card acceptances; told that, fable fixes the slivers in geometry and sweeps.
- Every task's scorer survived a dedicated adversarial pass only after hardening; all cheat geometries found (hidden tunnel septa, fingernail retention, walls replaced by posts under probe points, self-written measurement paperwork, a lift clamped into the stated band) live in the fairness suites as regressions. leg_cup's pass also produced the two structural rules the suites now follow: map the union of what the probes cover instead of guessing, and cross-check the recorded paperwork against the built geometry.
