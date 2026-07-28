# nurb

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

The build is now nearly all of the loop. Tessellation used to look like the larger half
at 620ms, and Phase 4 found that almost all of it was one iterator in build123d rather
than any geometry; `builder._triangulate` reads the same triangles by index in 30ms.
Write a continuous dimension as a float (`chamfer_size=1.0`) and a count as an int
(`bracket_count=4`): the viewer reads the type of the default to decide whether that
parameter's slider steps by one.

## Commands

```
nurb new <name>      create parts/<name>.py and its card
nurb dev             watch, rebuild, serve the viewer on :7373 or the next free port
nurb build [part]    build once, report size and timing
nurb check [part]    run the printability rules, --strict for CI
nurb rules           print the design doctrine
nurb skill           print an agent skill file for any AI harness
nurb card [part]     regenerate a card's AUTO block
nurb verify [part]   the doctrine's verification list, --strict-ish exit code
nurb render [part]   write build/<part>.png, needs the render extra
nurb export [part]   write STL and STEP into build/, --formats for GLB
nurb extract         find duplication across sibling parts
nurb launcher        write viewer.command, a double-clickable `nurb dev`
```

`uv run pytest` runs the suite, which includes the parts in `examples/`.

A project is any directory containing `parts/`. There is no init step, and there
never should be.

## Layout

```
src/nurb/registry.py      @part, signature introspection
src/nurb/builder.py       load, build, tessellate, GLB
src/nurb/checks.py        printability rules, convexity, Finding/Context, variants
src/nurb/printers.toml    shipped printer profiles, named by a project's printer.toml
src/nurb/card.py          the card's AUTO block
src/nurb/extract.py       duplication across sibling parts, up to alpha-equivalence
src/nurb/measurements.py  measured(), and the refusal to guess
src/nurb/edit.py          writes slider values back into a part's keyword defaults
src/nurb/render.py        headless PNG, the only module that wants a browser
src/nurb/doctrine.md      the doctrine itself, shipped in the package
src/nurb/server.py        watcher, rebuild, HTTP + websocket on one port
src/nurb/viewer.html      three.js viewer, Z-up, camera persistence, sliders, section
src/nurb/vendor/three/    three.js r169, so the viewer needs no network
src/nurb/cli.py           command surface
examples/notch/           the real parts, which are also the calibration set
tests/test_notch_fit.py   the hanging interface, asserted for every configuration
tests/                    rules and examples, both cases per rule
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

## Current state

Phases 1 through 5 are done. The whole Notch catalog lives in `examples/notch/`:
sixteen catalog entries out of thirteen part files and nineteen shipped configurations,
every one a single solid matching its Fusion bounding box, clean under
`nurb check --strict`, and watertight when exported.

`tests/test_notch_fit.py` is the hanging interface, asserted rather than read: every
channel floor on exact pitch, at full span, one per bracket and no more, for every
configuration. Its numbers are literals rather than imports from `system.py`, because a
fit test that reads the same constant the part built from agrees with the part however
wrong the constant is. A deliberate 0.1mm per interval pitch error is in the suite so
the assertion is known to be able to fail. 178 tests.

**Thirteen parts found rule bugs that three parts could not.** `concave_cosmetic` was
firing at the 2mm structural relief the doctrine prescribes for thin material, and
`bed_bevel` at the 45 degree corbel it prescribes for a raised feature. Both were
recalibrated against measurements, not opinions: a relief is wider than polish, and a
bottom chamfer rises by exactly its size where a corbel rises farther. `polish_edges` also
had a gap, allowing a sloped edge that reaches the bed. Every one was found by a part
rather than by review, which is the argument for `examples/` being the calibration set.

The agent surface is in: `nurb rules` prints the doctrine from `src/nurb/doctrine.md`,
`nurb card` regenerates each card's AUTO block from a build, `nurb render` screenshots the
viewer headlessly, and `measurements.toml` carries dimensions with their provenance.

`nurb extract` finds duplication across sibling parts up to alpha-equivalence and
reports it; it does not rewrite, because naming the thing is the judgement and noticing
is the mechanical part. Run over the finished port it found `system.slab()` in six files
at once.

The viewer has a slider per numeric parameter, inferred from the signature and nothing
else, a section view that caps its cut so a solid still reads as solid, and a button
that writes an exploration back into the file's defaults. three.js is vendored, so the
viewer and `nurb render` both work with no network.

**The live loop got about 20x faster in Phase 4, and not for a reason anyone would
guess.** `Shape.tessellate` reads its triangles with `for t in poly.Triangles()`, and
OCP's iterator over that array is pathological: 7790 triangles cost 536ms to iterate
and 6.8ms to read by index, against 10ms for the meshing itself. `builder._triangulate`
reads them by index and returns bit-identical geometry. Phase 1's recorded conclusion
that "tessellation is the loop" was measuring that iterator.

The README's original "not built yet" list is built. Printer profiles ship in
`src/nurb/printers.toml`, named once per project by `printer.toml` (`nurb check
--printer x` tries another machine). `min_wall` corrects its ray chords with an
inscribed sphere on exact kernel distances, gated so the sphere is only paid for where
it could change the verdict; the far contact gets the same 0.3 cosine floor as the
ray's exit filter, or a dimple's bowl reads as a thin wall (it did: 1.07mm in a 2.3mm
web on the scraper). And the viewer is the configurator: `stl`/`step` buttons build at
the slider values, polished, and hand back the file.
