# Aliases replaced with resolved model ids, 2026-08-24

Fifteen runs recorded a floating model name (`fable`, `sonnet`, `haiku`, `opus`) instead of a pinned id, because they ran before the `harness.py` change that captures `modelUsage`. The alias was whatever the contributor typed, and nothing wrote down which model answered. Rows pool on the model string, so the board rendered one model as two: a `fable` row beside a `claude-fable-5` one, and four Claude models a submission under a pinned id away from splitting the same way.

The transcripts kept what the rows did not. Running the current `ClaudeCode.usage()` over each stored transcript returns the same `modelUsage` map the runner reads today, so every id below is recovered from the run's own artifacts, not inferred from the alias. Each run was rewritten only after the expected id appeared in the `modelUsage` of every one of its rows.

| alias | resolved to | runs | rows |
|---|---|--:|--:|
| `fable` | `claude-fable-5` | 1 | 6 |
| `sonnet` | `claude-sonnet-5` | 6 | 36 |
| `haiku` | `claude-haiku-4-5-20251001` | 5 | 27 |
| `opus` | `claude-opus-5` | 1 | 6 |

In every run, `model` was set to the resolved id, `usage.models` was backfilled with the full served set (each carries a `claude-haiku-4-5-20251001` sidechain alongside its primary), and the directory was renamed to the `<harness>-<model>-<effort>-<id>` the wizard would generate today. Scores, stages, timings, token counts, transcripts, and part sources are untouched.

## The one run that also needed its revision restamped

`claude-claude-fable-5-high-b523a2` was graded under `28728fea0e2f` (cable_clip), `e60a6422d46a` (bit_block), `4eb71d63bef3` (bundle_holder), `d2dc4e75efc7` (pole_rest), `2498e1db7385` (valve_knob), and `ea00b7650ef5` (leg_cup). It is the only alias run that covers the same six tasks as a later run of the same model at the same effort, so leaving those revisions in place would have kept the two rows apart on the page for a reason that no longer exists.

Two inputs to that digest moved between the two runs: the `modelUsage` capture that caused this whole problem, and a crash guard in `leg_cup/task.py` for an empty probe region. Neither touches a rubric, and re-grading all six parts under the current revisions reproduces every committed score and stage exactly, valve_knob's 0.675 included, so the rows carry the current revisions.

The other fourteen runs keep theirs. They cover tasks their same-model siblings did not, so nothing had to merge, and several ran against nurb 0.10.0 under an older CLI. That is a real difference in what the model was working with, and the report separates rows on it deliberately.

## Checking any of this

For the model ids, run `ClaudeCode().usage()` over a run's `transcript.txt` files and read `models`. For a score, materialize the task at seed 13, drop the submitted part in, restore that run's `measurements.toml` for leg_cup, and grade.
