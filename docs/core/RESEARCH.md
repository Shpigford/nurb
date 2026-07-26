# nurb core research

The central reference for nurb. Everything else pulls from here.

Status as of 2026-07-26: Phases 1, 2 and 3 complete. Two real Notch parts and a
calibration coupon build, match their Fusion originals dimension for dimension, run in the
live loop, and report clean against eight printability rules. The kernel question is
settled and the agent surface is in. See `PROGRESS.md` for the findings, several of which
correct claims made in this document before any real part existed; those corrections are
folded in below and marked.

## Overview

nurb is an agentic CAD runtime for 3D printing. A part is a Python function whose
keyword defaults are its parameters. A long-lived process watches part files,
rebuilds on save, and pushes geometry to a browser without disturbing the camera.
Printability rules run as assertions inside that loop.

The primary user is a language model. That single fact drives most of the design:
boring command names, geometry as diffable code, failures as tracebacks, and
correctness expressed as tests rather than as something a human eyeballs.

## Problem statement

Fusion is not the bottleneck people assume. Its actual costs, measured against a
real parts library (Notch, 16 parts on Wall Control brackets):

1. **It cannot run headless.** Every operation needs a GUI instance, the right
   document active, and an HTTP shim. No CI, no server, no web configurator.
2. **It is single-tenant.** One active document. Two agents working in parallel
   do not run slowly, they corrupt each other. This is a hard blocker on the
   parallel-agent workflow, not a performance concern.
3. **Its statefulness generates most of the accumulated pain** (see below).
4. **Verification is manual.** Fit checks live in prose on catalog cards and get
   confirmed by reading, not by running.

What Fusion genuinely provides is one thing: a robust B-rep kernel. That is
replaceable with OCCT via build123d, which is the same class of kernel.

## The central finding: most accumulated Fusion knowledge is not portable, because
## it describes problems that do not exist in code

The `fusion` skill is 219 lines of hard-won API facts. Roughly 80% of it documents
workarounds for a stateful timeline, and those workarounds should be **deleted, not
translated**. Porting them would import accidental complexity into a system that
never had the problem.

### Vanishes entirely

| Fusion pathology | Why it disappears |
|---|---|
| "Executions are NOT transactional, partial work persists" | A function returns a shape or raises. No partial state. |
| "Every build step must be idempotent, delete features by name first" | A pure function is idempotent by construction. |
| "After a failed feature add, clean up by TYPE, the wreckage is unnamed" | Nothing persists to clean up. |
| "A failure can LOSE earlier work, re-list the timeline after any failure" | No timeline. |
| "Combine tool lists never grow, pattern instances are ignored" | `a - b` consumes whatever you pass it. |
| "Combine-JOIN silently drops rectangular-pattern instance bodies" | No combine feature. |
| "Feature-patterning a Combine silently no-ops" | A `for` loop. |
| "Patterning a pattern works ONLY one level deep, ONLY 1-D" | Nested loops, arbitrary depth. |
| "16 fixed comb lobes because a `bracket_count`-driven pattern breaks combines" | `for i in range(bracket_count)`. The entire comb/web construction is a workaround and should not be ported. |
| "`deleteMe()` CASCADES silently" | No dependency graph to cascade through. |
| "Sketch axes are NOT the world axes you assume" | Explicit coordinates. |
| "Every sketch must end fully constrained" | No sketches. Parameters are variables. |
| "Derived parameters are read-only references" | `from nurb_notch.system import BLOCK_WIDTH`. |
| "Derived geometry is pinned to the saved source VERSION" | An import resolves at build time. |
| "A folder's `dataFiles` loads asynchronously" | Files on disk. |

**Practical consequence for the Notch port:** it is not a translation. `ChannelTool`,
the 16-lobe comb, `CombWeb`, `JoinComb`, the derive link, and the fixed over-count
are all Fusion scaffolding. The actual geometry is: a slab, N dovetail channels cut
at `k * block_width`, and part-specific features. Expect the port to be dramatically
shorter than the timelines suggest.

### Survives, because it is physics or geometry

- The entire 3D-print design doctrine (support-free, 45° corbels, load paths,
  gussets, projection ratios, polish rules). Printer behavior, not CAD behavior.
