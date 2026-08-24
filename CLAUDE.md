# nurb

## Delegation policy (read first)

The session model (Fable) is the orchestrator, not the worker. Fable is the most expensive tier; spend its tokens only on decomposition, judgment calls, synthesis, and talking to the user. Delegate everything else to subagents via the Agent tool, picking the cheapest model that can do the job well:

- `model: "opus"` — the default worker tier. Anything requiring real judgment: implementation, debugging, architecture-aware exploration, adversarial review.
- `model: "sonnet"` — cheap tier for mechanical or low-stakes work: running tests and reporting output, simple greps/lookups with a known target, rote refactors from an exact spec, formatting, screenshot capture, admin chores. If getting it slightly wrong is cheap to catch, use sonnet.

How work splits:

- **Exploration/research**: never read broadly yourself. Spawn `Explore` agents (model: opus) with tightly scoped questions; consume their synthesized reports, not raw files. Trivial "find the file that defines X" lookups can go to sonnet.
- **Implementation**: for any multi-file change, spawn `general-purpose` agents (model: opus) with exact file paths, the relevant doctrine from this file, and a definition of done (tests to run). Independent changes get parallel agents in one message.
- **Verification/review**: adversarial review and blast-radius checks go to opus agents. Plain test runs and lint passes go to sonnet agents.
- Fable itself only edits directly when the change is small (one or two files, already-known locations).

Token rules:

- Batch independent agent launches in a single message so they run concurrently.
- Give agents file paths and constraints up front so they don't rediscover this file's contents; paste the relevant doctrine into the prompt.
- Never re-read files an agent already summarized; trust the report, spot-check only what you'll edit.
- Read only the line ranges you need from large files.
- Don't echo file contents or long diffs back to the user; report conclusions.

Agentic CAD for 3D printing. A part is a Python function; a long-lived process
rebuilds it on save and pushes geometry to a browser without moving the camera.

Built on build123d (OCCT), so parts are real B-rep solids.

## The part contract

One convention carries the whole system:

```python
from nurb import *

@part
def dispenser(width=80.0, height=120.0, wall=2.0, draft=False):
    body = Box(width, height, wall)
    if draft:
        return body
    bed = body.bounding_box().min.Z
    keep = body.edges().filter_by(lambda e: e.bounding_box().min.Z > bed)
    return polish(body, keep, 1.0)
```

**Keyword defaults are the parameters.** That single declaration feeds the agent, the
CLI, the viewer's sliders, the tests, and any future configurator. Never add a
parallel `PARAMS` dict; the two would drift.

`draft` is optional and injected by the runtime, never passed by callers. When true,
skip the polish pass. Worth 20% on a real part, not the 18x a cube suggested: chamfers
are 23% of the gridfinity shelf's build.

The build is nearly all of the loop. Tessellation used to look like the larger half at
620ms, and almost all of that was one pathological iterator in build123d rather than
any geometry; `builder._triangulate` reads the same triangles by index in 30ms.
Write a continuous dimension as a float (`chamfer_size=1.0`) and a count as an int
(`bracket_count=4`): the viewer reads the type of the default to decide whether that
parameter's slider steps by one.

## Commands

