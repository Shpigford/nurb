# Recorded under an alias, repaired on 2026-08-24

This run was submitted as `claude-fable-high-b523a2`, and its rows recorded `model = "fable"` with no resolved model ids. It ran a few days before the runner learned to capture `modelUsage`, so the CLI resolved the alias and nothing wrote down the answer. On the leaderboard that split one model across two rows, one labelled `fable` and one labelled `claude-fable-5`.

Both missing facts were recoverable from this run's own artifacts, so three fields were rewritten rather than left to fork the board.

| field | was | is | recovered from |
|---|---|---|---|
| `model` | `fable` | `claude-fable-5` | the transcripts |
| `usage.models` | absent | `["claude-fable-5", "claude-haiku-4-5-20251001"]` | the transcripts |
| `benchmark_revision` | see below | the current per-task revision | re-grading |

**The model id.** Every trial's `transcript.txt` carries the `modelUsage` map the runner reads today. Running the current `ClaudeCode.usage()` over the stored transcripts returns `["claude-fable-5", "claude-haiku-4-5-20251001"]` for all six, which is the same pair the later run records. Nothing here is inferred from the alias.

**The revision.** The rows were graded under `28728fea0e2f` (cable_clip), `e60a6422d46a` (bit_block), `4eb71d63bef3` (bundle_holder), `d2dc4e75efc7` (pole_rest), `2498e1db7385` (valve_knob), `ea00b7650ef5` (leg_cup). Only two inputs to that digest moved between those runs and this one: the `harness.py` change that added the `modelUsage` capture above, and a crash guard in `leg_cup/task.py` for an empty probe region. Neither touches a rubric. Re-grading all six parts under the current revisions reproduces every committed score and every stage exactly, the 0.675 on valve_knob included, so the restamped revision holds up under the check that field exists to support.

Scores, timings, token counts, transcripts, and part sources are untouched. To verify, drop each part into a project materialized from its task at seed 13, restore this run's `measurements.toml` for leg_cup, and grade.