- Sliver faces under 1mm². Real geometry that prints badly.
- Chamfer size capped by the narrowest adjacent face. A geometric constraint.
- Chamfer ordering effects. Each chamfer changes topology, so selectors resolved
  against pristine geometry drift once an earlier chamfer runs. **This is an OCCT
  problem too** and is the single most likely source of port failures.
- Concave-edge detection. Note the recorded failure: the "offset midpoint along
  averaged face normals then test containment" trick classifies concave edges as
  convex. The correct test is cross-product based (below).

### Unknown, must be re-derived for OCCT

- Which chamfer configurations fail, and with what errors. Fusion's `ASM_BL_NO_MATE`
  / `ASM_BL_CAP_COMPLEX` / `ASM_BL_UNFIN_SHEET` have OCCT analogues that have not
  been characterized.
- Whether adjacent different-sized chamfers need a single multi-set operation the
  way Fusion does.
- Tessellation quality and sliver-face reporting on curved geometry.

## Measured facts

From the working runtime, on this machine (M-series arm64, Python 3.13):

```
import build123d          45.7s cold (bytecode compile), 2.28s warm
build + boolean            4ms
chamfer, 8 edges           6ms
tessellate (tol 0.1)      51ms
export STL                 3ms
export STEP               15ms
--------------------------------
everything after import   ~80ms
```

Two consequences, both load-bearing:

1. **The persistent process is mandatory, not an optimization.** A 2.3s import per
   rebuild would make the loop unusable. `nurb dev` pays it once.
2. ~~**Draft mode is worth more than expected.** On a trivial part, 18ms polished vs
   **1ms** draft. Chamfers are essentially the entire build cost.~~ **Wrong, corrected
   by Phase 1.** That held only for `Box() - chamfer()`. On the gridfinity shelf,
   chamfers are 23% of the build and draft mode saves 20%, not 18x.

### Corrected by Phase 1, on real parts

```
                     build    tessellate + GLB    loop
hook, polished        46ms          120ms        ~166ms
hook, draft           26ms           66ms         ~92ms
shelf, polished      470ms          620ms       ~1090ms
shelf, draft         380ms          520ms        ~900ms
```

Shelf build, by stage: socket lofts 156ms (34%), socket cut 68ms, cosmetic chamfer
66ms, structural chamfer 43ms, gussets 42ms, fuse 39ms, edge selection 26ms, channels
and detent 21ms.

**Tessellation costs more than the entire build, and draft mode barely touches it.**
The latency lever is tessellation tolerance, caching, or moving tessellation off the
rebuild path. It is not the polish pass. Anything that plans around draft mode as the
primary lever is planning around a measurement taken on a cube.

## Architecture

### Layers

```
1  kernel + language     build123d / OCCT          not ours
2  runtime               watch, build, cache, serve, render
3  checks                printability rules as assertions
4  agent interface       CLI contract, doctrine, cards, measurements
5  project systems       system.py, extracted not scaffolded
```

Layer 3 is the differentiated work. Layer 1 is a dependency. Layers 2 and 4 are
small but decide whether the thing is usable.

### The part contract

One convention carries everything:

```python
@part
def dispenser(width=80, height=120, wall=2, draft=False):
    ...
    return solid
```

Keyword defaults are the parameters. That single declaration serves five consumers:
the agent, the CLI, the viewer's future slider UI, the test suite, and any eventual
published configurator. `draft` is injected by the runtime, not passed by callers.

Rejected alternative: a separate `PARAMS` dict alongside the signature. It duplicates
the declaration and lets the two drift.

### Build pipeline

```
part file --importlib--> @part fn --call--> Shape --tessellate--> Trimesh --> GLB
                                                 \--export--> STL / STEP / 3MF
                                                 \--checks--> findings
```

Modules are loaded fresh per build via `spec_from_file_location` with a unique name,
then popped from `sys.modules`. `sys.dont_write_bytecode` is set during the import so
no `__pycache__` appears in the user's `parts/`.

### Transport

One port serves both the viewer and the websocket, using the `websockets` library's
`process_request` hook to short-circuit HTTP requests before the WS handshake. GLB is
served over HTTP at `/glb/<name>.glb?v=<token>` rather than pushed over the socket,
so large meshes do not become giant base64 frames and `GLTFLoader` can fetch by URL.
The socket carries only small JSON notifications.

## Printability rules (layer 3)

**Decision: checks run on the in-memory B-rep solid during the build loop**, not on
exported files. This gives real faces with exact areas and normals rather than
triangles, at the cost of only working inside the nurb stack.

