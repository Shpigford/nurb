# nurb core implementation plan

Derived from `docs/core/RESEARCH.md`. Five phases, roughly half a day each.

## Overview

The runtime skeleton exists and works on trivial geometry. This plan takes it to a
system that can hold the Notch library, check its own output, and be driven by an
agent in a fresh session.

Phase order is set by risk, not by convenience. The kernel proof comes first because
every downstream decision assumes OCCT can build these parts, and that assumption is
currently untested.

## Prerequisites

Already in place:

- `nurb new / dev / build / export` working
- Live rebuild loop verified, camera survives rebuilds
- Errors surface as trimmed tracebacks with stale geometry retained
- Draft mode wired through the part contract

Needed before Phase 1:

- [ ] Commit the current tree (no restore point exists today)
- [ ] Decide where the Notch port lives (see Phase 1, first task)

## Technical findings that shape the plan

Confirmed against current build123d docs, so future sessions do not re-derive them:

- **`loft()`** works over a stack of sketches on parallel planes. This is how the
  gridfinity socket's z-profile gets built (mouth, 45° chamfer, vertical, 45°
  chamfer, floor, clearance recess), replacing Fusion's four-feature construction.
- **`GridLocations(x_spacing, y_spacing, x_count, y_count)`** natively replaces
  `SocketArray`. No pattern feature, no instance counting, no seed-inclusion trap.
- **`Select.LAST` and ShapeList set-difference** (`part.edges() - last`) select
  exactly the edges an operation just created. This is a materially better answer
  to chamfer-selector drift than Fusion's "cosmetic on pristine geometry first,
  then structural" ordering rule. Prefer it wherever a chamfer targets the output
  of a known step.
- **Algebra mode** (`part = Part() + Box(...)`, `part -= Hole(...)`) suits a
  function that returns a shape better than builder-context mode.

## Phase summary

| # | Phase | Delivers |
|---|---|---|
| 1 | Kernel proof: port the hardest Notch part | Two real, printable Notch parts in the live loop |
| 2 | `nurb check`: the rules engine | Real findings on real parts, zero false positives |
| 3 | Agent interface | A fresh agent session can work a part correctly |
| 4 | Viewer and human UX | Drag a parameter, watch it rebuild |
| 5 | Full port, extract, tests | Whole Notch library in nurb, CI-checkable |

---

## Phase 1: Kernel proof

### Objective

Prove OCCT can build real Notch geometry, and establish the patterns every later
part follows.

### Rationale

Everything measured so far comes from `Box() - chamfer()`. The gridfinity 2x2 shelf
is the hardest part in the library and already fights Fusion's kernel: its gusset
peak lands exactly on the slab-top chamfer boundary and fails `ASM_BL_NO_MATE` if
positioned naively. If OCCT cannot chamfer it cleanly, the architecture needs
rethinking, and that is far cheaper to learn now than after two more phases are
built on top.

Two parts, not one. The scissors hook establishes the slab-and-channel pattern on
simple geometry so that a gridfinity failure is unambiguously a kernel problem and
not inexperience with the API.

### Tasks

- [ ] Decide the Notch project location. Recommendation: `examples/notch/` inside
      this repo, as its own project directory with `parts/` and `system.py`. It
      doubles as the test corpus and the worked example. (A separate repo is the
      alternative; decide before writing files.)
- [ ] `system.py`: the Notch constants (`block_width` 25.16, `clearance` 0.2,
      `pocket_width` 20.56, `pocket_depth` 4, `pocket_neck_width` 12.16,
      `top_margin` 3, `pitch_slop` 0.12) as named module-level values
- [ ] `system.py`: `channels(count)` returning the dovetail cut solid, built with a
      plain `for` loop. Do NOT port `ChannelTool`, the 16-lobe comb, `CombWeb`, or
      `JoinComb`. Those exist only because Fusion's combine tool lists never grow.
- [ ] `system.py`: `detent_dimples(count)` (dimples at `z=-10`, 0.8mm past the
      `x=-4.2` floor), as a separate composable function
