# nurb

Agentic CAD for 3D printing. The user is a language model.

You describe a part to your agent. It writes a Python function, nurb builds that
into a real solid, checks it against print physics, and pushes the geometry to
your browser. You look at the thing, drag a slider, download the STL. The agent
never sees the screen, never holds a mouse, and forgets everything between
sessions, and every design decision in nurb exists to serve exactly that user.

Built on [build123d](https://build123d.readthedocs.io) (OCCT), so parts are real
B-rep solids with working chamfers, fillets, and STEP export, not meshes.

## Install

nurb is on [PyPI](https://pypi.org/project/nurb/):

```bash
uv tool install nurb       # or: pip install nurb
uvx nurb rules             # or run it without installing anything
```

PyPI is the only install channel, because nurb is Python driving a C++ kernel
and there is no JavaScript to ship.
[`@shpigford/nurb`](https://www.npmjs.com/package/@shpigford/nurb) exists as a
signpost: `npx @shpigford/nurb` tells you the two commands above instead of
leaving `npx` users at a 404. (npm blocks the unscoped name for everyone as too
similar to existing packages.)

## Give it to your agent

```bash
nurb new dispenser         # a working part and its card
nurb dev                   # http://127.0.0.1:7373, or the next free port
```

(Working from a checkout of this repo, prefix commands with `uv run`.)

Then tell your agent what you want and let it run `nurb rules`. That prints the
design doctrine: the printability rules, the load-path patterns, the kernel
traps, and what to verify before claiming a part works. It ships inside the
package, and a project's `SKILL.md` and `AGENTS.md` are ten lines pointing at
it, so there is one copy and it cannot drift. `nurb new` seeds that pointer into
a fresh project, which is the difference between an agent that uses the tool and
one that reads two Python files, decides this is an ordinary build123d script,
and never learns the tool exists.

The rest of the interface follows from the same user:

- **Command names are boring on purpose.** A model that has never seen nurb can
  guess `build`, `check`, and `export`. It cannot guess a themed alias, and
  every clever name is an indirection that degrades in a fresh context.
- **Errors are the interface.** Most sessions meet nurb for the first time
  through a failure, so tracebacks are trimmed to the agent's own file and
  messages say what to do next, never just "invalid input". Asking for a
  measurement that does not exist raises. A part refusing an impossible
  parameter refuses in its own words.
- **Generated files are nearly empty.** Scaffolders traditionally emit commented
  placeholder blocks. For an agent that is context to read past, so `nurb new`
  emits a working part and a card with headings only.
- **A project is any directory with a `parts/` folder.** There is no init step,
  no config, no state an agent has to discover: `mkdir -p thing/parts` is the
  whole setup, and every command works from anywhere inside.

## A part

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

That signature is the entire interface. **The keyword defaults are the
parameters**: one declaration feeds the agent, the CLI, the viewer's sliders,
the tests, and the export buttons, so there is no schema to keep in sync with
the code and nowhere for the two to drift apart. A model reads the whole state
of a part by reading its file, which is the point: no GUI timeline, no feature
tree, no kernel session that has to be replayed to be understood.

The type of a default is its annotation. Write a continuous dimension as a float
(`chamfer_size=1.0`) and a count as an int (`bracket_count=4`), and the slider
knows whether to step by one.

`draft` is optional and passed by the runtime, not the caller. When it's true the
part should skip its polish pass. `nurb dev` builds in draft by default: on this
trivial part it's 18ms polished vs 1ms draft, and on a real one the saving is
nearer 20%.

## The agent cannot see, so the checks are its eyes

A model can reason about geometry and still ship a part that snaps at a thin
wall or prints as spaghetti past a 45 degree overhang, because it never looks at
the thing. `nurb check` is the substitute for looking. It runs against the
in-memory solid rather than an exported mesh, so it sees real faces with exact
areas and normals instead of triangles, and every finding comes back as text
with a coordinate, which is the form a model can act on:

```
overhang          downward faces past 45 degrees, bridges told from cantilevers
min_wall          thinnest section, ray cast corrected by an inscribed sphere
sliver            faces too small to print as anything but a smear
concave_cosmetic  polish laid into an inside corner
bed_bevel         polish laid on the edges that meet the build plate
stability         center of mass outside the footprint
projection_ratio  reach over height, for a part cantilevered off a wall
build_volume      does it fit the printer at all
```

`min_wall`'s ray is exact on flat parallel walls and measures the slant through a
skewed one, so any chord thin enough to change the verdict is corrected by the
largest sphere tangent at that point, computed against the solid with exact
kernel distances. A sphere whose far contact is a graze rather than a wall is
rejected by the same 0.3 cosine floor the ray's exit filter uses, which is what
keeps a detent dimple's bowl from reading as a thin section of the web it is
pressed into.

The bed size belongs to the machine, not to a part, so it is not written on
cards. A project picks a shipped profile once, in `printer.toml` at the root:

```toml
profile = "bambu_a1_mini"
```

Any check setting can be overridden in the same file, machine-wide. A card still
wins for what its part has justified. `nurb check --printer prusa_mk4s` answers
"does this fit that machine" without touching the file, and naming a profile
that does not exist lists the ones that do.

Every part carries what it has already justified on its card, so a known finding
is silent and a new one is a regression:

```toml
[part]
min_wall = 1.0

[accepted]
sliver = 6
```

It reports by default and takes `--strict` for CI, on the grounds that a warning
which blocks work gets switched off. Findings also show up in `nurb dev`, with a
pin on the geometry at each one.

And when text is not enough, `nurb render <part>` writes `build/<part>.png` by
screenshotting the real viewer, so the agent can look at exactly what a human
would see and catch the failure no rule measures: a part that is wrong on
purpose it cannot articulate. It needs the optional extra, which is the only
part of nurb that wants a browser:

```
uv sync --extra render && uv run playwright install chromium
```

## The next session knows nothing, so parts carry their memory

An agent's context dies with its session. What survives is what got written
down, so every part gets a card next to it, same basename, and the card is where
the part explains itself months later. Most of it is hand-written, including a
`## Don't` section recording what was tried and rejected, which is the only
place that information exists and the only thing standing between the next
session and cheerfully re-adding the chamfer that was deliberately retired. One
fenced block is generated:

```
nurb card
```

That block holds what only a build can tell you: bounding box, volume, solid
count, sliver count against the accepted baseline, projection ratio, check
verdict. It carries no timestamp, so regenerating it on unchanged geometry
produces no diff and a stale card shows up in `git diff`. It deliberately does
not repeat the parameters, because the signature is the parameters and copying
them would be the drift the contract forbids.

Models guess fluently, and a guessed dimension is the worst failure in CAD: the
part builds, checks clean, prints, and does not fit. So dimensions an agent
cannot derive go in `measurements.toml` with how they were obtained, and asking
for one that is not there raises instead of estimating:

```toml
[bracket_pitch]
value = 25.16
unit = "mm"
how = "on-center spacing across a run of brackets, measured on the wall"
```

```python
from nurb import measured
pitch = measured("bracket_pitch")
```

Shared geometry is extracted, never scaffolded. `nurb extract` finds what
sibling parts say twice, up to renamed variables, and reports it rather than
rewriting, because choosing what the shared thing is called is a judgement and
noticing it is the only mechanical part.

## The loop is a session cost, so the loop is fast

An agent works in save-check cycles, dozens per part, so the loop's latency is
multiplied by everything. Importing build123d costs 45s cold and 2.3s warm, and
that is the whole argument for `nurb dev` being a long-lived process: it pays
the import once instead of on every save.

After that, a simple part rebuilds in 29ms and tessellates in 1ms; the heaviest
part in `examples/` is 401ms and 30ms. Draft mode is not the lever it looks
like: chamfers are 23% of that build, not most of it. Tessellation used to be
the larger half, at 620ms, and almost none of it was geometry: OCP's iterator
over the triangle array costs 536ms where reading the same 7790 triangles by
index costs 6.8ms. `builder._triangulate` does the latter and returns
bit-identical vertices and faces. It is worth knowing before optimising the
wrong thing.

## Commands

```
nurb new <name>     create parts/<name>.py and its card
nurb dev            watch, rebuild, serve the viewer
nurb build [part]   build once and report size
nurb check [part]   run the printability rules
nurb rules          print the design doctrine
nurb card [part]    regenerate a card's AUTO block
nurb verify [part]  run the doctrine's verification list
nurb render [part]  write a PNG into build/
nurb export [part]  write STL and STEP into build/, --formats for GLB
nurb extract        find duplication across parts
```

`nurb dev` serves one project, so two projects means two of them. It takes 7373
if that is free and walks up if it is not, printing where it landed, and the
sidebar and the browser tab both carry the project name so two of them are not
mistakable for each other.

## Layout

```
parts/<name>.py     the part
parts/<name>.md     its card: what it is, why, what not to retry
system.py           optional: shared constants and geometry, importable from a part
measurements.toml   optional: real-world dimensions with how they were obtained
printer.toml        optional: which machine this project prints on
build/              generated, gitignored
```

Cards are colocated with parts and share a basename. That's the whole link; a
rename is `git mv` on two files.

## Variants

Some parts in a catalog are the same function flexed rather than new geometry.
Those ship as variants on the card, not as copies of the file:

```toml
[variants.shelf_gridfinity_3x2.params]
grid_x = 3
bracket_count = 6

[variants.shelf_gridfinity_3x2.accepted]
sliver = 26
```

`build`, `check`, `card` and `export` all walk a part's variants the same way
they walk its default, so a variant gets its own STL, its own baselines and its
own line in the card's generated block. Four of the sixteen parts in
`examples/notch` are variants; the alternative was four near-copies of two
files, free to drift.

## The human's seat is the viewer

The division of labor: the agent models, the human judges. `nurb dev` is where
the judging happens, and it is also the configurator. A rebuild swaps the
geometry without moving your camera, so watching an agent iterate does not cost
you your viewpoint. The sliders come from the part's signature and nothing
else, the section view cuts the solid open without lying about it being solid,
and the `stl` and `step` buttons build the part at whatever the sliders are
holding, at full polish whatever the preview economy.
What is on screen is what lands in the slicer. A button writes an exploration
back into the file's keyword defaults, which is the human handing the result
back to the agent in the one place the agent will look. Point somebody at your
`nurb dev` and they can configure and download a part without touching Python.

## Tests

```
uv run pytest
```

The parts in `examples/` are the calibration set, asserted against the
dimensions and baselines their catalog cards recorded in Fusion, from parts
that were really printed. `tests/test_notch_fit.py` is
the hanging interface: every channel floor on exact pitch, at full span, one per
bracket and no more, for every shipped configuration. Its numbers are literals
rather than imports from the part's own constants, because a fit test that reads
the same constant the part built from agrees with the part however wrong the
constant is. That discipline exists for the same reason as everything else here:
the code was written by a model, and a model's tests love to agree with its
code.

## Not built yet

- A hosted configurator. `nurb dev` already is one for anybody who can reach it,
  but publishing without a running kernel is a different problem: MakerWorld's
  customizer runs OpenSCAD, which build123d does not transpile to.
- Measurement tools in the viewer. The section view shows an interior; it does
  not yet measure it.
- `min_wall` probes sample faces, so a pinch nothing lands near is still missed.
  A clean result means "no thin walls found", not "no thin walls".

## Debugging the viewer

`window.__nurb` exposes `{ THREE, scene, camera, controls, mesh, ready }`.

The URL takes `?part=<name>` to open a part, `?view=iso|front|back|left|right|top`
to frame it deterministically, and `?bare` to hide the chrome. `nurb render`
drives exactly that, and waits on `ready`.

three.js is vendored in `src/nurb/vendor/three`, so the viewer needs no network.
See the README beside it before changing versions: the import graph has grown
since r169 and the files it added fail as a blank canvas rather than as an error.

## License

[FSL-1.1-MIT](LICENSE). Source-available for any purpose except building a
competing product, and converts to plain MIT two years after each release.

Copyright 2026 Ordinary Systems LLC.

### Third-party notices

nurb uses **Open CASCADE Technology** (OCCT) for all B-rep geometry, reached
through [build123d](https://github.com/gumyr/build123d) (Apache-2.0) and the
`OCP` bindings (Apache-2.0). OCCT is licensed under
[LGPL-2.1 with an additional exception](https://dev.opencascade.org/resources/licensing).

nurb does not redistribute OCCT. It is installed separately as a dependency, and
dynamically linked at runtime. If you ever bundle nurb into a single-file
distribution that embeds the OCCT binaries, ship a copy of the OCCT license with
it and keep the library replaceable, per LGPL.

nurb **does** redistribute [three.js](https://threejs.org) r169 (MIT), vendored
in `src/nurb/vendor/three` so the viewer works without a network. Its `LICENSE`
ships beside it and the `@license` header stays on the build file, which is what
MIT asks for.

Other dependencies: trimesh (MIT), watchdog (Apache-2.0), websockets
(BSD-3-Clause), numpy (BSD-3-Clause). Optional, for `nurb render` only:
playwright (Apache-2.0), which downloads its own browser build.