The rule set is a direct encoding of the existing design doctrine. These are Josh's
standing rules, several of them vetoes rather than preferences.

### Rules with clear geometric definitions

| Rule | Definition | Threshold |
|---|---|---|
| `overhang` | Faces whose normal has a downward component, where the angle from vertical exceeds the limit | 45°, hard |
| `min_wall` | Thinnest section anywhere in the solid | 2mm (doctrine says 2-3mm) |
| `sliver` | Faces below an area threshold | 1mm², with a per-part accepted baseline |
| `chamfer_size` | Cosmetic chamfer dimension | 1mm default, never below 0.8mm |
| `back_bottom_chamfer` | Any chamfer on a face adjacent to the back plane or bed plane | forbidden |
| `mating_chamfer` | Any polish touching fit-critical geometry | forbidden |
| `concave_cosmetic` | Concave edge in the cosmetic pass | forbidden; concave junctions get a deliberate 3mm structural chamfer instead |
| `projection_ratio` | forward projection ÷ supporting height | ≤1.5 chamfers only; 1.5-2.5 end gussets; >2.5 raise height |
| `stability` | Center of mass outside the bed footprint | warn |
| `build_volume` | Bounding box vs printer | hard |
| `grounded` | Functional features must not float with a gap beneath | hard |
| `corbel_angle` | Underside support planes | exactly 45°, never ratio-matched |

### Implementation notes per rule

**Overhang.** Straightforward on B-rep: walk `solid.faces()`, take `normal_at()` on
each, keep faces where `normal.Z < 0`, compute the angle from `-Z`. Flag when it
exceeds 45°. Report area and whether the face is grounded. Planar faces are exact;
curved faces need sampling across the surface rather than a single normal.

