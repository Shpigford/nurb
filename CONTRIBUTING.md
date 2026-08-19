# Contributing to nurb

The [README](README.md) is about using nurb. This file is about hacking on it.

## How it works

### The dev loop

`nurb dev` is one long-lived process: a watchdog file watcher, the build worker, and an HTTP plus websocket server on one port (7373 by default, or the next free one; `--port` pins it). It stays alive because importing the OCCT kernel costs about 45 seconds cold. After that, rebuilds run 30 to 400ms depending on the part, which matters because an agent iterates in save-check cycles, dozens per part.

A save flows like this:

```
save parts/<name>.py
  -> watcher fires, the module is re-imported in the warm process
  -> @part functions rebuild with the current slider values
  -> the B-rep is tessellated (a direct indexed read of OCCT's triangles, ~30ms)
  -> GLB bytes push over the websocket
  -> the viewer swaps the mesh without moving your camera
```

A build error takes the same path: the traceback is trimmed to the user's own part file and shown in the viewer, and the last good geometry stays on screen.

### The viewer

`src/nurb/viewer.html` is a single self-contained page: three.js (vendored, r169), Z-up, camera persistence across rebuilds, one slider per keyword parameter, a section plane, check findings pinned to the faces they fired on, a print time row, a stress button, and export buttons. The desktop app embeds the same page in an iframe, so a browser tab and the app show the same thing.

### The modules

| Module | What it owns |
|--------|--------------|
| `src/nurb/registry.py` | `@part`, signature introspection: keyword defaults become parameters |
| `src/nurb/builder.py` | load, build, tessellate, GLB |
| `src/nurb/checks.py` | the printability rules, convexity, `Finding`/`Context`, variants |
| `src/nurb/probe.py` | what `nurb inspect` measures, in the rules' own units |
| `src/nurb/polish.py` | the bisecting polish pass, and chamfer with real errors |
| `src/nurb/crown.py` | `crown()`, a rounded bead on a rim, on request |
| `src/nurb/orient.py` | `stand()`, the diagonal print stance with its bed facet |
| `src/nurb/holes.py` | `counterbore()` and friends |
| `src/nurb/assembly.py` | `assembly`, `use`, `hinge`, `obstacle` |
| `src/nurb/mesh.py` | `import_stl()`, flat-faced meshes that can become a solid |
| `src/nurb/scan.py` | `nurb scan`: measuring a foreign mesh in mm |
| `src/nurb/compare.py` | deviation from a target mesh, in both directions |
| `src/nurb/measurements.py` | `measured()`, and the refusal to guess |
| `src/nurb/card.py` | the card's AUTO block |
| `src/nurb/edit.py` | writes slider values back into a part's keyword defaults |
| `src/nurb/extract.py` | duplication across sibling parts, up to alpha-equivalence |
| `src/nurb/slicing.py` | the handoff to an installed slicer, and the two numbers back |
| `src/nurb/stress.py` | voxel FEA behind `nurb stress` and the viewer's stress button |
| `src/nurb/render.py` | headless PNG, the only module that wants a browser |
| `src/nurb/server.py` | watcher, rebuild, HTTP + websocket on one port |
| `src/nurb/api.py` | the vocabulary, derived from `__all__` so it cannot drift |
| `src/nurb/cli.py` | the command surface |
| `src/nurb/doctrine.md` | the design doctrine, shipped in the package, printed by `nurb rules` |
| `src/nurb/printers.toml` | shipped printer profiles |

The public API is `src/nurb/__init__.py`: everything exported there is a promise, everything else is internal and free to change. The version lives in `pyproject.toml` and nowhere else.

## Setup

Prerequisites:

