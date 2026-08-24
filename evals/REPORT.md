# nurb leaderboard

Generated from the committed submissions by `python -m nurb_evals.report --write`, so it can never disagree with them; the reader-facing version is [nurb.dev/benchmarks](https://nurb.dev/benchmarks.html), built from the same rows. Matching rows pool across submissions, single runs included, and every row's transcripts and parts live under [submissions/](submissions/). See [README.md](README.md) to run one.

## bit_block (seed 13)

| harness | benchmark | model | effort | trials | score | built | lint | dims | flex | pass@1 | pass@3 | tokens | cost | wall | trial scores |
|---|---|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| claude 2.1.241 | 0.22.2/0.1.0@e8f4e93e23fd | claude-fable-5 | high | 4 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 9,028 | $1.92 | 219s | 1.000 / 1.000 / 1.000 / 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@e60a6422d46a | claude-opus-5 | low | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 4,055 | $0.59 | 176s | 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@e60a6422d46a | claude-sonnet-5 | high | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 20,562 | $0.80 | 401s | 1.000 / 1.000 / 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@e60a6422d46a | claude-sonnet-5 | low | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 6,546 | $0.38 | 243s | 1.000 / 1.000 / 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@e60a6422d46a | claude-sonnet-5 | medium | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 10,323 | $0.54 | 344s | 1.000 / 1.000 / 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@e60a6422d46a | claude-sonnet-5 | xhigh | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 22,823 | $0.76 | 443s | 1.000 / 1.000 / 1.000 |
| grok 1.0.5 | 0.22.2/0.1.0@e8f4e93e23fd | grok-4.6 | low | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 72,679 | $0.06 | 109s | 1.000 / 1.000 / 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@e60a6422d46a | claude-haiku-4-5-20251001 | high | 3 | 0.806 | 1.00 | 1.00 | 0.83 | 0.44 | 0.33 | 1.00 | 30,793 | $0.49 | 488s | 0.867 / 0.550 / 1.000 |
| codex 0.149.1 | 0.22.2/0.1.0@e8f4e93e23fd | gpt-5.6-terra | low | 3 | 0.775 | 1.00 | 0.92 | 0.87 | 0.33 | 0.33 | 1.00 | 399,731 | $0.84 | 131s | 0.625 / 1.000 / 0.700 |
| codex 0.149.1 | 0.22.2/0.1.0@e8f4e93e23fd | gpt-5.6-luna | low | 3 | 0.681 | 1.00 | 0.92 | 0.77 | 0.11 | 0.00 | 0.00 | 365,642 | $0.08 | 150s | 0.500 / 0.867 / 0.675 |
| claude 2.1.241 | 0.22.2/0.1.0@e60a6422d46a | claude-haiku-4-5-20251001 | low | 3 | 0.639 | 1.00 | 1.00 | 0.63 | 0.11 | 0.00 | 0.00 | 21,255 | $0.39 | 391s | 0.500 / 0.867 / 0.550 |

`benchmark` is nurb/evals@content-revision and separates rows whenever the tool, task, scorer, harness adapter, or locked dependencies change. `score` averages all trials with gate failures as zeros; `built` is the fraction of trials past the gate, and lint/dims/flex average built trials only. A pass is a score of at least 0.99. Stage columns overlap by design: a part wrong at the stated size is wrong at every probed size too, so it loses dims and flex together. `tokens` is input plus output as the harness reports them, and harnesses count differently (claude's input excludes cache reads, codex counts full per-turn context), so compare tokens within a harness only. `cost` is the API-equivalent dollar cost of a trial at list prices, the mean across trials: subscription runs paid no invoice, so this is what the same tokens would have cost through the API. claude rows carry the CLI's own cache-aware figure; other harnesses derive from their token counts and the dated prices.toml, which folds any cached tokens in at the full input rate and so reads slightly high.

## bundle_holder (seed 13)

| harness | benchmark | model | effort | trials | score | built | lint | dims | flex | pass@1 | pass@3 | tokens | cost | wall | trial scores |
|---|---|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| claude 2.1.241 | 0.22.2/0.1.0@c16e77e91b9a | claude-fable-5 | high | 4 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 36,715 | $4.84 | 652s | 1.000 / 1.000 / 1.000 / 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@4eb71d63bef3 | claude-opus-5 | low | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 15,799 | $1.20 | 333s | 1.000 |
| claude 2.1.220 | 0.10.0/0.1.0@f65a02da4de4 | claude-sonnet-5 | medium | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 213,727 | $8.46 | 3058s | 1.000 |
| claude 2.1.220 | 0.10.0/0.1.0@f65a02da4de4 | claude-sonnet-5 | xhigh | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 209,853 | $7.38 | 2527s | 1.000 |
| grok 1.0.4 | 0.19.2/0.1.0@9620846dd1cf | grok-4.6 | high | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 217,583 | $0.32 | 869s | 1.000 |
| claude 2.1.220 | 0.10.0/0.1.0@f65a02da4de4 | claude-sonnet-5 | high | 1 | 0.967 | 1.00 | 1.00 | 0.93 | 1.00 | 0.00 | 0.00 | 162,188 | $8.05 | 2353s | 0.967 |
| grok 1.0.5 | 0.22.2/0.1.0@c16e77e91b9a | grok-4.6 | low | 3 | 0.867 | 1.00 | 1.00 | 0.87 | 0.67 | 0.67 | 1.00 | 118,602 | $0.10 | 197s | 0.600 / 1.000 / 1.000 |
| codex 0.149.1 | 0.22.2/0.1.0@c16e77e91b9a | gpt-5.6-terra | low | 3 | 0.678 | 1.00 | 1.00 | 0.76 | 0.00 | 0.00 | 0.00 | 393,177 | $0.86 | 189s | 0.667 / 0.767 / 0.600 |
| codex 0.149.1 | 0.22.2/0.1.0@c16e77e91b9a | gpt-5.6-luna | low | 3 | 0.633 | 1.00 | 1.00 | 0.67 | 0.00 | 0.00 | 0.00 | 437,067 | $0.09 | 210s | 0.667 / 0.700 / 0.533 |
| claude 2.1.220 | 0.10.0/0.1.0@f65a02da4de4 | claude-sonnet-5 | low | 1 | 0.567 | 1.00 | 1.00 | 0.53 | 0.00 | 0.00 | 0.00 | 53,090 | $2.09 | 722s | 0.567 |
| claude 2.1.220 | 0.10.0/0.1.0@f65a02da4de4 | claude-haiku-4-5-20251001 | high | 1 | 0.467 | 1.00 | 1.00 | 0.33 | 0.00 | 0.00 | 0.00 | 23,169 | $0.36 | 345s | 0.467 |
| claude 2.1.220 | 0.10.0/0.1.0@f65a02da4de4 | claude-haiku-4-5-20251001 | low | 2 | 0.429 | 1.00 | 0.88 | 0.33 | 0.00 | 0.00 | 0.00 | 34,398 | $0.53 | 498s | 0.467 / 0.392 |

`benchmark` is nurb/evals@content-revision and separates rows whenever the tool, task, scorer, harness adapter, or locked dependencies change. `score` averages all trials with gate failures as zeros; `built` is the fraction of trials past the gate, and lint/dims/flex average built trials only. A pass is a score of at least 0.99. Stage columns overlap by design: a part wrong at the stated size is wrong at every probed size too, so it loses dims and flex together. `tokens` is input plus output as the harness reports them, and harnesses count differently (claude's input excludes cache reads, codex counts full per-turn context), so compare tokens within a harness only. `cost` is the API-equivalent dollar cost of a trial at list prices, the mean across trials: subscription runs paid no invoice, so this is what the same tokens would have cost through the API. claude rows carry the CLI's own cache-aware figure; other harnesses derive from their token counts and the dated prices.toml, which folds any cached tokens in at the full input rate and so reads slightly high.

## cable_clip (seed 13)

| harness | benchmark | model | effort | trials | score | built | lint | dims | flex | pass@1 | pass@3 | tokens | cost | wall | trial scores |
|---|---|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| claude 2.1.241 | 0.22.2/0.1.0@13435a35f451 | claude-fable-5 | high | 4 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 22,612 | $3.36 | 421s | 1.000 / 1.000 / 1.000 / 1.000 |
| claude 2.1.220 | 0.10.0/0.1.0@8b7526eb5988 | claude-haiku-4-5-20251001 | high | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 20,340 | $0.33 | 315s | 1.000 |
| claude 2.1.220 | 0.10.0/0.1.0@8b7526eb5988 | claude-haiku-4-5-20251001 | low | 2 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 40,432 | $0.57 | 550s | 1.000 / 1.000 |
| claude 2.1.220 | 0.10.0/0.1.0@8b7526eb5988 | claude-sonnet-5 | high | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 18,426 | $1.02 | 292s | 1.000 |
| claude 2.1.220 | 0.10.0/0.1.0@8b7526eb5988 | claude-sonnet-5 | low | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 12,388 | $0.66 | 175s | 1.000 |
| claude 2.1.220 | 0.10.0/0.1.0@8b7526eb5988 | claude-sonnet-5 | xhigh | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 80,874 | $3.76 | 1038s | 1.000 |
| codex 0.149.1 | 0.22.2/0.1.0@13435a35f451 | gpt-5.6-terra | low | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 188,882 | $0.41 | 77s | 1.000 / 1.000 / 1.000 |
| grok 1.0.4 | 0.19.2/0.1.0@62d2e9d68448 | grok-4.6 | high | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 201,616 | $0.17 | 622s | 1.000 |
| grok 1.0.5 | 0.22.2/0.1.0@13435a35f451 | grok-4.6 | low | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 105,605 | $0.07 | 100s | 1.000 / 1.000 / 1.000 |
| codex 0.149.1 | 0.22.2/0.1.0@13435a35f451 | gpt-5.6-luna | low | 3 | 0.915 | 1.00 | 1.00 | 0.96 | 0.67 | 0.67 | 1.00 | 209,886 | $0.04 | 96s | 1.000 / 0.745 / 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@28728fea0e2f | claude-opus-5 | low | 1 | 0.745 | 1.00 | 1.00 | 0.89 | 0.00 | 0.00 | 0.00 | 7,054 | $1.08 | 288s | 0.745 |
| claude 2.1.220 | 0.10.0/0.1.0@8b7526eb5988 | claude-sonnet-5 | medium | 1 | 0.745 | 1.00 | 1.00 | 0.89 | 0.00 | 0.00 | 0.00 | 29,937 | $1.54 | 452s | 0.745 |

`benchmark` is nurb/evals@content-revision and separates rows whenever the tool, task, scorer, harness adapter, or locked dependencies change. `score` averages all trials with gate failures as zeros; `built` is the fraction of trials past the gate, and lint/dims/flex average built trials only. A pass is a score of at least 0.99. Stage columns overlap by design: a part wrong at the stated size is wrong at every probed size too, so it loses dims and flex together. `tokens` is input plus output as the harness reports them, and harnesses count differently (claude's input excludes cache reads, codex counts full per-turn context), so compare tokens within a harness only. `cost` is the API-equivalent dollar cost of a trial at list prices, the mean across trials: subscription runs paid no invoice, so this is what the same tokens would have cost through the API. claude rows carry the CLI's own cache-aware figure; other harnesses derive from their token counts and the dated prices.toml, which folds any cached tokens in at the full input rate and so reads slightly high.

## leg_cup (seed 13)

| harness | benchmark | model | effort | trials | score | built | lint | dims | flex | pass@1 | pass@3 | tokens | cost | wall | trial scores |
|---|---|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| claude 2.1.241 | 0.22.2/0.1.0@cb94fa2b8578 | claude-fable-5 | high | 4 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 14,404 | $2.49 | 309s | 1.000 / 1.000 / 1.000 / 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@ea00b7650ef5 | claude-opus-5 | low | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 4,311 | $0.68 | 169s | 1.000 |
| claude 2.1.220 | 0.10.0/0.1.0@8bc6d7c6cef1 | claude-sonnet-5 | high | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 10,337 | $0.83 | 181s | 1.000 |
| claude 2.1.220 | 0.10.0/0.1.0@8bc6d7c6cef1 | claude-sonnet-5 | low | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 4,310 | $0.41 | 92s | 1.000 |
| claude 2.1.220 | 0.10.0/0.1.0@8bc6d7c6cef1 | claude-sonnet-5 | medium | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 6,872 | $0.55 | 124s | 1.000 |
| claude 2.1.220 | 0.10.0/0.1.0@8bc6d7c6cef1 | claude-sonnet-5 | xhigh | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 35,209 | $1.85 | 461s | 1.000 |
| grok 1.0.4 | 0.19.2/0.1.0@7ef9696be198 | grok-4.6 | high | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 59,350 | $0.06 | 266s | 1.000 |
| grok 1.0.5 | 0.22.2/0.1.0@cb94fa2b8578 | grok-4.6 | low | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 72,660 | $0.05 | 86s | 1.000 / 1.000 / 1.000 |
| claude 2.1.220 | 0.10.0/0.1.0@8bc6d7c6cef1 | claude-haiku-4-5-20251001 | low | 2 | 0.950 | 1.00 | 1.00 | 1.00 | 0.75 | 0.50 | 1.00 | 10,871 | $0.17 | 150s | 1.000 / 0.900 |
| codex 0.149.1 | 0.22.2/0.1.0@cb94fa2b8578 | gpt-5.6-terra | low | 3 | 0.878 | 1.00 | 1.00 | 0.89 | 0.67 | 0.67 | 1.00 | 283,117 | $0.60 | 94s | 1.000 / 1.000 / 0.633 |
| codex 0.149.1 | 0.22.2/0.1.0@cb94fa2b8578 | gpt-5.6-luna | low | 3 | 0.844 | 1.00 | 1.00 | 0.82 | 0.67 | 0.67 | 1.00 | 255,368 | $0.05 | 91s | 1.000 / 0.533 / 1.000 |
| claude 2.1.220 | 0.10.0/0.1.0@8bc6d7c6cef1 | claude-haiku-4-5-20251001 | high | 1 | 0.500 | 1.00 | 1.00 | 0.40 | 0.00 | 0.00 | 0.00 | 20,562 | $0.24 | 251s | 0.500 |

`benchmark` is nurb/evals@content-revision and separates rows whenever the tool, task, scorer, harness adapter, or locked dependencies change. `score` averages all trials with gate failures as zeros; `built` is the fraction of trials past the gate, and lint/dims/flex average built trials only. A pass is a score of at least 0.99. Stage columns overlap by design: a part wrong at the stated size is wrong at every probed size too, so it loses dims and flex together. `tokens` is input plus output as the harness reports them, and harnesses count differently (claude's input excludes cache reads, codex counts full per-turn context), so compare tokens within a harness only. `cost` is the API-equivalent dollar cost of a trial at list prices, the mean across trials: subscription runs paid no invoice, so this is what the same tokens would have cost through the API. claude rows carry the CLI's own cache-aware figure; other harnesses derive from their token counts and the dated prices.toml, which folds any cached tokens in at the full input rate and so reads slightly high.

## pole_rest (seed 13)

| harness | benchmark | model | effort | trials | score | built | lint | dims | flex | pass@1 | pass@3 | tokens | cost | wall | trial scores |
|---|---|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| claude 2.1.241 | 0.22.2/0.1.0@de974b4cb0c3 | claude-fable-5 | high | 4 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 24,900 | $3.37 | 442s | 1.000 / 1.000 / 1.000 / 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@d2dc4e75efc7 | claude-opus-5 | low | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 10,794 | $0.95 | 276s | 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@d2dc4e75efc7 | claude-sonnet-5 | high | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 41,414 | $1.15 | 612s | 1.000 / 1.000 / 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@d2dc4e75efc7 | claude-sonnet-5 | medium | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 27,033 | $0.86 | 446s | 1.000 / 1.000 / 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@d2dc4e75efc7 | claude-sonnet-5 | xhigh | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 66,578 | $1.95 | 926s | 1.000 / 1.000 / 1.000 |
| grok 1.0.5 | 0.22.2/0.1.0@de974b4cb0c3 | grok-4.6 | low | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 133,061 | $0.08 | 153s | 1.000 / 1.000 / 1.000 |
| codex 0.149.1 | 0.22.2/0.1.0@de974b4cb0c3 | gpt-5.6-terra | low | 3 | 0.856 | 1.00 | 1.00 | 0.85 | 0.67 | 0.67 | 1.00 | 430,455 | $0.93 | 208s | 0.569 / 1.000 / 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@d2dc4e75efc7 | claude-sonnet-5 | low | 3 | 0.831 | 1.00 | 1.00 | 0.79 | 0.67 | 0.67 | 1.00 | 31,597 | $1.02 | 541s | 0.492 / 1.000 / 1.000 |
| codex 0.149.1 | 0.22.2/0.1.0@de974b4cb0c3 | gpt-5.6-luna | low | 3 | 0.628 | 1.00 | 1.00 | 0.59 | 0.17 | 0.00 | 0.00 | 647,325 | $0.14 | 251s | 0.492 / 0.492 / 0.900 |
| claude 2.1.241 | 0.22.2/0.1.0@d2dc4e75efc7 | claude-haiku-4-5-20251001 | high | 3 | 0.467 | 1.00 | 1.00 | 0.33 | 0.00 | 0.00 | 0.00 | 44,091 | $0.70 | 722s | 0.492 / 0.492 / 0.415 |
| claude 2.1.241 | 0.22.2/0.1.0@d2dc4e75efc7 | claude-haiku-4-5-20251001 | low | 3 | 0.454 | 1.00 | 0.92 | 0.36 | 0.00 | 0.00 | 0.00 | 32,209 | $0.52 | 513s | 0.417 / 0.492 / 0.454 |

`benchmark` is nurb/evals@content-revision and separates rows whenever the tool, task, scorer, harness adapter, or locked dependencies change. `score` averages all trials with gate failures as zeros; `built` is the fraction of trials past the gate, and lint/dims/flex average built trials only. A pass is a score of at least 0.99. Stage columns overlap by design: a part wrong at the stated size is wrong at every probed size too, so it loses dims and flex together. `tokens` is input plus output as the harness reports them, and harnesses count differently (claude's input excludes cache reads, codex counts full per-turn context), so compare tokens within a harness only. `cost` is the API-equivalent dollar cost of a trial at list prices, the mean across trials: subscription runs paid no invoice, so this is what the same tokens would have cost through the API. claude rows carry the CLI's own cache-aware figure; other harnesses derive from their token counts and the dated prices.toml, which folds any cached tokens in at the full input rate and so reads slightly high.

## valve_knob (seed 13)

| harness | benchmark | model | effort | trials | score | built | lint | dims | flex | pass@1 | pass@3 | tokens | cost | wall | trial scores |
|---|---|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| claude 2.1.241 | 0.22.2/0.1.0@2498e1db7385 | claude-opus-5 | low | 1 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 7,526 | $0.80 | 272s | 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@2498e1db7385 | claude-sonnet-5 | high | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 49,643 | $1.28 | 681s | 1.000 / 1.000 / 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@2498e1db7385 | claude-sonnet-5 | medium | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 23,735 | $0.67 | 373s | 1.000 / 1.000 / 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@2498e1db7385 | claude-sonnet-5 | xhigh | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 61,697 | $1.67 | 867s | 1.000 / 1.000 / 1.000 |
| grok 1.0.5 | 0.22.2/0.1.0@64ee1d278c28 | grok-4.6 | low | 3 | 1.000 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 115,425 | $0.08 | 167s | 1.000 / 1.000 / 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@64ee1d278c28 | claude-fable-5 | high | 4 | 0.919 | 1.00 | 1.00 | 0.94 | 0.75 | 0.75 | 1.00 | 23,188 | $3.23 | 421s | 0.675 / 1.000 / 1.000 / 1.000 |
| claude 2.1.241 | 0.22.2/0.1.0@2498e1db7385 | claude-sonnet-5 | low | 3 | 0.892 | 1.00 | 1.00 | 0.92 | 0.67 | 0.67 | 1.00 | 14,922 | $0.46 | 258s | 1.000 / 1.000 / 0.675 |
| codex 0.149.1 | 0.22.2/0.1.0@64ee1d278c28 | gpt-5.6-terra | low | 3 | 0.892 | 1.00 | 1.00 | 0.92 | 0.67 | 0.67 | 1.00 | 369,360 | $0.78 | 140s | 1.000 / 0.675 / 1.000 |
| codex 0.149.1 | 0.22.2/0.1.0@64ee1d278c28 | gpt-5.6-luna | low | 3 | 0.804 | 1.00 | 1.00 | 0.88 | 0.33 | 0.33 | 1.00 | 284,379 | $0.06 | 102s | 1.000 / 0.706 / 0.706 |
| claude 2.1.241 | 0.22.2/0.1.0@2498e1db7385 | claude-haiku-4-5-20251001 | low | 3 | 0.565 | 1.00 | 0.67 | 0.73 | 0.00 | 0.00 | 0.00 | 24,496 | $0.37 | 371s | 0.644 / 0.406 / 0.644 |
| claude 2.1.241 | 0.22.2/0.1.0@2498e1db7385 | claude-haiku-4-5-20251001 | high | 3 | 0.494 | 1.00 | 0.50 | 0.69 | 0.00 | 0.00 | 0.00 | 38,825 | $0.65 | 583s | 0.494 / 0.644 / 0.344 |

`benchmark` is nurb/evals@content-revision and separates rows whenever the tool, task, scorer, harness adapter, or locked dependencies change. `score` averages all trials with gate failures as zeros; `built` is the fraction of trials past the gate, and lint/dims/flex average built trials only. A pass is a score of at least 0.99. Stage columns overlap by design: a part wrong at the stated size is wrong at every probed size too, so it loses dims and flex together. `tokens` is input plus output as the harness reports them, and harnesses count differently (claude's input excludes cache reads, codex counts full per-turn context), so compare tokens within a harness only. `cost` is the API-equivalent dollar cost of a trial at list prices, the mean across trials: subscription runs paid no invoice, so this is what the same tokens would have cost through the API. claude rows carry the CLI's own cache-aware figure; other harnesses derive from their token counts and the dated prices.toml, which folds any cached tokens in at the full input rate and so reads slightly high.
