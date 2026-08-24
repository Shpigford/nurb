# nurb leaderboard

Generated from the committed submissions by `python -m nurb_evals.report --write`, so it can never disagree with them; the reader-facing version is [nurb.dev/benchmarks](https://nurb.dev/benchmarks.html), built from the same rows. Matching rows pool across submissions, single runs included, and every row's transcripts and parts live under [submissions/](submissions/). See [README.md](README.md) to run one.

## bit_block (seed 13)

| harness | benchmark | model | effort | trials | score | built | lint | dims | flex | pass@1 | pass@3 | tokens | cost | wall | trial scores |
|---|---|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| claude 2.1.241 | 0.22.2/0.1.0@e60a6422d46a | fable | high | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 11,067 | $2.04 | 224s | 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@e60a6422d46a | opus | low | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 4,055 | $0.59 | 176s | 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@e60a6422d46a | sonnet | high | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 20,562 | $0.80 | 401s | 1.000 / 1.000 / 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@e60a6422d46a | sonnet | low | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 6,546 | $0.38 | 243s | 1.000 / 1.000 / 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@e60a6422d46a | sonnet | medium | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 10,323 | $0.54 | 344s | 1.000 / 1.000 / 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@e60a6422d46a | sonnet | xhigh | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 22,823 | $0.76 | 443s | 1.000 / 1.000 / 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@e60a6422d46a | haiku | high | 3 | 0.806 | 1.00 | 1.00 | 0.83 | 0.44 | 0.33 | 1.00 | 30,793 | $0.49 | 488s | 0.867 / 0.550 / 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@e60a6422d46a | haiku | low | 3 | 0.639 | 1.00 | 1.00 | 0.63 | 0.11 | 0.00 | 0.00 | 21,255 | $0.39 | 391s | 0.500 / 0.867 / 0.550 |

`benchmark` is nurb/evals@content-revision and separates rows whenever the tool, task, scorer, harness adapter, or locked dependencies change. `score` averages all trials with gate failures as zeros; `built` is the fraction of trials past the gate, and lint/dims/flex average built trials only. A pass is a score of at least 0.99. Stage columns overlap by design: a part wrong at the stated size is wrong at every probed size too, so it loses dims and flex together. `tokens` is input plus output as the harness reports them, and harnesses count differently (claude's input excludes cache reads, codex counts full per-turn context), so compare tokens within a harness only. `cost` is the API-equivalent dollar cost of a trial at list prices, the mean across trials: subscription runs paid no invoice, so this is what the same tokens would have cost through the API. claude rows carry the CLI's own cache-aware figure; other harnesses derive from their token counts and the dated prices.toml, which folds any cached tokens in at the full input rate and so reads slightly high.

## bundle_holder (seed 13)

| harness | benchmark | model | effort | trials | score | built | lint | dims | flex | pass@1 | pass@3 | tokens | cost | wall | trial scores |
|---|---|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| claude 2.1.241 | 0.22.2/0.1.0@4eb71d63bef3 | fable | high | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 31,786 | $3.92 | 528s | 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@4eb71d63bef3 | opus | low | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 15,799 | $1.20 | 333s | 1.000 |
| claude 2.1.220 | 0.10.0/0.1.0@f65a02da4de4 | sonnet | medium | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 213,727 | $8.46 | 3058s | 1.000 |
| claude 2.1.220 | 0.10.0/0.1.0@f65a02da4de4 | sonnet | xhigh | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 209,853 | $7.38 | 2527s | 1.000 |
| grok 1.0.4 | 0.19.2/0.1.0@9620846dd1cf | grok-4.6 | high | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 217,583 | $0.32 | 869s | 1.000 |
| claude 2.1.220 | 0.10.0/0.1.0@f65a02da4de4 | sonnet | high | 1 | 0.967 | 1.00 | 1.00 | 0.93 | 1.00 | 0.00 | 0.00 | 162,188 | $8.05 | 2353s | 0.967 |
| claude 2.1.220 | 0.10.0/0.1.0@f65a02da4de4 | sonnet | low | 1 | 0.567 | 1.00 | 1.00 | 0.53 | 0.00 | 0.00 | 0.00 | 53,090 | $2.09 | 722s | 0.567 |
| claude 2.1.220 | 0.10.0/0.1.0@f65a02da4de4 | haiku | high | 1 | 0.467 | 1.00 | 1.00 | 0.33 | 0.00 | 0.00 | 0.00 | 23,169 | $0.36 | 345s | 0.467 |
| claude 2.1.220 | 0.10.0/0.1.0@f65a02da4de4 | haiku | low | 2 | 0.429 | 1.00 | 0.88 | 0.33 | 0.00 | 0.00 | 0.00 | 34,398 | $0.53 | 498s | 0.467 / 0.392 |

`benchmark` is nurb/evals@content-revision and separates rows whenever the tool, task, scorer, harness adapter, or locked dependencies change. `score` averages all trials with gate failures as zeros; `built` is the fraction of trials past the gate, and lint/dims/flex average built trials only. A pass is a score of at least 0.99. Stage columns overlap by design: a part wrong at the stated size is wrong at every probed size too, so it loses dims and flex together. `tokens` is input plus output as the harness reports them, and harnesses count differently (claude's input excludes cache reads, codex counts full per-turn context), so compare tokens within a harness only. `cost` is the API-equivalent dollar cost of a trial at list prices, the mean across trials: subscription runs paid no invoice, so this is what the same tokens would have cost through the API. claude rows carry the CLI's own cache-aware figure; other harnesses derive from their token counts and the dated prices.toml, which folds any cached tokens in at the full input rate and so reads slightly high.

## cable_clip (seed 13)

| harness | benchmark | model | effort | trials | score | built | lint | dims | flex | pass@1 | pass@3 | tokens | cost | wall | trial scores |
|---|---|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| claude 2.1.241 | 0.22.2/0.1.0@28728fea0e2f | fable | high | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 24,329 | $3.61 | 433s | 1.000 |
| claude 2.1.220 | 0.10.0/0.1.0@8b7526eb5988 | haiku | high | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 20,340 | $0.33 | 315s | 1.000 |
| claude 2.1.220 | 0.10.0/0.1.0@8b7526eb5988 | haiku | low | 2 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 40,432 | $0.57 | 550s | 1.000 / 1.000 |
| claude 2.1.220 | 0.10.0/0.1.0@8b7526eb5988 | sonnet | high | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 18,426 | $1.02 | 292s | 1.000 |
| claude 2.1.220 | 0.10.0/0.1.0@8b7526eb5988 | sonnet | low | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 12,388 | $0.66 | 175s | 1.000 |
| claude 2.1.220 | 0.10.0/0.1.0@8b7526eb5988 | sonnet | xhigh | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 80,874 | $3.76 | 1038s | 1.000 |
| grok 1.0.4 | 0.19.2/0.1.0@62d2e9d68448 | grok-4.6 | high | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 201,616 | $0.17 | 622s | 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@28728fea0e2f | opus | low | 1 | 0.745 | 1.00 | 1.00 | 0.89 | 0.00 | 0.00 | 0.00 | 7,054 | $1.08 | 288s | 0.745 |
| claude 2.1.220 | 0.10.0/0.1.0@8b7526eb5988 | sonnet | medium | 1 | 0.745 | 1.00 | 1.00 | 0.89 | 0.00 | 0.00 | 0.00 | 29,937 | $1.54 | 452s | 0.745 |

`benchmark` is nurb/evals@content-revision and separates rows whenever the tool, task, scorer, harness adapter, or locked dependencies change. `score` averages all trials with gate failures as zeros; `built` is the fraction of trials past the gate, and lint/dims/flex average built trials only. A pass is a score of at least 0.99. Stage columns overlap by design: a part wrong at the stated size is wrong at every probed size too, so it loses dims and flex together. `tokens` is input plus output as the harness reports them, and harnesses count differently (claude's input excludes cache reads, codex counts full per-turn context), so compare tokens within a harness only. `cost` is the API-equivalent dollar cost of a trial at list prices, the mean across trials: subscription runs paid no invoice, so this is what the same tokens would have cost through the API. claude rows carry the CLI's own cache-aware figure; other harnesses derive from their token counts and the dated prices.toml, which folds any cached tokens in at the full input rate and so reads slightly high.

## leg_cup (seed 13)

| harness | benchmark | model | effort | trials | score | built | lint | dims | flex | pass@1 | pass@3 | tokens | cost | wall | trial scores |
|---|---|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| claude 2.1.241 | 0.22.2/0.1.0@ea00b7650ef5 | fable | high | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 11,724 | $2.42 | 238s | 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@ea00b7650ef5 | opus | low | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 4,311 | $0.68 | 169s | 1.000 |
| claude 2.1.220 | 0.10.0/0.1.0@8bc6d7c6cef1 | sonnet | high | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 10,337 | $0.83 | 181s | 1.000 |
| claude 2.1.220 | 0.10.0/0.1.0@8bc6d7c6cef1 | sonnet | low | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 4,310 | $0.41 | 92s | 1.000 |
| claude 2.1.220 | 0.10.0/0.1.0@8bc6d7c6cef1 | sonnet | medium | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 6,872 | $0.55 | 124s | 1.000 |
| claude 2.1.220 | 0.10.0/0.1.0@8bc6d7c6cef1 | sonnet | xhigh | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 35,209 | $1.85 | 461s | 1.000 |
| grok 1.0.4 | 0.19.2/0.1.0@7ef9696be198 | grok-4.6 | high | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 59,350 | $0.06 | 266s | 1.000 |
| claude 2.1.220 | 0.10.0/0.1.0@8bc6d7c6cef1 | haiku | low | 2 | 0.950 | 1.00 | 1.00 | 1.00 | 0.75 | 0.50 | 1.00 | 10,871 | $0.17 | 150s | 1.000 / 0.900 |
| claude 2.1.220 | 0.10.0/0.1.0@8bc6d7c6cef1 | haiku | high | 1 | 0.500 | 1.00 | 1.00 | 0.40 | 0.00 | 0.00 | 0.00 | 20,562 | $0.24 | 251s | 0.500 |

`benchmark` is nurb/evals@content-revision and separates rows whenever the tool, task, scorer, harness adapter, or locked dependencies change. `score` averages all trials with gate failures as zeros; `built` is the fraction of trials past the gate, and lint/dims/flex average built trials only. A pass is a score of at least 0.99. Stage columns overlap by design: a part wrong at the stated size is wrong at every probed size too, so it loses dims and flex together. `tokens` is input plus output as the harness reports them, and harnesses count differently (claude's input excludes cache reads, codex counts full per-turn context), so compare tokens within a harness only. `cost` is the API-equivalent dollar cost of a trial at list prices, the mean across trials: subscription runs paid no invoice, so this is what the same tokens would have cost through the API. claude rows carry the CLI's own cache-aware figure; other harnesses derive from their token counts and the dated prices.toml, which folds any cached tokens in at the full input rate and so reads slightly high.

## pole_rest (seed 13)

| harness | benchmark | model | effort | trials | score | built | lint | dims | flex | pass@1 | pass@3 | tokens | cost | wall | trial scores |
|---|---|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| claude 2.1.241 | 0.22.2/0.1.0@d2dc4e75efc7 | fable | high | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 23,567 | $3.28 | 406s | 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@d2dc4e75efc7 | opus | low | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 10,794 | $0.95 | 276s | 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@d2dc4e75efc7 | sonnet | high | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 41,414 | $1.15 | 612s | 1.000 / 1.000 / 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@d2dc4e75efc7 | sonnet | medium | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 27,033 | $0.86 | 446s | 1.000 / 1.000 / 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@d2dc4e75efc7 | sonnet | xhigh | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 66,578 | $1.95 | 926s | 1.000 / 1.000 / 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@d2dc4e75efc7 | sonnet | low | 3 | 0.831 | 1.00 | 1.00 | 0.79 | 0.67 | 0.67 | 1.00 | 31,597 | $1.02 | 541s | 0.492 / 1.000 / 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@d2dc4e75efc7 | haiku | high | 3 | 0.467 | 1.00 | 1.00 | 0.33 | 0.00 | 0.00 | 0.00 | 44,091 | $0.70 | 722s | 0.492 / 0.492 / 0.415 |
| claude 2.1.241 | 0.22.2/0.1.0@d2dc4e75efc7 | haiku | low | 3 | 0.454 | 1.00 | 0.92 | 0.36 | 0.00 | 0.00 | 0.00 | 32,209 | $0.52 | 513s | 0.417 / 0.492 / 0.454 |

`benchmark` is nurb/evals@content-revision and separates rows whenever the tool, task, scorer, harness adapter, or locked dependencies change. `score` averages all trials with gate failures as zeros; `built` is the fraction of trials past the gate, and lint/dims/flex average built trials only. A pass is a score of at least 0.99. Stage columns overlap by design: a part wrong at the stated size is wrong at every probed size too, so it loses dims and flex together. `tokens` is input plus output as the harness reports them, and harnesses count differently (claude's input excludes cache reads, codex counts full per-turn context), so compare tokens within a harness only. `cost` is the API-equivalent dollar cost of a trial at list prices, the mean across trials: subscription runs paid no invoice, so this is what the same tokens would have cost through the API. claude rows carry the CLI's own cache-aware figure; other harnesses derive from their token counts and the dated prices.toml, which folds any cached tokens in at the full input rate and so reads slightly high.

## valve_knob (seed 13)

| harness | benchmark | model | effort | trials | score | built | lint | dims | flex | pass@1 | pass@3 | tokens | cost | wall | trial scores |
|---|---|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| claude 2.1.241 | 0.22.2/0.1.0@2498e1db7385 | opus | low | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 7,526 | $0.80 | 272s | 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@2498e1db7385 | sonnet | high | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 49,643 | $1.28 | 681s | 1.000 / 1.000 / 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@2498e1db7385 | sonnet | medium | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 23,735 | $0.67 | 373s | 1.000 / 1.000 / 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@2498e1db7385 | sonnet | xhigh | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 61,697 | $1.67 | 867s | 1.000 / 1.000 / 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@2498e1db7385 | sonnet | low | 3 | 0.892 | 1.00 | 1.00 | 0.92 | 0.67 | 0.67 | 1.00 | 14,922 | $0.46 | 258s | 1.000 / 1.000 / 0.675 |
| claude 2.1.241 | 0.22.2/0.1.0@2498e1db7385 | fable | high | 1 | 0.675 | 1.00 | 1.00 | 0.75 | 0.00 | 0.00 | 0.00 | 20,867 | $3.05 | 356s | 0.675 |
| claude 2.1.241 | 0.22.2/0.1.0@2498e1db7385 | haiku | low | 3 | 0.565 | 1.00 | 0.67 | 0.73 | 0.00 | 0.00 | 0.00 | 24,496 | $0.37 | 371s | 0.644 / 0.406 / 0.644 |
| claude 2.1.241 | 0.22.2/0.1.0@2498e1db7385 | haiku | high | 3 | 0.494 | 1.00 | 0.50 | 0.69 | 0.00 | 0.00 | 0.00 | 38,825 | $0.65 | 583s | 0.494 / 0.644 / 0.344 |

`benchmark` is nurb/evals@content-revision and separates rows whenever the tool, task, scorer, harness adapter, or locked dependencies change. `score` averages all trials with gate failures as zeros; `built` is the fraction of trials past the gate, and lint/dims/flex average built trials only. A pass is a score of at least 0.99. Stage columns overlap by design: a part wrong at the stated size is wrong at every probed size too, so it loses dims and flex together. `tokens` is input plus output as the harness reports them, and harnesses count differently (claude's input excludes cache reads, codex counts full per-turn context), so compare tokens within a harness only. `cost` is the API-equivalent dollar cost of a trial at list prices, the mean across trials: subscription runs paid no invoice, so this is what the same tokens would have cost through the API. claude rows carry the CLI's own cache-aware figure; other harnesses derive from their token counts and the dated prices.toml, which folds any cached tokens in at the full input rate and so reads slightly high.