- [ ] Port `Hook - Scissors - 1x`: 30mm slab, 6mm arm projecting 28mm, 15mm upstand,
      all at the slab bottom, 3mm structural chamfers at the arm junctions, 1mm
      cosmetic pass excluding back/bottom/channel faces
- [ ] Port `Shelf - Gridfinity 2x2 - 4x`: slab, platform, gridfinity sockets via
      `loft()` arrayed with `GridLocations`, gussets at outer ends only (truncated
      quads, not sharp triangles), `Chamfer_Structural` 3mm then `Chamfer_Edges` 1mm
- [ ] Verify fit by coordinate: channel floors at `x=-4.2`, y-centers exactly
      `k * 25.16` for `k` in `0..bracket_count-1`
- [ ] Flex `bracket_count` in both directions (4 → 6 → 2 → 4) and confirm geometry
      tracks. Growth is what catches frozen-selection bugs; shrinking alone passes
      broken parts.
- [ ] Count faces under 1mm² on the gridfinity shelf and compare against the known
      baseline of 18 (16 recess-corner segments at 0.63mm², 2 corner triangles at
      0.87mm²)
- [ ] Measure rebuild latency on both parts, draft and polished, and record it
- [ ] Export STL and confirm it opens cleanly in a slicer

### Success criteria

- Both parts build without OCCT errors
- Gridfinity sliver count is 18, or every deviation is explained
- Fit coordinates match the Fusion originals exactly
- `bracket_count` flexes both directions without breaking chamfers
- Polished rebuild stays under ~500ms (if not, draft mode and caching move up)
- An exported STL is genuinely printable

### Files likely affected

```
examples/notch/system.py                    new
examples/notch/parts/hook_scissors.py       new
examples/notch/parts/shelf_gridfinity.py    new
src/nurb/builder.py                         find_parts may need a system.py exclusion
```

### Known risks in this phase

Chamfer robustness is the whole point of the phase. If `Chamfer_Edges` fails on the
gridfinity shelf, try in order: `Select.LAST` scoping instead of geometric selectors,
splitting into per-region chamfer calls, and moving the gusset peak off the slab-top
boundary (the same fix Fusion needed). Record whatever the failure mode turns out to
be, since it is the OCCT analogue of `ASM_BL_NO_MATE` and will recur.

---

## Phase 2: `nurb check`

### Objective

Printability rules that run as assertions on the in-memory B-rep, calibrated against
parts with known-good outcomes.

### Rationale

This is the differentiated work. Everything else in nurb is assembly of existing
pieces; the rules engine is the part that does not exist elsewhere. Doing it second,
right after the port, means it can be calibrated immediately against 16 parts that
were designed, printed, and whose outcomes are known.

### Tasks

- [ ] `checks.py`: a `Finding` type (rule, severity, message, location, area/value)
      and a registry so rules compose
- [ ] Rule `overhang`: walk faces, keep `normal.Z < 0`, flag angle from `-Z` beyond
      45°. Report area and whether grounded. Sample curved faces rather than taking
      a single `normal_at()`.
- [ ] Rule `sliver`: faces under 1mm², diffed against the part's accepted baseline
- [ ] Rule `build_volume`: bounding box against a printer profile
- [ ] Rule `stability`: center of mass projected outside the bed footprint
- [ ] Rule `projection_ratio`: forward projection ÷ supporting height, warning at
      the doctrine's thresholds (≤1.5 chamfers only, 1.5-2.5 end gussets, >2.5 raise
      height)
- [ ] Convexity test: sign of `(n1 × n2) · t` for an edge between two faces.
      **Unit-test both convex and concave cases explicitly.** The naive
      averaged-normal approach is recorded as failing, so this needs empirical
      verification, not reasoning.
- [ ] Rule `concave_cosmetic`: flag any concave edge carrying a cosmetic-sized
      chamfer
- [ ] Rule `back_bottom_chamfer`: flag chamfers on faces adjacent to the back plane
      or bed plane
- [ ] Accepted-warnings baseline: structured, stored per part, so a new finding is a
      regression and a known one is silent
