# nurb leaderboard

Five model and effort combinations across the three task classes, each row 3 trials at seed 13, run 2026-08-02 on subscription CLIs against nurb 0.9.0 and graded under the content revisions shown below. The spread is the corpus design working: the spec task (cable_clip) measures execution and tops out fast, the function task (bundle_holder) makes design judgment mechanical and separates the field, and the judgment task (leg_cup) measures measurement discipline the way nurb's doctrine defines it. The full rows and sanitized transcripts are committed under [submissions](submissions/); see [README.md](README.md) for how to run and submit a row.

## bundle_holder (seed 13)

| harness | benchmark | model | effort | trials | score | built | lint | dims | flex | pass@1 | pass@3 | tokens | wall | trial scores |
|---|---|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| claude 2.1.220 | 0.9.0/0.1.0@6c5a63bbdc84 | fable | high | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 36,535 | 610s | 1.000 / 1.000 / 1.000 |
| claude 2.1.220 | 0.9.0/0.1.0@46c733b2f7b1 | opus | high | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 42,234 | 814s | 1.000 / 1.000 / 1.000 |
| codex 0.139.0 | 0.9.0/0.1.0@1cd714991c83 | gpt-5.5 | medium | 3 | 0.933 | 1.00 | 1.00 | 1.00 | 0.67 | 0.67 | 1.00 | 1,003,614 | 365s | 1.000 / 0.800 / 1.000 |
| claude 2.1.220 | 0.9.0/0.1.0@188d0634d9f2 | sonnet | high | 3 | 0.697 | 1.00 | 0.25 | 0.98 | 0.67 | 0.00 | 0.00 | - | 900s | 0.700 / 0.700 / 0.692 |
| claude 2.1.220 | 0.9.0/0.1.0@1cd714991c83 | haiku | low | 3 | 0.253 | 1.00 | 0.25 | 0.36 | 0.00 | 0.00 | 0.00 | 36,462 | 534s | 0.133 / 0.133 / 0.492 |