- [uv](https://docs.astral.sh/uv/). It fetches the right Python (3.13+) on its own.
- For the render tests and `nurb render`: a Chromium, installed by playwright below.
- For the desktop app only: a Rust toolchain, Node 22+, and Xcode command line tools.

```bash
git clone https://github.com/Shpigford/nurb.git
cd nurb
uv sync --locked --all-extras --dev
uv run playwright install chromium   # without a browser the render tests fail, not skip
```

## Run it against a real project

`examples/notch` and `examples/demo` are real projects. From inside one, run the checkout's nurb with `--project`:

```bash
cd examples/notch
uv run --project ../.. nurb check
uv run --project ../.. nurb dev
```

The viewer URL takes `?part=<name>&variant=<name>` to deep-link the exact configuration you want looked at.

## Dependencies are a cost

Four runtime dependencies: build123d, trimesh, watchdog, websockets. playwright is an optional extra because `nurb render` is the only command that wants a browser and the download is larger than everything else here. Adding a fifth dependency needs a strong, stated reason. Anything new the viewer imports gets vendored (and added to `pyproject.toml`'s `source-include`), because the viewer must keep working with no network.

## Testing

```bash
uv run pytest           # the suite
uv run pytest -n auto   # parallel; the suite is CPU-bound OCCT builds and scales almost perfectly
```

The parts in `examples/` are the calibration set, asserted against dimensions from really-printed parts, so a broken example is a red build rather than a stale README. Fit tests use literal numbers, never the part's own constants, because a test that reads the same constant as the code cannot catch that constant being wrong.

`evals/` is its own uv project with its own suite (`cd evals && uv sync --dev && uv run pytest`); the root `pytest` deliberately does not collect it.

CI (`.github/workflows/test.yml`) runs three jobs on every push and PR: the pytest suite with the render extra and a real Chromium, the evals suite, and `nurb check --strict` from inside `examples/notch`, which exercises the rules against the real library on a machine they were not calibrated on.

## The desktop app

`desktop/` is a Tauri shell around nurb: project rail, agent chat column, and the live viewer in one window. The app embeds `viewer.html` in an iframe, so features about the part itself land in the viewer and reach both the app and `nurb dev` in a browser; React shell work is only for what the shell alone can do.

```bash
cd desktop
npm install
npm run tauri dev
```

Debug builds run nurb out of the checkout and need no provisioning. Release builds provision everything on first launch into `~/Library/Application Support/dev.nurb.desktop`: a managed CPython and venv with the bundled nurb wheel, a pinned Node, and the agent ACP adapters. `desktop/README.md` has the full provisioning and signing story.

## Debugging the viewer

`window.__nurb` exposes `{ THREE, scene, camera, controls, mesh, ready }`. The URL takes `?part=<name>`, `?view=iso|front|back|left|right|top`, and `?bare`. three.js is vendored in `src/nurb/vendor/three`, so the viewer needs no network; see the README beside it before changing versions.

A geometry trap worth knowing: `BRep_API: command not done` from a chamfer means two chamfered edges have less than `2 * chamfer_size` of face between them. Every edge chamfers fine on its own and only the batch fails, so testing one at a time reports nothing wrong. Bisect the set; `polish()` does this bisection for you.

## Releasing

A release is one version across the engine and the app, and it is triggered by a merge, not a button:

1. Bump the version in four places, and tests enforce they agree: `uv version X.Y.Z` (pyproject), the `version:` lines in `src/nurb/skill.md` and `skills/nurb/SKILL.md`, and `version` in `desktop/src-tauri/tauri.conf.json`.
2. Merge to main. `.github/workflows/publish.yml` sees the untagged version, builds and uploads to PyPI over trusted publishing (no tokens), then creates the `vX.Y.Z` tag and GitHub release with generated notes. The job is idempotent: an already-tagged version is skipped, an already-uploaded version still gets its tag.
3. Run `desktop/scripts/release.sh` from a Mac with the Developer ID certificate in the keychain. It builds, signs, and notarizes the app for Apple silicon and Intel, uploads `nurb.dmg` and `nurb-intel.dmg` plus updater archives into that same GitHub release, and refreshes `latest.json` on the rolling `desktop-latest` prerelease that installed apps poll for self-updates. It refuses to upload twice for one version.

The release date matters beyond shipping: FSL-1.1-MIT converts each version to MIT two years after its release, and the GitHub release is that date, published.