- [ ] `nurb check` CLI, reporting findings grouped by severity
- [ ] Wire check results into the viewer as an overlay panel
- [ ] Calibrate: run against both ported parts and drive false positives to zero

### Success criteria

- Zero false positives on parts that printed fine
- The gridfinity shelf's 18 known slivers are silent; a nineteenth would fail
- Every rule distinguishes "this will fail" from "this needs support"
- Findings appear in the viewer without leaving the loop

### Files likely affected

```
src/nurb/checks.py        new
src/nurb/rules/*.py       new, one module per rule family
src/nurb/cli.py           add the check command
src/nurb/server.py        include findings in the rebuild payload
src/nurb/viewer.html      findings panel
tests/test_convexity.py   new, both cases
```

### Explicitly out of scope

`min_wall` is deferred. It is the hardest rule (inscribed sphere is correct but
expensive, ray casting is cheap and wrong at corners) and it should not hold up the
rules that are exact and cheap. Revisit in post-implementation.

---

## Phase 3: Agent interface

### Objective

A fresh Claude or Codex session can open a part cold, understand why it is the way
it is, change it, and verify the change.

### Rationale

The primary user is a model. Until the doctrine, the cards, and a way for an agent to
see its own output exist, nurb is a tool a human drives that an agent can technically
invoke. This phase is what makes it agentic.

### Tasks

- [ ] Move the design doctrine into the package as a single markdown file, exposed
      via `nurb rules`. One source of truth; harness files become thin shims.
- [ ] `SKILL.md` for Claude Code and `AGENTS.md` for other harnesses, each ~10 lines
      pointing at `nurb rules`
- [ ] `nurb card`: generate the AUTO block from a build (parameters, bbox, derived
      ratios, fit checks, check findings)
- [ ] Card template with `## What it is`, `## Design notes`, **`## Don't`**, and
      `## Changelog`. `## Don't` is required, not optional: it is the only place that
      records what was tried and rejected, and without it an agent re-adds the
      lead-in chamfer that was deliberately retired.
- [ ] Fold the accepted-warnings baseline into the card
- [ ] `measurements.yaml`: named real-world values with provenance, plus a
      convention for the agent to ask before building rather than improvising
- [ ] Headless PNG render: Playwright against the running viewer at
      `?part=<name>&view=iso`, reusing the same scene so the agent sees what the
      human sees and no offscreen GL stack is needed
- [ ] `nurb render <part>` writing to `build/<part>.png`

### Success criteria

- A fresh session, given only the repo, can build a part correctly without asking
- `nurb rules` output is complete enough that no doctrine lives in harness files
- An agent can call `nurb render` and read the resulting image
- Editing a part updates its card without hand-editing the AUTO block

### Files likely affected

```
src/nurb/doctrine.md      new, the single source
src/nurb/card.py          new
src/nurb/render.py        new, Playwright
src/nurb/cli.py           rules, card, render
SKILL.md, AGENTS.md       new, thin
```

---

## Phase 4: Viewer and human UX

### Objective

Make the design loop feel good to drive by hand.

### Rationale

Sliders are nearly free given the part contract (keyword defaults are already
introspectable) and they are the single feature that makes this feel like a design
tool rather than a build script with a preview window. Deliberately after the agent
interface, since the agent path is the point of the project.

### Tasks

- [ ] Expose each part's parameters over the API from the existing signature
      introspection
- [ ] Slider UI in the viewer, one control per numeric parameter, with sensible
      ranges derived from the default
- [ ] Live rebuild on slider drag, debounced, using draft mode
- [ ] "Apply to file" so a slider exploration can be written back to the defaults
- [ ] Vendor three.js so the viewer works offline
- [ ] Verify the reframe button and empty state visually (currently confirmed only
      in CSS, never on screen)
- [ ] Section view toggle

### Success criteria

- Dragging `item_height` rebuilds live without touching the file
- The viewer works with networking disabled
- All four overlays (HUD, error, reframe, empty) confirmed on screen

### Files likely affected

```
src/nurb/viewer.html      sliders, sections, vendored three
src/nurb/vendor/          new
src/nurb/server.py        param API, param overrides in rebuild
src/nurb/builder.py       already supports overrides; wire them through
```