```
nurb new <name>      create parts/<name>.py and its card
nurb dev             watch, rebuild, serve the viewer on :7373 or the next free port
nurb build [part]    build once, report size and timing
nurb check [part]    run the printability rules, --strict for CI
nurb inspect [part]  faces, normals, concave edges, each finding on its face, --render for stills of them
nurb scan <file>     measure a mesh in mm, a phone scan or a downloaded model (STL/OBJ/GLB or triangulated PLY), --section for a profile polyline
nurb compare [part]  deviation from the card's target mesh, both directions, --against for a one-off file
nurb rules           print the design doctrine
nurb api             the vocabulary a part file gets, with signatures
nurb skill           print an agent skill file for any AI harness, --sync rewrites installed copies
nurb update          upgrade nurb, then re-sync the installed skill to match
nurb card [part]     regenerate a card's AUTO block
nurb diff [part]     what moved since the card was written: size, volume, faces, verdict
nurb slice [part]    print time and filament, via an installed OrcaSlicer or BambuStudio
nurb stress [part]   static stress under a load: peak MPa, sag, margin to breaking
nurb verify [part]   the doctrine's verification list, --report bundles it with renders
nurb render [part]   write build/renders/<part>.png, --section cuts it open, needs the render extra
nurb export [part]   write 3MF with tuned print settings into build/, --formats for STL, STEP or GLB
nurb extract         find duplication across sibling parts
nurb launcher        write viewer.command (viewer.cmd on Windows), a double-clickable `nurb dev`
```

`uv run pytest` runs the suite, which includes the parts in `examples/`.

A project is any directory containing `parts/`. There is no init step, and there
never should be.

A release is a version bump merged to main: `uv version X.Y.Z`, plus the matching `version:` line in `src/nurb/skill.md` and `skills/nurb/SKILL.md`, plus the matching `version` in `desktop/src-tauri/tauri.conf.json` (tests enforce all three agree). The publish workflow does the PyPI upload, tag, and GitHub release; `desktop/scripts/release.sh` then builds the desktop app into that same release, so the engine and the app always ship together under one version. The `/release` skill runs the whole ceremony end to end, changelog included.

## Layout

```
src/nurb/registry.py      @part, signature introspection
src/nurb/builder.py       load, build, tessellate, GLB
src/nurb/checks.py        printability rules, convexity, Finding/Context, variants
src/nurb/compare.py       deviation from a target mesh, the ghost's numbers
src/nurb/polish.py        the bisecting polish pass, and chamfer with real errors
src/nurb/orient.py        stand(), the diagonal print stance with its bed facet
src/nurb/probe.py         what `nurb inspect` measures, in the rules' own units
src/nurb/api.py           the vocabulary, derived from __all__ so it cannot drift
src/nurb/printers.toml    shipped printer profiles, named by a project's printer.toml
src/nurb/card.py          the card's AUTO block
src/nurb/extract.py       duplication across sibling parts, up to alpha-equivalence
src/nurb/mesh.py          import_stl(), the flat-faced meshes that can be a solid
src/nurb/measurements.py  measured(), and the refusal to guess
src/nurb/edit.py          writes slider values back into a part's keyword defaults
src/nurb/render.py        headless PNG, the only module that wants a browser
src/nurb/slicing.py       the handoff to an installed slicer, and the two numbers back
src/nurb/stress.py        voxel FEA behind `nurb stress` and the viewer's stress button
src/nurb/doctrine.md      the doctrine itself, shipped in the package
src/nurb/server.py        watcher, rebuild, HTTP + websocket on one port
src/nurb/viewer.html      three.js viewer, Z-up, camera persistence, sliders, section
src/nurb/vendor/three/    three.js r169, so the viewer needs no network
src/nurb/cli.py           command surface
examples/notch/           the real parts, which are also the calibration set
tests/test_notch_fit.py   the hanging interface, asserted for every configuration
tests/                    rules and examples, both cases per rule
```

