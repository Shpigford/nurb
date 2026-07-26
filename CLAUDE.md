# nurb

Agentic CAD for 3D printing. A part is a Python function; a long-lived process
rebuilds it on save and pushes geometry to a browser without moving the camera.

Built on build123d (OCCT), so parts are real B-rep solids.

**Read `docs/core/RESEARCH.md` before making architectural decisions.** It is the
central reference and explains why things are the way they are. `docs/core/PROGRESS.md`
is the running log; update it as you work.

## The part contract

One convention carries the whole system:

```python
from nurb import *

@part
def dispenser(width=80, height=120, wall=2, draft=False):
    body = Box(width, height, wall)
    if not draft:
        body = chamfer(body.edges().filter_by(Axis.Z), length=1)
    return body
```

**Keyword defaults are the parameters.** That single declaration feeds the agent, the
CLI, the viewer's sliders, the tests, and any future configurator. Never add a
parallel `PARAMS` dict; the two would drift.

`draft` is optional and injected by the runtime, never passed by callers. When true,
skip the polish pass. Worth 20% on a real part, not the 18x a cube suggested: chamfers
are 23% of the gridfinity shelf's build. Tessellation, at 620ms against a 470ms build,
is where the loop latency actually lives.

## Commands

```
nurb new <name>      create parts/<name>.py and its card
nurb dev             watch, rebuild, serve the viewer on :7373
nurb build [part]    build once, report size and timing
nurb export [part]   write STL/STEP/GLB into build/
```

A project is any directory containing `parts/`. There is no init step, and there
never should be.

## Layout

```
src/nurb/registry.py   @part, signature introspection
src/nurb/builder.py    load, build, tessellate, GLB
src/nurb/server.py     watcher, rebuild, HTTP + websocket on one port
src/nurb/viewer.html   three.js viewer, Z-up, camera persistence
src/nurb/cli.py        command surface
docs/core/             research, plan, progress
```

## Rules

### Command names stay boring

The primary user is a language model. An agent that has never seen this tool can
guess `build`, `check`, `export`. It cannot guess a themed alias. Every clever name
is an indirection that degrades in a fresh context. The brand can be distinctive;
the interface cannot.

### Never port Fusion scaffolding

Notch's Fusion timelines contain constructions that exist only to work around a
stateful CAD kernel: `ChannelTool`, the 16-lobe comb, `CombWeb`, `JoinComb`, fixed
over-counts, derive links. In code these are a `for` loop and an `import`. Porting
them imports accidental complexity into a system that never had the problem. See the
table in RESEARCH.md for the full list of what vanishes and what survives.

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
- **The viewer must work offline** once three.js is vendored. A CAD tool that needs
  a CDN is broken on a plane.
- **Examples are tests.** `examples/` holds real parts that the suite builds, so a
  broken example is a red build rather than a stale README.

## Style

- Match the surrounding code. Comments explain *why*, and only where the reason is
  not obvious from the code.
- No em-dashes in user-facing copy, docs, or comments.
- Commit messages describe what changed and why, in plain sentences.

## Current state

Phase 1 is done. Two real Notch parts live in `examples/notch/`, build to one solid
each, match their Fusion originals dimension for dimension, and reproduce their sliver
baselines exactly. The kernel question is settled and the timing numbers now come from
real geometry rather than a cube. Phase 2 (`nurb check`) is next.

`docs/core/PROGRESS.md` has the findings, including two claims from RESEARCH.md that a
real part disproved.
