# nurb

Agentic CAD for 3D printing.

A part is a Python function. Its keyword defaults are its parameters. `nurb dev`
watches your parts, rebuilds them on save, and pushes new geometry to a browser
without moving your camera.

Built on [build123d](https://build123d.readthedocs.io) (OCCT), so parts are real
B-rep solids with working chamfers, fillets, and STEP export.

## Try it

```bash
uv run nurb new dispenser
uv run nurb dev            # http://127.0.0.1:7373, or the next free port
```

Edit `parts/dispenser.py` and watch it update.

## A part

```python
from nurb import *

@part
def dispenser(width=40, depth=30, height=20, wall=2, draft=False):
    body = Box(width, depth, height)
    if not draft:
        body = chamfer(body.edges().filter_by(Axis.Z), length=1)
    return body
```

`draft` is optional and passed by the runtime, not the caller. When it's true the
part should skip its polish pass. `nurb dev` builds in draft by default: on this
trivial part it's 18ms polished vs 1ms draft, and on a real one the saving is
nearer 20%.

## Commands

```
nurb new <name>     create parts/<name>.py and its card
nurb dev            watch, rebuild, serve the viewer
nurb build [part]   build once and report size
nurb check [part]   run the printability rules
nurb rules          print the design doctrine
nurb card [part]    regenerate a card's AUTO block
nurb render [part]  write a PNG into build/
nurb export [part]  write STL/STEP/GLB into build/
nurb extract        find duplication across parts
```

A project is any directory with a `parts/` folder. There's no init step, and there's
no such thing as being outside a project: `mkdir -p thing/parts && cd thing && nurb new
clip` is the whole setup for a one-off.

`nurb dev` serves one project, so two projects means two of them. It takes 7373 if that
is free and walks up if it is not, printing where it landed, and the sidebar and the
browser tab both carry the project name so two of them are not mistakable for each
other.

Names are deliberately boring. The primary user is a language model, and a model that
has never seen this tool can guess `build`, `check` and `export`. It cannot guess a
themed alias.

## Why a long-lived process

Importing build123d costs 45s cold and 2.3s warm, and that is the whole argument: the
dev server pays it once instead of on every save.

What a rebuild costs after that depends on the part. A simple one is 29ms to build and
1ms to tessellate. The heaviest part in `examples/` is 401ms and 30ms. Draft mode is
not the lever it looks like: chamfers are 23% of that build, not most of it.

Tessellation used to be the larger half, at 620ms on that part, and almost none of it
was geometry. `Shape.tessellate` reads its triangles with `for t in poly.Triangles()`,
and OCP's iterator over that array costs 536ms where reading the same 7790 triangles by
index costs 6.8ms. `builder._triangulate` does the latter and returns bit-identical
vertices and faces. It is worth knowing before optimising the wrong thing.

## Layout

```
parts/<name>.py     the part
parts/<name>.md     its card: what it is, why, what not to retry
system.py           optional: shared constants and geometry, importable from a part
measurements.toml   optional: real-world dimensions with how they were obtained
build/              generated, gitignored
```

Cards are colocated with parts and share a basename. That's the whole link; a
rename is `git mv` on two files.

## Checks

`nurb check` runs the printability rules against the solid rather than an exported
mesh, so it sees real faces with exact areas and normals instead of triangles.

```
overhang          downward faces past 45 degrees, bridges told from cantilevers
min_wall          thinnest section, by ray cast
sliver            faces too small to print as anything but a smear
concave_cosmetic  polish laid into an inside corner
bed_bevel         polish laid on the edges that meet the build plate
stability         center of mass outside the footprint
projection_ratio  reach over height, for a part cantilevered off a wall
build_volume      does it fit the printer at all
```

Every part carries what it has already justified on its card, so a known finding is
silent and a new one is a regression:

```toml
[part]
min_wall = 1.0

[accepted]
sliver = 6
```

It reports by default and takes `--strict` for CI, on the grounds that a warning which
blocks work gets switched off. Findings also show up in `nurb dev`, with a pin on the
geometry at each one.

## Variants

Some parts in a catalog are the same function flexed rather than new geometry. Those
ship as variants on the card, not as copies of the file:

```toml
[variants.shelf_gridfinity_3x2.params]
grid_x = 3
bracket_count = 6

[variants.shelf_gridfinity_3x2.accepted]
sliver = 26
```

`build`, `check`, `card` and `export` all walk a part's variants the same way they walk
its default, so a variant gets its own STL, its own baselines and its own line in the
card's generated block. Four of the sixteen parts in `examples/notch` are variants; the
alternative was four near-copies of two files, free to drift.

## For an agent

The doctrine lives in the package and prints with `nurb rules`: printability, load paths,
the polish pass, the kernel traps, and what to verify. `SKILL.md` and `AGENTS.md` are ten
lines each pointing at it, so there is one copy and it cannot drift.

A part explains itself in a card next to it, same basename. Most of it is written by
hand, including a `## Don't` section that records what was tried and rejected, which is
the only place that information exists. One fenced block is generated:

```
nurb card
```

That block holds what only a build can tell you: bounding box, volume, solid count,
sliver count against the accepted baseline, projection ratio, check verdict. It carries
no timestamp, so regenerating it on unchanged geometry produces no diff and a stale card
shows up in `git diff`. It deliberately does not repeat the parameters, because the
signature is the parameters and copying them would be the drift the contract forbids.

Dimensions an agent cannot derive go in `measurements.toml` with how they were obtained:

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

Asking for something that isn't there raises and says so. That failure is the point: a
guessed dimension produces a part that builds, checks clean, and prints.

`nurb render <part>` writes `build/<part>.png` by screenshotting the viewer, so the image
is what a human would see. It needs the optional extra, which is the only part of nurb
that wants a browser:

```
uv sync --extra render && uv run playwright install chromium
```

## Tests

```
uv run pytest
```

The parts in `examples/` are part of the suite, asserted against the dimensions and
baselines their catalog cards recorded in Fusion. `tests/test_notch_fit.py` is the
hanging interface: every channel floor on exact pitch, at full span, one per bracket and
no more, for every shipped configuration. Its numbers are literals rather than imports
from the part's own constants, because a fit test that reads the same constant the part
built from agrees with the part however wrong the constant is.

## Not built yet

- `min_wall` is a ray cast, so it is exact on flat parallel walls and approximate
  everywhere else. An inscribed sphere is the correct answer and an expensive one.
- Printer profiles, shipped rather than written per card
- A configurator: a part's parameters are already introspectable, so the missing piece
  is publishing, not modelling

## Debugging the viewer

`window.__nurb` exposes `{ THREE, scene, camera, controls, mesh, ready }`.

The URL takes `?part=<name>` to open a part, `?view=iso|front|back|left|right|top` to
frame it deterministically, and `?bare` to hide the chrome. `nurb render` drives exactly
that, and waits on `ready`.

three.js is vendored in `src/nurb/vendor/three`, so the viewer needs no network. See the
README beside it before changing versions: the import graph has grown since r169 and the
files it added fail as a blank canvas rather than as an error.

## License

[FSL-1.1-MIT](LICENSE). Source-available for any purpose except building a competing
product, and converts to plain MIT two years after each release.

Copyright 2026 Ordinary Systems LLC.

### Third-party notices

nurb uses **Open CASCADE Technology** (OCCT) for all B-rep geometry, reached through
[build123d](https://github.com/gumyr/build123d) (Apache-2.0) and the `OCP` bindings
(Apache-2.0). OCCT is licensed under
[LGPL-2.1 with an additional exception](https://dev.opencascade.org/resources/licensing).

nurb does not redistribute OCCT. It is installed separately as a dependency, and
dynamically linked at runtime. If you ever bundle nurb into a single-file
distribution that embeds the OCCT binaries, ship a copy of the OCCT license with it
and keep the library replaceable, per LGPL.

nurb **does** redistribute [three.js](https://threejs.org) r169 (MIT), vendored in
`src/nurb/vendor/three` so the viewer works without a network. Its `LICENSE` ships
beside it and the `@license` header stays on the build file, which is what MIT asks for.

Other dependencies: trimesh (MIT), watchdog (Apache-2.0), websockets (BSD-3-Clause),
numpy (BSD-3-Clause). Optional, for `nurb render` only: playwright (Apache-2.0), which
downloads its own browser build.