The model leaderboard (tasks, scorer, runner, and every submitted run) lives in its own repo, [Shpigford/nurb-benchmarks](https://github.com/Shpigford/nurb-benchmarks): submissions dwarf everything else and keep growing, so they stay out of this repo. `site/benchmarks.html` here is regenerated from that repo's submissions by the `/leaderboard` skill.

## Rules

### This file is for developing nurb, not for using it

The part-design workflow (start `nurb dev` first thing, end every reply with the viewer URL, model while the user watches) belongs to the shipped skill (`src/nurb/agents.md`, mirrored into `skills/nurb/SKILL.md`) and applies in a user's parts project, never in this repo. Here you are building the tool. When verifying viewer or server changes, run `nurb dev` against `examples/notch` in the background and share the URL for that; `?part=<name>&variant=<name>` deep-links to the exact configuration you want looked at.

### Every feature gets a surface in the app

The desktop app is the primary entry point, and it is what to optimize for. A capability that exists only as a CLI subcommand does not exist for the person who downloaded the app: they will never type it, never read `--help`, and never learn it is there. "The agent can run it when asked" is not a surface either, because it requires the user to already know the feature exists in order to ask for it.

So a feature is not done when the command works. It is done when someone looking at their part can see it and use it without being told. Ship the command and the surface in the same change, and if the surface is genuinely wrong for the feature, say why out loud rather than deferring it.

Nearly always that surface belongs in `src/nurb/viewer.html`, not in `desktop/src`. The app embeds the viewer in an iframe, so one control there reaches both the app and `nurb dev` in a browser. React shell work is for what only the shell can do: the window, the rail, projects, chat, updates. Anything about the part itself goes in the viewer.

Two things a surface owes the user that a command does not. It must not dead-end: when a feature needs something the project has not chosen yet, offer the choice in place rather than printing what the user should have configured. And a result that outlived its geometry is worse than no result, so anything cached from a build clears when that part rebuilds.

### No change is done until the desktop is accounted for

The recurring failure mode in this repo: a change lands in the Python engine or the viewer, works in a browser, and ships with the desktop app never considered. That is backwards. The desktop app is the primary UI, so every change ends with an explicit desktop pass: what does `desktop/src` need for this, and if the honest answer is nothing, say that in the summary rather than leaving it unexamined.

The shell duplicates viewer state on purpose, and that duplication is where changes go silently missing. Its rail draws its own part and variant rows from `list_parts` polling, not from the viewer's sidebar; selection flows through `nurb:part` postMessages; viewer state the shell must react to travels over `nurb:*` messages (`nurb:saved`, `nurb:shared`, `nurb:variant`). So check each seam: new server fields the rail should reflect need `list_parts` plumbing, new viewer state the rail mirrors needs a message, and anything that lives in the sidebar or footer is invisible in the app, because `?embed` hides both. Labels too: embed mode speaks to hobbyists, so a button that names a `.py` or `.md` file in the browser needs an embed variant that does not.

The check is cheap: grep `desktop/src` for the concept you touched, and run `./node_modules/.bin/tsc --noEmit` plus `npm test` in `desktop/` whenever it changed.

### Command names stay boring

The CLI's user is a language model, while the app's user is a person; both surfaces are real and neither substitutes for the other. An agent that has never seen this tool can guess `build`, `check`, `export`. It cannot guess a themed alias. Every clever name is an indirection that degrades in a fresh context. The brand can be distinctive; the interface cannot.

### Never port Fusion scaffolding

Notch's Fusion timelines contain constructions that exist only to work around a
stateful CAD kernel: `ChannelTool`, the 16-lobe comb, `CombWeb`, `JoinComb`, fixed
over-counts, derive links. In code these are a `for` loop and an `import`. Porting
them imports accidental complexity into a system that never had the problem.

What does survive is physics: the print doctrine, sliver thresholds, chamfer sizing
limits, and chamfer ordering effects.

### Prefer `new_edges` over geometric selectors for chamfers

Each chamfer changes topology, so selectors resolved against pristine geometry drift
once an earlier chamfer runs. `new_edges(before, combined=after)` returns exactly the
edges an operation created and sidesteps the problem. It is the algebra-mode
equivalent of a builder's `Select.LAST`, and algebra mode is what a part file uses, so
`part.edges() - last` is not available to you. Reach for it before falling back on
strict operation ordering.

### Two chamfered edges need room between them

More than `2 * chamfer_size` of face, or OCCT fails with `BRep_API: command not done`.
This is the analogue of Fusion's `ASM_BL_NO_MATE` and it is the single most common way
a part stops building. The trap: every edge chamfers fine on its own and only the batch
fails, so testing them one at a time reports that nothing is wrong. Bisect the set.

### Systems are extracted, never scaffolded

Notch did not begin as a system; `block_width = 25.16` exists because a real wall got
measured after parts existed. Guessing what is shared before you know propagates the
wrong abstraction. The command is `nurb extract`, not `nurb new system`.

It reports and does not rewrite, because choosing which free names become parameters and
what the function is called are judgements about what the thing *is*, and noticing is
the only mechanical part. Run over the finished port it found `system.slab()` in six
files at once. **The test of a real extraction is what does not use it**: three parts
still build their own plate, because they genuinely differ, and a helper with a flag for
each of them would have been the wrong abstraction wearing the right name.

### Generated files stay nearly empty

Scaffolders traditionally emit commented placeholder blocks. That is fine for humans
skimming and actively bad for an agent, where it is context to read past. `nurb new`
emits a working part and a card with headings only.

### Verify before claiming

Untested code is a guess. Before saying something works: run it, trigger the exact
path changed, and observe the result. For viewer changes that means a screenshot, not
a DOM query. Two traps already hit here, both of which produced confident wrong
conclusions:

- `elementFromPoint` skips `pointer-events: none` elements, so it reports the canvas
  covering an overlay when painting is fine.
- A repro that starts at equilibrium proves nothing. The ResizeObserver loop needs an
  initial size mismatch to ratchet against.

Also: `print(..., flush=True)` in the server. Python buffers stdout when it is not a
tty, and buffered output makes debugging the watcher blind.

## Open source conventions

This is source-available under FSL-1.1-MIT (converts to MIT after two years). Build
as though every file will be read by a stranger.

- **No secrets, ever.** No API keys, no absolute paths pointing into a home
  directory, no personal data in committed files or test fixtures.
- **Public API is `src/nurb/__init__.py`.** Anything exported there is a promise.
  Everything else is internal and free to change. Keep the surface small.
- **Dependencies are a cost.** Four right now: build123d, trimesh, watchdog,
  websockets. Adding a fifth needs a reason that survives being asked out loud.
- **Watch the transitive license surface.** build123d is Apache-2.0, but it pulls
  OCP, whose wheel bundles OCCT native libraries under LGPL-2.1-with-exception. That
  is fine while we dynamically link and do not redistribute them. It stops being
  automatic if nurb is ever bundled into a single-file binary, which would require
  shipping the OCCT license and keeping the library replaceable. Attribution lives in
  the README's third-party notices.
- **Errors are the interface.** Most users will meet this tool through a failure.
  Tracebacks get trimmed to the user's own file; messages say what went wrong and
  what to do, never just "invalid input".
- **The doctrine ships in the package**, exposed via `nurb rules`. One source of
  truth. `SKILL.md` and `AGENTS.md` are thin shims that point at it, never copies.
- **The viewer works offline.** Everything it *needs* is local: three.js is vendored in `src/nurb/vendor/three`, because a CAD tool that needs a CDN is broken on a plane, and `nurb render` drives the same page. Anything new the viewer imports gets vendored too, and `pyproject.toml`'s `source-include` has to carry it. Network is allowed for nudges that degrade silently, like the daily PyPI update check, which also stays out of headless renders.
- **Examples are tests.** `examples/` holds real parts that the suite builds, so a
  broken example is a red build rather than a stale README.

## Style

- Match the surrounding code. Comments explain *why*, and only where the reason is
  not obvious from the code.
- No em-dashes in user-facing copy, docs, or comments.
- Commit messages describe what changed and why, in plain sentences.
- **Never hard-wrap prose. Ever.** One paragraph is one line; editors soft-wrap. This applies to every markdown and text file, and it applies even when the surrounding file is already wrapped: fix the paragraph you touch instead of matching the wrapping. Code, tables, and fenced blocks keep their formatting.
