# nurb leaderboard

No rows yet: the benchmark was reset before its first deploy, so every published row will come from the released pipeline, run exactly as the instructions describe. Run one on your own subscription:

```
curl -fsSL https://nurb.dev/bench.sh | sh
```

See [README.md](README.md) for how rows work, the task classes, and how submissions pool. The rendered leaderboard lives at [nurb.dev/benchmarks](https://nurb.dev/benchmarks.html), generated from the committed submissions by `python -m nurb_evals.site`.
