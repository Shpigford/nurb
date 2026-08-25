# nurb evals

How well do coding agents design 3D-printable parts with nurb? Each task in `tasks/` is an original part with seeded parametric dimensions. An agent gets a throwaway nurb project and the task instruction; the scorer builds whatever it wrote, headlessly, and grades the actual B-rep geometry. No human judging, no reference meshes, nothing to memorize.

The current leaderboard is in [REPORT.md](REPORT.md).

## The tasks

Tasks come in classes, because the benchmark measures two different abilities:

- **Spec tasks** (`tasks/cable_clip`, `tasks/bit_block`): every dimension stated, zero interpretation. They measure execution fidelity, the floor. bit_block raises that floor to where the kernel pushes back: a grid of chamfered pocket mouths with 2.0 webs sits close to OCCT's adjacent-chamfer limit, so a wrong chamfer order, a selector resolved before the pockets were cut, or a grid slid half a millimetre does not lose points, it does not build. Its grid is driven by an int parameter and the flex probes rebuild it at other counts, which catches a grid written out by hand.
- **Function tasks** (`tasks/bundle_holder`, `tasks/pole_rest`, `tasks/valve_knob`): the problem, the measured interfaces, and the printer are stated, the geometry is not. Scoring is functional gates that are mechanical facts of the B-rep (the bundle has a retained place to sit, the screw has a bore, a seat, and driver access) plus a material-economy gradient, so a cleverer design legitimately wins without a human deciding it was clever. This is where models that can interpret outmaneuver models that can only follow. pole_rest is the class's curvature test: the support gate demands one continuous 120 degree arc of backed contact around a measured pole, which a V-block or a square channel mechanically cannot own, so only geometry sized to the measured curve passes. valve_knob is the class's mating-fit test: the grader drives a virtual D-stem into the candidate's bore and grades the tolerance band from both sides (grown by the stated clearance it must pass, grown by the stated slop it must jam) and then turns it 20 degrees, which a lazy round bore survives freely and therefore fails.
- **Judgment tasks** (`tasks/leg_cup`): the geometry is stated, but one real-world dimension is deliberately not on file and nobody can measure it right now. What is scored, beyond the geometry, is measurement discipline the way nurb's doctrine defines it: the part derives from `measured()` values (the scorer rebuilds it against a rewritten `measurements.toml` and the geometry must track), and the missing dimension is recorded as a provisional guess with provenance instead of baked into the code. A silent plausible number works tonight and is exactly what loses points. Because the graded artifact is the part plus the measurements entry next to it, this task is always graded inside a materialized project.

Every scored check is stated in the task instruction; nothing unstated is ever graded.

## What a row is

A leaderboard row is one model at one effort level, run through a real agent CLI (`claude` or `codex`) on the contributor's own subscription. That is deliberate: it benchmarks what a nurb user actually runs, which is the model, the harness, and the shipped skill together. Every trial records the harness version, nurb version, evals version, and a content revision over the task, scorer, harness adapters, shipped nurb package, and lockfile; changing any of them makes a different row.

Scoring is gate-then-grade. A part that does not build within the timeout, or builds anything other than exactly one solid, scores zero. Past the gate, three weighted stages: the printability rules under a context the task owns (0.3), the task's dimensional assertions against the B-rep (0.5), and flex probes that rebuild the part with a changed parameter and assert the geometry tracks, which catches hardcoded dimensions (0.2). Stage columns overlap by design: a part wrong at the stated size is wrong at every probed size too.

Candidate code never runs in the scorer's process. It builds in an isolated worker and crosses into the trusted scorer only as BREP geometry, so forged output and mutated check registries score zero instead of a forged pass.

## Running a row

The easy way is the wizard, from anywhere (or paste the line to your AI and let it drive):

```
curl -fsSL https://nurb.dev/bench.sh | sh
```

