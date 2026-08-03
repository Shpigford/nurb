# nurb leaderboard

Generated from the committed submissions by `python -m nurb_evals.report --write`, so it can never disagree with them; the reader-facing version is [nurb.dev/benchmarks](https://nurb.dev/benchmarks.html), built from the same rows. Matching rows pool across submissions, single runs included, and every row's transcripts and parts live under [submissions/](submissions/). See [README.md](README.md) to run one.

## bundle_holder (seed 13)

| harness | benchmark | model | effort | trials | score | built | lint | dims | flex | pass@1 | pass@3 | tokens | wall | trial scores |
|---|---|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| claude 2.1.220 | 0.10.0/0.1.0@f65a02da4de4 | haiku | low | 1 | 0.342 | 1.00 | 0.25 | 0.53 | 0.00 | 0.00 | 0.00 | 46,650 | 643s | 0.342 |

`benchmark` is nurb/evals@content-revision and separates rows whenever the tool, task, scorer, harness adapter, or locked dependencies change. `score` averages all trials with gate failures as zeros; `built` is the fraction of trials past the gate, and lint/dims/flex average built trials only. A pass is a score of at least 0.99. Stage columns overlap by design: a part wrong at the stated size is wrong at every probed size too, so it loses dims and flex together. `tokens` is input plus output as the harness reports them, and harnesses count differently (claude's input excludes cache reads, codex counts full per-turn context), so compare tokens within a harness only.

## cable_clip (seed 13)

| harness | benchmark | model | effort | trials | score | built | lint | dims | flex | pass@1 | pass@3 | tokens | wall | trial scores |
|---|---|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| claude 2.1.220 | 0.10.0/0.1.0@8b7526eb5988 | haiku | low | 1 | 0.578 | 1.00 | 1.00 | 0.56 | 0.00 | 0.00 | 0.00 | 24,622 | 286s | 0.578 |

`benchmark` is nurb/evals@content-revision and separates rows whenever the tool, task, scorer, harness adapter, or locked dependencies change. `score` averages all trials with gate failures as zeros; `built` is the fraction of trials past the gate, and lint/dims/flex average built trials only. A pass is a score of at least 0.99. Stage columns overlap by design: a part wrong at the stated size is wrong at every probed size too, so it loses dims and flex together. `tokens` is input plus output as the harness reports them, and harnesses count differently (claude's input excludes cache reads, codex counts full per-turn context), so compare tokens within a harness only.

## leg_cup (seed 13)

| harness | benchmark | model | effort | trials | score | built | lint | dims | flex | pass@1 | pass@3 | tokens | wall | trial scores |
|---|---|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| claude 2.1.220 | 0.10.0/0.1.0@8bc6d7c6cef1 | haiku | low | 1 | 0.825 | 1.00 | 0.75 | 0.80 | 1.00 | 0.00 | 0.00 | 18,456 | 220s | 0.825 |

`benchmark` is nurb/evals@content-revision and separates rows whenever the tool, task, scorer, harness adapter, or locked dependencies change. `score` averages all trials with gate failures as zeros; `built` is the fraction of trials past the gate, and lint/dims/flex average built trials only. A pass is a score of at least 0.99. Stage columns overlap by design: a part wrong at the stated size is wrong at every probed size too, so it loses dims and flex together. `tokens` is input plus output as the harness reports them, and harnesses count differently (claude's input excludes cache reads, codex counts full per-turn context), so compare tokens within a harness only.
