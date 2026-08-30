# Porting upstream nurb releases into the Windows fork

This fork (nurb-windows) tracks upstream nurb and adds a Windows platform layer.
A future upstream release is ported by an AI agent following the workflow
below. The companion `docs/windows/PORTING-MERGE-CHECKLIST.md` holds the
per-file decision rule and the worked conflict map from v0.21.0; this guide is
the end-to-end procedure and the map of what is Windows-specific.

## What this fork owns

These are the fork's contributions. Upstream work that touches them must be
**ADAPT**ed or **KEEP**-decided, never blindly overwritten:

- `src/nurb/platform/` - the OS-specific layer (paths, process handling, shell
  invocation). Fork-additive; upstream has nothing here.
- `src/nurb/cli.py`, `src/nurb/server.py`, `src/nurb/mcp.py` - upstream code
  with Windows adaptations inside (per-user config paths, process routing).
- `src/nurb/plugins/` and `plugins/` - the plugin system, fork-only.
- `desktop/` - the Tauri desktop app (React + Rust), fork-only.
- `tools/upstream_sync.py`, `tools/release_gate.py` - the fork's CI gates.
- `tests/` - includes fork tests (`test_plugins.py`, Windows-skip decorators).
- `.github/workflows/` - the fork's Windows CI.

What tracks upstream closely (usually **PORT** on conflict): the CAD engine
modules (`builder.py`, `checks.py`, `polish.py`, `orient.py`, `card.py`), the
doctrine, the shipped printer profiles, and `pyproject.toml` version bumps.

## Before you start

```bash
git fetch upstream main
python tools/upstream_sync.py status --strict   # tells you which paths drifted
python tools/release_gate.py                    # current state must be READY
```

The strict gate classifies every path as SAFE (fork and upstream identical),
REVIEW (both changed), or WINDOWS-SPECIFIC. A clean start is a pure-ahead fork:
all drift is yours, upstream is behind you. If the gate reports anything else,
stop and reconcile before porting anything.

## The port, step by step

1. **Inspect the upstream release.** `git log --oneline upstream/main` since
   the last merged upstream commit. Read the release notes and the diffs of
   every touched file, not just the file names.
2. **Compare against this fork.** For each upstream change, find the fork's
   version of the file. Identical files are not exempt: history, callers, and
   dependencies differ even when content does not.
3. **Identify conflicts.** `git merge --no-commit --no-ff upstream/main`
   enumerates them. Classify every conflicted path with the decision rule in
   `PORTING-MERGE-CHECKLIST.md` (PORT / ADAPT / KEEP / REWRITE / DROP / DEFER).
4. **Understand architectural changes before resolving.** A new parameter, a
   renamed module, or a moved responsibility upstream means the fork's callers
   change too. Read the upstream PR or issue that introduced the change when
   the diff alone is not self-explanatory.
5. **Map into the Windows fork.** Resolve each conflict semantically:
   upstream's structure with the fork's Windows behavior inside it (ADAPT),
   fork content winning (KEEP), or a fresh write (REWRITE). Never resolve by
   taking one side wholesale.
6. **Preserve the Windows adaptations.** After the merge, verify the platform
   layer, the process routing, the per-user config paths, and the plugin system
   are intact. `git diff upstream/main --stat` shows what the fork still owns.
7. **Run the tests.** `uv run --project . pytest tests/ --collect-only` first
   (a post-merge patch that dropped an import fails at collection, which is a
   suite failure, not a test failure), then the full suite.
8. **Fix regressions.** A failing fork test is a real regression, not noise.
   Fix the code, never delete the test.
9. **Review the diff.** `git diff` from the merge base: every change is either
   the upstream feature or a deliberate fork adaptation, and nothing private
   (`.dev/`, tokens, machine paths) is in it.
10. **Verify packaging.** `python tools/release_gate.py` must read READY, and
    `python tools/upstream_sync.py status --strict` must exit 0.
11. **Commit.** One commit per merge, message naming the upstream release and
    the notable decisions.

## The verification gate (do not skip)

```bash
python tools/upstream_sync.py status --strict   # exit 0: no SAFE-zone drift
python tools/release_gate.py                    # release-gate: READY
uv run --project . pytest tests/ --collect-only
uv run --project . pytest tests/
```

Plus, after any workflow change: parse the YAML (`.github/workflows/*.yml`).

## Breaking upstream changes to watch for

- **API changes in build123d** (the CAD kernel): geometry code in parts and
  modules breaks loudly; watch for renamed builders in upstream `builder.py`.
- **New shipped data files**: upstream adding to `printers.toml` or the
  doctrine means the fork's copies need the same addition (they are PORT-zone).
- **Agent-skill contract files**: `src/nurb/skill.md`, `src/nurb/agents.md`,
  and `skills/nurb/SKILL.md` must stay in lockstep. Tests assert the three are
  one body; changing one without the others breaks CI.
- **CLI surface changes**: new flags in upstream `cli.py` must also reach the
  fork's `mcp.py` tool definitions and the desktop app, which mirror the CLI.

## Where the plugin system lives (fork-only)

The plugin system is entirely fork-specific and does not exist upstream:

- `src/nurb/plugins/` - manifest parsing, the registry, the loader.
- `plugins/examples/` - the shipped example plugins (everything, agent-yoke).
- `plugins/_template/` - the scaffolding template behind `nurb plugin new`.
- `src/nurb/plugins/state.py` - per-project enable/disable state
  (`<project>/.nurb/plugins.toml`), shared by the CLI and the desktop Settings
  panel.
- `tests/test_plugins.py` - the plugin suite.
- `docs/windows/PLUGINS.md` - the plugin contract.

Upstream merges will not touch these. If a future upstream release ever adds
its own plugin concept, reconcile the two before layering one on the other:
decide which registry wins and keep a single manifest format.

## What an AI agent should never do

- Do not merge with `--strategy-option theirs` and push the result. Every
  conflict needs a classification, and the classification needs the fork's
  tests to pass.
- Do not drop the fork's CI gates to get a merge to go through.
- Do not copy `.dev/` or any private material into the port. The repo is
  public; the gate and the diff review are the checks that keep it that way.
- Do not "clean up" the Windows-skip decorators or the platform layer. They
  are the point of the fork.
- Do not commit a merge where `git diff upstream/main --stat` shows the
  platform layer or the plugin system deleted.

## The short version for a routine release

```bash
git fetch upstream main
git merge --no-commit --no-ff upstream/main
python tools/upstream_sync.py status --strict      # classify before resolving
# resolve per PORTING-MERGE-CHECKLIST.md decision rule
git merge --continue
python tools/upstream_sync.py status --strict      # must exit 0
python tools/release_gate.py                       # must be READY
uv run --project . pytest tests/ --collect-only
uv run --project . pytest tests/
```

Document each resolved path in the checklist's table before finishing. The
strict gate only tells you what drifted; the table is where the reasoning
lives.