It detects which agent CLIs you have, leads with the combo the leaderboard currently needs most (fewest pooled trials among the menu's models, for the CLIs you actually have), offers the rest of the models from a menu with their run counts so you never guess a spelling, asks how many rounds to run and says why more rounds mean a steadier number, runs them on your subscription three trials at a time (`--parallel` changes that; agent time is unchanged, wall clock divides), sanitizes the artifacts, and then offers to open the pull request itself with the GitHub CLI: branch, commit, push, fork only if you lack push access, PR URL printed. Every run is its own uniquely named directory, branch, and PR, so run it as many times as you like, even concurrently: more runs mean tighter numbers, and matching rows pool on the leaderboard no matter which PR they arrived in. Agents and scripts can skip every question with flags: `uv run python -m nurb_evals.contribute --harness claude --model claude-sonnet-5 --effort medium --pr yes`.

The manual way needs `uv` and the `claude` or `codex` CLI installed and logged in to your own subscription. Then:

```
cd evals
uv sync --locked
uv run python -m nurb_evals.run --harness claude --model claude-opus-5 --effort high --seed 13 --trials 3 --task tasks/cable_clip
uv run python -m nurb_evals.run --harness claude --model claude-opus-5 --effort high --seed 13 --trials 3 --task tasks/bit_block
uv run python -m nurb_evals.run --harness claude --model claude-opus-5 --effort high --seed 13 --trials 3 --task tasks/bundle_holder
uv run python -m nurb_evals.run --harness claude --model claude-opus-5 --effort high --seed 13 --trials 3 --task tasks/pole_rest
uv run python -m nurb_evals.run --harness claude --model claude-opus-5 --effort high --seed 13 --trials 3 --task tasks/valve_knob
uv run python -m nurb_evals.run --harness claude --model claude-opus-5 --effort high --seed 13 --trials 3 --task tasks/leg_cup
uv run python -m nurb_evals.report results/claude-opus-high
```

Both runs append to the same `results.jsonl`; the report renders one table per task.

Cost: trials spend your subscription, not API credit. A cable_clip trial has run 2 to 8 minutes of agent time depending on the model; three trials is a coffee, not an afternoon. The `--timeout` wall clock (default 3600s per trial) exists to stop runaway sessions, not to measure: time per part is one of the three numbers a user decides on, so the cap sits high enough that a finishing model records its true time. A trial that still hits it is reported as censored, never as a duration, and the cap used lands in the row. A session the machine kills mid-run is different: an updater cycling instances or a reaper sending SIGTERM measures your laptop, not the model, so the runner never scores it. The killed session is kept next to the trial slot as `trial_<n>_killed_<k>` for audit, the trial reruns fresh, and three kills in a row abort the run with instructions to fix the environment. Every row in a `results.jsonl` is therefore a completed agent session.

Each run leaves everything under `results/<harness>-<model>-<effort>/`: `results.jsonl` with one row per trial (full benchmark identity, score, stages, usage, durations), plus `<task>/trial_<n>/` holding the full JSON event transcript and the project the agent left behind. A row nobody can audit is a rumor, so all of it is kept.

Trials run on your machine like any normal agent session. The live throwaway project sits outside the benchmark checkout, then moves under `results/` after the harness exits for auditing. `claude` runs with permissions skipped inside that project; `codex` uses its own workspace-write sandbox and an ephemeral home containing only your auth. Only run rows on a machine where you would run those agents anyway; containerized trials are a planned hardening step.

## Submitting a row

A submission can be any number of trials, including one: `--trials 1` is a valid, welcome contribution. The leaderboard pools every submitted trial that shares a full benchmark identity (task content revision, harness and version, model, effort), so single runs from different people stack into one row with a growing sample, and each attempt shows as its own tick on the published bars. What keeps pooling honest is submitting everything you ran, not a lucky pick: your `results.jsonl` must be complete for the label you submit (contiguous trial numbers, a transcript for every row, no pruning), and the seeded spot-check below applies regardless of how many trials you sent. If a run went badly, that is data; submit it.

Open a PR that copies your `results/<label>/results.jsonl`, each `<task>/trial_<n>/transcript.txt`, and the auditable candidate source into `submissions/<label>/`. Preserve `project/parts/*.py` plus any project-root or package `.py` files they import; leave cards, meshes, renders, and other generated project files out. Replace machine-specific home paths in transcripts and source with `<home>` or `<workspace>`. `results/` itself is gitignored so a submission is always a deliberate copy, never a bulk commit of local runs.

Your PR carries only your run's directory, nothing else: submission PRs are pure additions, which is what lets any number of them, from any number of people or concurrent sessions, merge in any order without a conflict. `evals/REPORT.md` and the page at [nurb.dev/benchmarks](https://nurb.dev/benchmarks.html) are regenerated from the merged submissions when a maintainer publishes the leaderboard, which is also when new runs get their sanity check (the spot-check policy above) and new model combos get their verdict sentences. Your row appearing on the page a few days after your PR merges is that process working, not your submission being lost.

Rows land on the leaderboard in one of two tiers:

- **self-reported**: the logs are present and format-valid.
- **validated**: a maintainer re-ran your model and effort on a fresh seed and the scores matched within noise.

The spot-check works because every assertion is parametric in the seed: the instruction, the fixture measurements, and the graded dimensions all move together. A planted or memorized solution scores zero on a seed it has never seen, so validation needs no trust in the submitted transcripts.

What the spot-check cannot catch is a part written against the grader rather than the task: candidate code is built in its own process behind a B-rep boundary, which keeps it away from the check functions and the verdict, but it still chooses the geometry it exports, so a part that detects the grading process and builds something different for it would pass a re-run too. That is out of the benchmark's threat model, because a graded agent never sees the grader, and a contributor who does could forge the JSONL rows outright. The defense is that submitted parts are published and readable: a part file that inspects `sys.argv` is not a design, and gets the row rejected.