**Minimum wall thickness.** The genuinely hard one. Two established approaches
([Oxford JCDE](https://academic.oup.com/jcde/article/2/3/183/5743362),
[Analysis Situs](https://analysissitus.org/features/features_thickness.html)):

- *Inscribed sphere*: thickness at a point is the diameter of the largest sphere
  contained in the solid touching the surface there. Correct in curved zones and
  inner corners. The locus of sphere centers is the medial surface. Expensive.
- *Ray casting*: shoot a ray inward along the inverted normal, measure to the first
  opposite surface. Cheap, good for nominally uniform walls, wrong at corners and
  on curves.

Recommendation: start with ray casting on a sampled subset of faces, since Notch
parts are overwhelmingly prismatic with uniform walls. Treat it as an approximation
and say so in the output. Do not promise inscribed-sphere accuracy from a ray cast.

**Sliver detection.** `[f for f in solid.faces() if f.area < 1.0]`. The only
acceptable tiny faces per doctrine are corner triangles where three 1mm chamfers
meet at a convex box corner, about 0.87mm². The gridfinity 2x2 shelf has a known
baseline of 18: 16 recess-corner segments at 0.63mm² (gridfinity spec geometry, four
per cell) plus 2 corner triangles at 0.87mm². **That baseline belongs in the part's
card as structured data**, so a new sliver is a regression and known ones stay silent.

**Concave edge detection.** Required by the polish rules, and the naive approach is
known to fail. Recorded in the Fusion skill: offsetting the edge midpoint along
averaged face normals and testing containment misclassifies concave edges as convex,
because for a concave edge the averaged normal also points into open space.

The correct test uses orientation rather than position. For edge `E` between faces
`F1` and `F2`, at a point `P` on `E` with face normals `n1`, `n2` and edge tangent
`t`: the sign of `(n1 × n2) · t` gives convexity, with the sign convention fixed by
the solid's outward orientation. Verify empirically against a part with known
concave junctions before trusting it, and unit-test both cases.

**Selectors make the exclusion rules tractable.** build123d's `ShapeList` API
supports `filter_by(GeomType)`, `filter_by(lambda)`, `group_by`, and `sort_by`, and
they chain. The doctrine's "exclude back face, bottom face, mating geometry, and
concave edges" becomes a composable declarative selector rather than the `tempId`
bookkeeping Fusion required. This is a genuine improvement over the source system,
not just parity.

### Calibration

**False positives are the entire credibility problem.** Every hobbyist knows their
printer bridges past the textbook 45°, and one wrong warning gets the tool
uninstalled. Two requirements:

1. Rules are per-printer and per-material, not global constants.
2. Distinguish "this will fail" from "this needs support." Different decisions.

The 16 Notch parts are an unusually good calibration set: designed, printed, known
outcomes, with expected values already recorded on their cards. **Any warning fired
against a part that printed fine is a bug in the rule.** Getting to zero false
positives across the existing library is the credibility bar and can be cleared
before showing anyone.

## Agent interface (layer 4)

### Distribution

Split by what is deterministic and what is prose.

- **Code** ships as a pip package with a CLI. `nurb`. This is the portable surface;
  agents drive CLIs natively in every harness.
- **Doctrine** ships *inside the package*, exposed as `nurb rules`. One source of
  truth. Per-harness files (`SKILL.md` for Claude Code, `AGENTS.md` for Codex and
  others) are thin shims that say "run `nurb rules` first."

**Explicitly rejected: an MCP server.** The existing Fusion MCP is the cautionary
case: its tools do not load into Claude Code natively, are absent from ToolSearch,
and required a hand-written HTTP client (`fmcp.py`) to be usable at all. A CLI with
good `--help` and good error text is more reliable and works everywhere.

### Command surface

Boring names, deliberately. An agent that has never seen the tool can guess `build`,
`check`, `export`. It cannot guess a themed alias. Every clever name is an
indirection that degrades in a fresh context.

```
nurb new <name>      create parts/<name>.py and its card
nurb dev             watch, rebuild, serve
nurb build [part]    build once
nurb check [part]    run rules, honor the card's accepted baseline
nurb export [part]   STL / STEP / 3MF / GLB into build/
nurb extract         pull duplication out of sibling parts into system.py
nurb rules           print the doctrine
nurb card [part]     regenerate the AUTO block
nurb render [part]   PNG into build/, so an agent can look at what it made
```

A project is any directory containing `parts/`. There is no init step.

### Context recovery

An agent opening a part cold needs four things:

1. **The code** (what)
2. **The card's design notes** (why the dimensions are what they are)
3. **`## Don't`** (what was tried and rejected)
4. **The accepted-warnings baseline** (which findings are known and fine)

Plus `measurements.toml` for the provenance of real-world numbers. **TOML, not YAML,
decided in Phase 3:** `tomllib` is in the standard library and cards already use a TOML
fence, so YAML would have meant a fifth dependency and a second format for one small file.

Card structure, carried over from the working Notch pattern:

- **AUTO block**, regenerated from the build. Never hand-edited. A cache, not a source of
  truth. **Phase 3 narrowed what goes in it:** bbox, volume, solid and face counts, sliver
  count against the accepted baseline, projection ratio, check verdict. Not the
  parameters, because the signature is the parameters and a generated restatement is the
  `PARAMS` dict the contract forbids. Not fit checks, because "channel floors at x=-4.2"
  is Notch and `src/nurb/` should not know what a channel is; those are Phase 5 tests.
  No timestamp, so the block is idempotent.
- **Narrative**: `## What it is`, `## Design notes`, `## Don't`, `## Changelog`.

**`## Don't` is promoted to a required section.** It is the highest-value content in
the existing cards and is currently incidental. Without it an agent helpfully re-adds
the lead-in chamfer that was deliberately retired on 2026-07-22. Geometry records
what is; only the card records what was tried and rejected.

Cards are colocated with parts and share a basename. That is the entire linking
mechanism, replacing Fusion's URN anchor plus back-pointer attribute plus
`sync_card.py` bridge. A rename is `git mv` on two files.

### Measurement capture

The real bottleneck on one-offs is not geometry, it is dimensions. The burrito
dispenser needs the burrito's size and the freezer shelf depth. An agent cannot
measure, and a wrong number produces a perfect model of the wrong object.

Notch paid this cost once (25.16mm bracket pitch, measured off a real wall) and has
amortized it across 16 parts. One-offs pay it every time. So measurement capture
should be a first-class step: `measurements.toml` holding named values with
provenance, which the agent asks for before building rather than improvising.

**Built in Phase 3.** `measured("name")` reads it, and the load-bearing part is what
happens when the name is not there: it raises, naming what is on file. Provenance is
required too, since a value with no `how` is a guess with a filename on it.

## Systems (layer 5)

**Systems are extracted, never scaffolded.** Notch did not begin as a system;
`block_width = 25.16` exists because a real wall got measured after parts existed.
Scaffolding `system.py` on day one means guessing what is shared before you know,
and the wrong abstraction propagates.

So the command is `nurb extract`, not `nurb new system`. It does work (find
duplication across sibling parts, lift it, rewrite imports) rather than creating
empty files.

### Notch constants, for the port

Owned by the system module. Never redefined per part.

```
block_width        25.16 mm   bracket pitch on-center, measured
clearance           0.2 mm    slide-fit per side
pocket_width       20.56 mm   bracket plate width at the item
pocket_depth        4 mm      channel depth into the item
pocket_neck_width  12.16 mm   dovetail opening at the back face
top_margin          3 mm      solid material above channel ceiling
pitch_slop          0.12 mm   per-interval scatter allowance
bracket height     25 mm      physical, drives min item_height = 28
```

**Those are the bracket pocket, not the channel.** Phase 1 read the shipped
`ChannelTool` off the live Fusion model and the channel is the pocket plus clearance
that differs by axis: **0.2mm in depth, 0.5mm per side in width.** Nothing in the
notes said so, and deriving the channel from the table alone produces one a
millimeter too tight. The channel that ships is a trapezoid, floor at `x=-4.2`
spanning `y` +/-10.78, mouth at `x=0` spanning +/-6.58, ceiling at `z=-3`. Its walls
are therefore at exactly 45 degrees, which is what lets the dovetail print without
support. `examples/notch/system.py` holds it.

Coordinate convention: slab top at `z=0` (part extends down), back face at `x=0`
(part extends forward in `-x`), first channel centered at `y=0`, channels marching
`+y` at `block_width` spacing. Landing those three datums makes the hanging
interface correct automatically.

Anti-lift detent: a ramped wedge on the shared bracket plate (0.5mm proud, 7mm below
the plate top, ramped top and bottom because a flat protrusion is an unprintable
overhang) plus a mating dimple in each channel floor at `z=-10`, 0.8mm past the
`x=-4.2` floor.

Fit assertions for the test suite: channel floors at `x=-4.2`, y-centers exactly
`k * 25.16` for `k` in `0..bracket_count-1`, no extra floor face beyond
`bracket_count`, no floor with a stunted y-span.

## Viewer and UX

### Built and verified

- Z-up scene matching CAD convention, orbit/pan/zoom, XY grid as the build plate
- Part list with per-part build times and error state
- **Camera survives rebuilds.** A rebuild is a geometry swap, never a camera reset.
  Verified by parking the camera and diffing after a rebuild.
- Camera persists per part to `localStorage`, so reloads restore it
- Reframe is an offered button, not automatic, and appears only when the bounding
  box changes by more than 3x (below that the camera is still pointed at the part)
- Build errors show a traceback trimmed to the user's file, keep the last good
  geometry visible at 22% opacity, and clear on the next good build

### Bugs found during the build, worth not repeating

1. **Black render.** trimesh welded a box down to 8 shared corners and dropped the
   normal attribute, leaving the shader nothing to light. Fix: `process=False` on
   the `Trimesh` constructor. OCCT already splits vertices at face boundaries, which
   is the correct layout (crisp edges on flats, smooth on curves), and letting
   trimesh weld them destroys it. Also touch `mesh.vertex_normals` before export or
   the GLB ships without normals.
2. **Hot reload silently dead.** Both the watchdog `Observer` and the asyncio drain
   task were created without holding a reference. asyncio keeps only weak references
   to tasks. Fails by never firing, with no error.
3. **Canvas stacking.** Fixing a ResizeObserver feedback loop by making the canvas
   `position: absolute` turned it into a positioned element appended after the
   overlay divs, so it painted over the HUD. Overlays need explicit `z-index`.

### Not built

- Parameter sliders driven by the same keyword defaults. Nearly free given the
  contract, and it is the feature that makes the tool feel consumer-grade: drag
  `item_height`, watch it rebuild. Effectively a local version of MakerWorld's
  customizer, available during design rather than after publishing.
- ~~Headless PNG render so an agent can see its own work.~~ **Built in Phase 3**, the way
  this predicted: Playwright against the existing viewer at `?part=x&view=iso`, on a
  server the render starts itself. Playwright is an optional extra rather than a
  dependency. The headless shell renders WebGL 2.0 through SwiftShader, so no offscreen
  GL stack and no browser channel pin were needed.
- Section view, measurement tools.
- Vendored three.js. Currently loaded from unpkg via importmap, so the viewer needs
  network. A CAD tool should work offline. **Phase 3 raised the stakes on this:**
  `nurb render` drives the same page, so it fails closed without network. Measured with
  unpkg blocked: the page loads, the canvas exists, three.js never arrives, nothing is
  ever drawn.

## Risks

**Ranked by how much they threaten the thesis.** Ranks 1, 2 and 5 were resolved by
Phase 1 and are kept here with their outcomes, since the outcomes are the useful part.

1. ~~**OCCT chamfer robustness on real geometry. Untested.**~~ **Resolved. OCCT
   handles it.** Both parts build, the shelf reproduces its 18-face sliver baseline
   exactly, and the geometry matches the Fusion originals dimension for dimension.
   One rule accounts for every failure encountered: **two chamfered convex edges need
   more than `2 * chamfer_size` of face between them**, or OCCT raises
   `BRep_API: command not done`. That is the `ASM_BL_NO_MATE` analogue. Fusion's
   gusset-peak workaround was the same constraint at a smaller threshold.

   The trap: **every edge chamfers fine individually; only the batch fails.** Checking
   edges one at a time reports that nothing is wrong. Bisect the set pairwise.
2. ~~**Rebuild latency on real parts.**~~ **Resolved, and the answer is not the one
   assumed.** Build is 470ms on the shelf, but tessellation is another 620ms, so the
   loop is ~1.1s. Tessellation is the critical path and draft mode does not address
   it. See the measured facts above.
3. **False positives in the rules.** Kills adoption faster than missing checks. Two
   calibration parts now exist with exact baselines.
4. **Concave edge detection.** Required by the polish rules, known to have a subtle
   failure mode, must be verified empirically rather than reasoned about. Phase 1
   sidestepped it by subtracting `new_edges` from the polish set, which works only
   because those parts' sole concave edges are the ones the structural pass made.
5. ~~**Chamfer selector drift.**~~ **Resolved.** `new_edges(before, combined=after)`
   returns exactly what an operation created, and is the algebra-mode `Select.LAST`.
   Both parts flex `bracket_count` in both directions with baselines unchanged. This
   is genuinely better than Fusion's strict-ordering rule, not just parity.
6. **three.js CDN dependency.** Offline breaks the viewer.

## Open questions

- ~~Does `nurb check` gate `nurb export`, or only report?~~ **Answered in Phase 2:**
  report only, with `--strict` for CI.
- ~~Do accepted-warnings baselines live in the card's AUTO block or a separate
  `.check.yaml`?~~ **Answered in Phase 2 and 3:** neither. They sit in a hand-authored
  TOML fence in the card, next to the sentence that justifies them, and the AUTO block is
  a separate generated region that prints the measured count beside the accepted one. The
  churn worry was real and is solved by the block carrying no timestamp, so regenerating
  it produces no diff unless the geometry moved.
- Does the port target one part per file, or does a family (gridfinity 2x1, 2x2,
  3x2) become one file with different defaults? The three gridfinity shelves are the
  same part flexed, which argues for one parameterized file and separate export
  configs.
- Printer profiles: shipped defaults, or user-authored from the start?
- Is `nurb` also the name of the published PyPI package, given `nurb` is free there
  today, or does the package become `nurb-cad` with `nurb` as the console script?

## References

- [build123d documentation](https://build123d.readthedocs.io) — selectors, chamfer,
  export. Confirmed: `filter_by(GeomType)`, `filter_by(lambda)`, `group_by`,
  `sort_by`, and normal-based face filtering, all chainable.
- [Thickness and clearance visualization based on distance field of 3D objects](https://academic.oup.com/jcde/article/2/3/183/5743362) — inscribed sphere and medial surface
- [Analysis Situs: thickness distribution](https://analysissitus.org/features/features_thickness.html) — ray casting vs sphere, sampling for speed
- [MakerWorld Parametric Model Maker](https://all3dp.com/4/bambu-labs-parametric-model-maker-brings-openscad-to-makerworld/) — the customizer runs OpenSCAD; relevant to eventual publishing
- Local: `~/.claude/skills/fusion/SKILL.md` (design doctrine, API pathologies),
  `~/.claude/skills/notch/SKILL.md` (system constants, recipe, verification),
  `~/.claude/skills/notch/catalog/` (16 part cards with parameters and baselines)