`benchmark` is nurb/evals@content-revision and separates rows whenever the tool, task, scorer, harness adapter, or locked dependencies change. `score` averages all trials with gate failures as zeros; `built` is the fraction of trials past the gate, and lint/dims/flex average built trials only. A pass is a score of at least 0.99. Stage columns overlap by design: a part wrong at the stated size is wrong at every probed size too, so it loses dims and flex together. `tokens` is input plus output as the harness reports them, and harnesses count differently (claude's input excludes cache reads, codex counts full per-turn context), so compare tokens within a harness only.

## cable_clip (seed 13)

| harness | benchmark | model | effort | trials | score | built | lint | dims | flex | pass@1 | pass@3 | tokens | wall | trial scores |
|---|---|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| claude 2.1.220 | 0.9.0/0.1.0@f65057a28754 | fable | high | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 24,358 | 409s | 1.000 / 1.000 / 1.000 |
| claude 2.1.220 | 0.9.0/0.1.0@c00b02b82228 | opus | high | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 33,384 | 553s | 1.000 / 1.000 / 1.000 |
| claude 2.1.220 | 0.9.0/0.1.0@c00b02b82228 | sonnet | high | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 37,251 | 545s | 1.000 / 1.000 / 1.000 |
| codex 0.139.0 | 0.9.0/0.1.0@f65057a28754 | gpt-5.5 | medium | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 427,410 | 142s | 1.000 / 1.000 / 1.000 |
| claude 2.1.220 | 0.9.0/0.1.0@f65057a28754 | haiku | low | 3 | 0.667 | 0.67 | 1.00 | 1.00 | 1.00 | 0.67 | 1.00 | 33,125 | 470s | 1.000 / 1.000 / 0.000 |

`benchmark` is nurb/evals@content-revision and separates rows whenever the tool, task, scorer, harness adapter, or locked dependencies change. `score` averages all trials with gate failures as zeros; `built` is the fraction of trials past the gate, and lint/dims/flex average built trials only. A pass is a score of at least 0.99. Stage columns overlap by design: a part wrong at the stated size is wrong at every probed size too, so it loses dims and flex together. `tokens` is input plus output as the harness reports them, and harnesses count differently (claude's input excludes cache reads, codex counts full per-turn context), so compare tokens within a harness only.

## leg_cup (seed 13)

| harness | benchmark | model | effort | trials | score | built | lint | dims | flex | pass@1 | pass@3 | tokens | wall | trial scores |
|---|---|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| claude 2.1.220 | 0.9.0/0.1.0@c2f1130c6f0d | fable | high | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 12,852 | 211s | 1.000 / 1.000 / 1.000 |
| claude 2.1.220 | 0.9.0/0.1.0@6b1f4f029947 | opus | high | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 15,000 | 282s | 1.000 / 1.000 / 1.000 |
| claude 2.1.220 | 0.9.0/0.1.0@6b1f4f029947 | sonnet | high | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 21,302 | 298s | 1.000 / 1.000 / 1.000 |
| codex 0.139.0 | 0.9.0/0.1.0@6b1f4f029947 | gpt-5.5 | medium | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 357,312 | 110s | 1.000 / 1.000 / 1.000 |
| claude 2.1.220 | 0.9.0/0.1.0@6b1f4f029947 | haiku | low | 3 | 0.711 | 1.00 | 1.00 | 0.69 | 0.33 | 0.00 | 0.00 | 23,167 | 318s | 0.900 / 0.533 / 0.700 |

`benchmark` is nurb/evals@content-revision and separates rows whenever the tool, task, scorer, harness adapter, or locked dependencies change. `score` averages all trials with gate failures as zeros; `built` is the fraction of trials past the gate, and lint/dims/flex average built trials only. A pass is a score of at least 0.99. Stage columns overlap by design: a part wrong at the stated size is wrong at every probed size too, so it loses dims and flex together. `tokens` is input plus output as the harness reports them, and harnesses count differently (claude's input excludes cache reads, codex counts full per-turn context), so compare tokens within a harness only.

## Notes from these runs

- bundle_holder is a function task: it states the problem (a measured bundle, one M4 screw, a P1S) and grades functional gates on the B-rep plus a material gradient, never the shape. The models produced genuinely different designs.
- opus matches fable everywhere at about a third more wall time: it twice ran the 900s cap out on bundle_holder polishing and re-verifying a part that was already perfect on disk (a capped trial grades whatever the project holds, so both still scored 1.0).
- sonnet is the interesting row. Perfect on the spec task and the judgment task, and every one of its bundle_holder trials ran the full 900s (the killed harness reports no usage, hence the missing tokens). Its cradle designs genuinely hold the bundle and take the screw, and would genuinely fail on the printer: 50 degree unsupported overhangs under the tube, one wall at 0.86mm, one part whose center of mass falls outside its footprint. Function without print physics is exactly the failure this benchmark exists to price in.
- sonnet's row also caught a real scorer bug, disclosed here: its curved cradle cross-sections made the retention search's iterated polygon intersections compound vertices without bound (1.2 million on one part), grinding past the one-minute grading cap, and two trials were wrongly zeroed for grader slowness. Fixed by snapping section polygons to a micron grid, three orders below every scored tolerance; the 20-test fairness suite passes with exact reference scores, all nine previously committed bundle_holder parts re-grade identically, and sonnet's rows were re-graded under the same precedent as every earlier scorer fix: re-grade when only the grading was wrong, re-run when the instruction changed.
- codex's one 0.8 is a flex miss: its head-clearance slot design leaves under 100 mm2 of flat back face once the bundle grows 1mm, a real parametric flaw at exactly the stated minimum.
- leg_cup grades the refusal to guess: one dimension is deliberately unmeasured, the part has to track a rewritten measurements.toml, and the guess has to be recorded as provisional with provenance rather than baked into the code. fable, opus, sonnet, and gpt-5.5 all did it right in every trial, independently authored parts against honestly provisional entries. haiku is the cautionary row: all three trials wrote the number into measurements.toml with a plausible note and never marked it provisional, a guess dressed as a measurement, which is the exact failure the doctrine's provenance rule exists to prevent; one trial hardcoded the value in the part on top of it.
- haiku at low effort collapses on the function task (square "bore", sub-printable 0.5mm walls, blocked head paths) after scoring 1.000-when-it-built on the spec task. Execution is not the same ability as design.
- The fable rows on cable_clip and bundle_holder were first run before an earlier benchmark bug fix, and its 0.925s were the bug: it accepted its cosmetic sliver findings in the part's card exactly as the shipped doctrine teaches, and the card-ignoring grader still charged the WARN. Both instructions now state that the grader ignores card acceptances; told that, fable fixes the slivers in geometry and sweeps.
- Every task's scorer survived a dedicated adversarial pass only after hardening; all cheat geometries found live in the fairness suites as regressions, and the structural rules they produced (map the union of what the probes cover, cross-check recorded paperwork against built geometry, make every check continuous) are recorded in the project docs.