---

## Phase 5: Full port, extract, tests

### Objective

The whole Notch library running in nurb, with fit correctness enforced by CI rather
than by reading.

### Rationale

Once one hard part and one simple part work, the remaining fourteen are mechanical
and parallelizable. The test suite is what converts the catalog cards' hand-checked
"Fit:" lines into something that runs.

### Tasks

- [ ] Port the remaining 14 parts (3 hooks, 5 holders, 2 mounts, 1 bin, 3 shelves
      beyond the archetype). Parallelizable: one part per file, no shared state.
- [ ] Decide whether the three gridfinity shelves (2x1, 2x2, 3x2) collapse into one
      parameterized file with export configs, since they are the same part flexed
- [ ] `nurb extract`: find duplication across sibling parts, lift it into
      `system.py`, rewrite imports. Runs after the port, not before, because systems
      are extracted rather than scaffolded.
- [ ] pytest suite over every part: channel floors at `x=-4.2`, y-centers on exact
      pitch, no extra floor face beyond `bracket_count`, no stunted y-span
- [ ] Parametrized flex test: every part builds at several `bracket_count` values
- [ ] Check baselines asserted for every part
- [ ] CI workflow running the suite

### Success criteria

- All 16 parts build
- `pytest` green across the library
- Fit assertions catch a deliberately introduced pitch error
- Exports match the Fusion STLs dimensionally

### Files likely affected

```
examples/notch/parts/*.py     14 new
examples/notch/system.py      grows via extract
tests/test_notch_fit.py       new
src/nurb/cli.py               extract
.github/workflows/test.yml    new
```

---

## Post-implementation

All five phases are complete. What is left, in the order it looks worth doing:

- [x] `min_wall` rule, shipped in Phase 2 as a ray cast and stated as an approximation
- [x] `min_wall` by inscribed sphere, as a correction of the ray rather than a
      replacement. A full tangent-sphere pass proved wrong on this library before it
      shipped: it reads curvature as thickness (0.033mm on the shelf, 0.8mm at every
      detent dimple), so the sphere only refines chords thin enough to change the
      verdict, and a contact that grazes rather than crosses is rejected by the same
      0.3 cosine floor the ray's exit filter uses. See PROGRESS.md.
- [x] Printer profiles: shipped. Machine facts live in `src/nurb/printers.toml`, a
      project names one in `printer.toml`, and a card still wins for what its part
      has justified. `nurb check --printer x` tries another machine.
- [ ] Decide `nurb` vs `nurb-cad` for the PyPI package name
- [ ] Claim PyPI `nurb`, npm `nurb`, nurb.dev
- [x] Publishing path, half-answered: nurb hosts its own. The dev server's viewer is
      the configurator, with `stl`/`step` downloads built at the slider values. An
      OpenSCAD export for MakerWorld's customizer is not a target, because build123d
      does not transpile to OpenSCAD. Hosting without a running kernel stays open.

## Notes

**Decisions carried in from research:**

- Checks run on in-memory B-rep, not exported files. More accurate, only works
  inside the stack.
- Notch ports to nurb, making its 16 parts the test corpus and calibration set.
- Systems are extracted, never scaffolded. `nurb extract` over `nurb new system`.
- No MCP server. The CLI is the portable agent surface.
- Command names stay boring so a model can guess them.

**Open question deferred to Phase 2:** does `nurb check` gate `nurb export`, or only
report? Leaning report-only with an opt-in `--strict`, on the grounds that a warning
which blocks work gets disabled. Settled that way, and CI is what spends the `--strict`.

**Planning note:** Phase 1 is the only phase that can invalidate the others. If the
gridfinity port fails in a way that cannot be worked around, stop and revisit the
kernel choice before continuing. It did not, and nothing in the twelve parts that
followed moved the kernel question either.

**Answered in Phase 5:** the three gridfinity shelves do collapse into one file, and so
do the two utility hooks, as variants on the card rather than as export configs in a
separate place. See `docs/core/PROGRESS.md`.
