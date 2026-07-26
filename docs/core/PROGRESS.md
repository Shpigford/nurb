# nurb core progress

## Status: Phase 1 complete. Phase 2 next.

**The kernel question is answered: OCCT builds both parts and both match the Fusion
originals dimension for dimension.** The architecture stands. Two assumptions carried
in from research did not survive contact with a real part, and they change what Phase 2
and Phase 4 should prioritize. See Findings below.

## Quick reference

- Research: `docs/core/RESEARCH.md`
- Implementation: `docs/core/IMPLEMENTATION.md`

## Prerequisites

- [x] Commit the current tree. Done: `957a6fc`, the runtime and docs.
- [x] Decide where the Notch port lives. **`examples/notch/`**, its own project
      directory with `parts/` and `system.py`. It doubles as test corpus and worked
      example, and `examples/` is already where the suite will look.

---

## Phase progress

### Phase 1: Kernel proof
**Status:** Complete (2026-07-25)

Both parts build, match the Fusion originals, and run in the live loop.

#### Tasks completed
- [x] Notch port lives in `examples/notch/`
- [x] `system.py`: constants, `channels()`, `detent_dimples()`, `polish_edges()`
- [x] Ported `Hook - Scissors - 1x`
- [x] Ported `Shelf - Gridfinity 2x2 - 4x`
- [x] Fit verified by coordinate on both parts
- [x] `bracket_count` flexed both directions
- [x] Sliver counts compared against the known baselines
- [x] Rebuild latency measured, draft and polished, per stage
- [x] STL exported and checked

#### Results against the success criteria

| Criterion | Result |
|---|---|
| Both parts build without OCCT errors | Yes, one solid each |
| Gridfinity sliver count is 18 | **Exactly 18**: 16 x 0.632mm² + 2 x 0.866mm² |
| Fit coordinates match Fusion exactly | Floors at x=-4.2, y-centers on exact pitch, full 21.56mm spans |
| `bracket_count` flexes both directions | Hook 1 -> 2 -> 3 -> 1, shelf 4 -> 6 -> 4, baselines unchanged |
| Polished rebuild under ~500ms | Build yes (470ms). **Whole loop no (~1.09s)**, see Findings |
| An exported STL is genuinely printable | Watertight, 1 body, euler 2, no degenerate faces; BambuStudio reports `manifold = yes` |

The hook's bounding box is 34 x 25.16 x 30mm and the shelf's is 94 x 100.64 x 42mm.
Both match their catalog cards to the digit.

The sliver counts are the strongest evidence in the phase. Neither was tuned for:
the polish exclusion rule was derived from the doctrine, and the counts came out at
the recorded baselines on the first build that completed. The shelf's baseline also
generalizes to `4 * grid_x * grid_y + 2`, confirmed at four grid sizes.

#### Decisions made

- **Notch lives at `examples/notch/`.** Test corpus and worked example in one place.
- **`system.py` carries `polish_edges()` as well as the constants.** Both parts need
  the same three vetoes (back face, bottom face, channel interior), and it was clear
  they were shared because both parts were in front of me. Extraction, not scaffolding.
- **No `gusset_count` on the shelf.** The Fusion part carries one because the shelf
  family shares a template; here the gussets are the side cheeks and a third lands in
  the middle of a cell. A parameter that breaks the part when changed is worse than
  no parameter.
- **`gusset_drop` raised 2 -> 3mm.** The 2mm in Fusion was a kernel workaround, not
  design intent. Restated as a rule (clear twice the chamfer) it is correct for both.
- **Structural chamfers use `new_edges`, not geometric selectors.** This is the
  algebra-mode answer to `Select.LAST`, and it is why the parts survive a flex.
- **Grid is the build plate.** The viewer now drops a part onto z=0 rather than
  drawing it where its modeling origin says. Notch hangs everything below z=0, so
  every part rendered underneath the plate.
- **Channel clearance is per-channel, not per-system.** The first printed
  `hook_scissors` came out loose side to side. A calibration ladder (`fit_coupon` at
  0.20 / 0.30 / 0.40 / 0.50) put the right single-bracket fit at **0.30mm per side**,
  against a shipped 0.5. The looseness is specific to 1x parts: one channel constrains
  yaw over its own 21.56mm, four constrain it over 75mm, which is why the shelves
  never felt loose at the same number. **One clearance now, every channel, every
  part.** Printed coupons at 2, 4 and 6 brackets all slid on at the same fit, so a
  real wall's pitch needs no compensating for and a longer run costs nothing.

  Three wrong versions preceded that, all variations on giving later channels more
  room, and the sequence is the lesson:

  1. Relief accumulating per channel, unbounded. Printed at 0.66 on the far channel of
     a 4x, looser than the flat 0.5 the library shipped for years, so it exceeded the
     only fit ever shown to work.
  2. Relief capped, but still per-channel: channel 0 tight, the rest relieved. Nothing
     makes channel 0 the datum except being `k=0` in the loop, and putting the one
     tight channel at the *end* of a run is the worst place for it, since residual yaw
     then pivots there and swings the far end the maximum amount.
  3. Uniform within a part, scaled by run length. Coherent, and still wrong, because
     it was compensating for scatter the wall does not have.

  Each version was a smaller amount of code than the one before, and the correct
  answer was the least of all: no scaling at all. `PITCH_SLOP` survives in the
  constants table as measured hardware data with nothing spending it.

  The general lesson is worth more than the number. Every version was reasoned from a
  plausible physical story about pitch scatter, and the story was never checked
  against a wall. Three rounds of increasingly careful modelling of a phenomenon that
  had to be measured before it was worth modelling at all.

  **The number is 0.25**, from 0.20 printing too tight to seat and 0.30 sliding on
  loosely. The window is therefore only about 0.1mm wide, which is the same order as
  FDM extrusion variation, so 0.25 is chosen as the middle of the band rather than as
  a preference: it is where a print that drifts either way still fits. It also sets
  where calibration stops being worth it, since the printer moves further between
  prints than a finer increment would.
- **Parts check `item_depth` against `MIN_ITEM_DEPTH`.** Found in review: a slab
  thinner than 5.2mm leaves no material at `MERGE_X`, so the forward feature never
  touches it. That built, reported a normal bounding box, and exported an STL in two
  loose pieces. Nothing in the pipeline reports solid count, which is what made it
  silent, and `item_depth=5` is a plausible edit given the channel is only 4.2 deep.
  The two guards duplicate; `nurb extract` in Phase 5 is where that gets lifted.

#### Blockers
- (none)

---

### Phase 2: `nurb check`
**Status:** In progress

Printability rules on the in-memory B-rep, calibrated to zero false positives.

#### Tasks completed
- [x] `checks.py`: `Finding`, `Context`, a rule registry, `run()`
- [x] Convexity test, with both cases unit-tested
- [x] Rule `sliver`, silent at a declared baseline
- [x] Rule `build_volume`

#### Decisions made

- **Convexity is `n1 . u2`**: does the second face extend in the direction the first
  face's outward normal points. If it does, the solid folds back on itself and the
  edge is concave. No winding convention, no orientation assumption.
- **Which way a face extends is settled by probing the face**, not by aiming at its
  centroid. The centroid version passed a box and both unit tests and was still
  wrong: a face with the rest of the part merged into it puts its centroid somewhere
  unrelated to this edge, which showed up as convex slab edges reported concave. It
  took an independent method to catch, which is the whole reason RESEARCH said to
  verify this one empirically rather than reason about it.
- **Verified two ways.** Four unit tests with hand-counted answers covering both
  cases, plus every edge of both real parts cross-checked against a completely
  separate method (sample a ring around the edge, ask the solid how much of it is
  inside). 115/115 on the hook and 369/512 on the shelf agree with zero
  disagreements; the other 143 are edges the sampling method cannot resolve at any
  radius, which is a limit of the cross-check and not a verdict on the classifier.
- **The build direction is not the model's z**, so `Context.up` carries it. A part is
  modelled on whatever datums make it readable and printed on whatever face keeps it
  off supports, and for Notch those differ by 90 degrees: parts hang from a slab top
  at z=0 and print on their backs. An overhang rule that assumes model z would report
  confident nonsense about every part in this library.
- **The sliver baseline is a count, not a set of faces.** Which face is which shifts
  as soon as anything upstream of the polish pass moves; the count is the stable
  assertion. Hook 6, shelf 18, both silent when declared and both reported exactly
  when not.

#### Carried in from Phase 1
- Two calibration parts exist with **known-exact** baselines: hook 6 slivers at
  0.866mm², shelf 18 (`4 * grid_x * grid_y + 2`). A nineteenth is a regression.
- A new rule falls out of the port: **`chamfer_clearance`**. Two chamfered convex
  edges need more than `2 * chamfer_size` of face between them or the kernel cannot
  build the corner. It is cheap to check, it is exact, and it caught two real bugs
  in this phase before either was understood. Worth adding to the rule list.
- `polish_edges()` in `examples/notch/system.py` is a first draft of the
  `back_bottom_chamfer` and `mating_chamfer` rules, written as a selector instead of
  a check. Phase 2 should be able to reuse the predicate.
- The concave-edge exclusion is still done structurally (subtract `new_edges` from
  the polish set) rather than by testing convexity. That works because the only
  concave edges in these two parts are the ones the structural pass just made. It
  will not generalize, so the convexity test is still owed.

#### Blockers
- (none)

---

### Phase 3: Agent interface
**Status:** Not Started

`nurb rules`, card generation, headless render, harness shims.

#### Tasks completed
- (none yet)

#### Decisions made
- (none yet)

#### Blockers
- (none)

---

### Phase 4: Viewer and human UX
**Status:** Not Started

Parameter sliders, vendored three.js, section view.

#### Tasks completed
- (none yet)

#### Decisions made
- (none yet)

#### Blockers
- (none)

---

### Phase 5: Full port, extract, tests
**Status:** Not Started

Remaining 14 Notch parts, `nurb extract`, pytest suite, CI.

#### Tasks completed
- (none yet)

#### Decisions made
- (none yet)

#### Blockers
- Depends on Phase 1 establishing the part patterns

---

## Pre-phase work (already built)

The runtime skeleton predates this plan and belongs to no phase. Recorded here so a
future session knows what exists.

**Built and verified 2026-07-25:**

- `nurb new / dev / build / export`, 744 lines across six files
- Live rebuild loop: save a part, geometry swaps in the browser
- **Camera survives rebuilds.** Verified by parking the camera at a known position
  and diffing after a rebuild. Persists per part to localStorage across reloads.
- Reframe offered as a button, only when the bbox changes more than 3x
- Build errors show a traceback trimmed to the user's file, retain the last good
  geometry at 22% opacity, and clear on the next good build
- Draft mode wired through the part contract

**Verified only on `Box() - chamfer()`.** This is the central caveat on everything
above, and the entire reason Phase 1 comes first.

---

## Findings from Phase 1

Three of these change what later phases should do. Recorded here rather than buried
in a card, because they contradict things written in RESEARCH.md before any real part
existed.

### 1. The kernel rule that explains every failure in this phase

**Two chamfered convex edges need more than `2 * chamfer_size` of face between them.**
Closer than that and OCCT raises `Standard_Failure: BRep_API: command not done`, which
build123d surfaces as `ValueError: Failed creating a chamfer, try a smaller length
value(s)`. This is the OCCT analogue of `ASM_BL_NO_MATE`.

Measured, not reasoned: at `chamfer_size` 1mm the shelf fails with 1.66mm between the
edges and builds with 2.16mm; at 0.5mm it builds with 1.16mm. The threshold tracks the
chamfer exactly.

Both shelf failures were this one rule:

- The gusset peak 2mm below the slab top. Fusion needed exactly that 2mm to escape
  `ASM_BL_NO_MATE`; OCCT needs more than 2mm. Same spot, same cause, different
  threshold.
- A platform wider than `slab - 4 * chamfer_size`. This is where the card's grid-to-
  bracket pairings (1 -> 3, 2 -> 4, 3 -> 6) actually come from.

Notably, **every individual edge chamfered fine**; only the batch failed. Debugging by
"try a smaller length" would never have found it. Bisecting the edge set pairwise did.

### 2. Draft mode is not the latency lever research claimed

RESEARCH.md says chamfers are essentially the entire build cost and that draft mode
scales with polish. That came from `Box() - chamfer()` and **it is false on a real
part.** Stage breakdown for the shelf:

```
socket lofts          156ms   34%
socket cut             68ms   15%
cosmetic chamfer       66ms   14%
structural chamfer     43ms    9%
gussets                42ms    9%
fuse to slab           39ms    8%
select polish edges    26ms    6%
channels + detent      21ms    5%
--------------------------------
build                 460ms
```

Stage timings come from one instrumented run, so they total 460ms against the 470ms
measured elsewhere in this document. Run-to-run noise, not a discrepancy.

Chamfers are 23% of the build, not all of it. Draft mode saves 20%, not 18x.

### 3. Tessellation, not the build, is the loop

```
                     build    tessellate + GLB    loop
hook, polished        46ms          120ms        ~166ms
hook, draft           26ms           66ms         ~92ms
shelf, polished      470ms          620ms       ~1090ms
shelf, draft         380ms          520ms        ~900ms
```

Tessellation costs more than the entire build on the shelf, and draft mode barely
touches it. **The phase's ~500ms target is met by the build and missed by the loop.**
The lever is tessellation tolerance, geometry caching, or pushing tessellation off the
rebuild path, none of which is draft mode. This should inform Phase 4 rather than
being discovered there.

### 4. `new_edges` is the algebra-mode `Select.LAST`

`new_edges(before, combined=after)` returns exactly the edges an operation created.
Used for the structural chamfers and to exclude them from the cosmetic pass. This is
what makes the parts survive a `bracket_count` flex, and it is a genuine improvement
over the strict-ordering rule Fusion needed. CLAUDE.md's preference for it is correct
and now has evidence.

---

## Session log

### 2026-07-25 (later): Phase 1

Ported both parts. Read the exact channel cross-section off the live Fusion model
rather than deriving it from the constants table, which was the right call: the table
documents the bracket pocket, and the channel is the pocket plus clearance that is
0.2mm in depth but 0.5mm per side in width. Guessing would have produced a channel
1mm too tight.

Order of work: system module, hook, shelf. The hook earned its place in the plan.
Its cosmetic pass failed first, on the detent dimple, which was a plain bug in my
exclusion envelope rather than anything kernel-related, and finding that on simple
geometry made the shelf's two real failures easy to recognize as different.

Both parts verified in the live loop with a screenshot, both sitting on the grid.

### 2026-07-25: runtime skeleton

Built the runtime skeleton, then wrote RESEARCH.md and IMPLEMENTATION.md.

Measured on this machine (M-series arm64, Python 3.13):

```
import build123d          45.7s cold, 2.28s warm
build + boolean            4ms
chamfer, 8 edges           6ms
tessellate (tol 0.1)      51ms
export STL / STEP          3ms / 15ms
draft vs polished         1ms vs 18ms
```

Three bugs found and fixed (see Lessons learned).

Next session: prerequisites, then Phase 1.

---

## Files changed

```
src/nurb/__init__.py      part decorator + build123d re-export
src/nurb/registry.py      @part, signature introspection
src/nurb/builder.py       load, build, tessellate, GLB
src/nurb/server.py        watcher, rebuild, HTTP + websocket on one port
src/nurb/viewer.html      three.js viewer, Z-up, camera persistence
src/nurb/cli.py           new / dev / build / export
parts/bracket.py          throwaway demo part
README.md
docs/core/*.md
```

Phase 1:

```
examples/notch/system.py                     new  constants, channels, detent, polish_edges
examples/notch/parts/hook_scissors.py        new
examples/notch/parts/hook_scissors.md        new
examples/notch/parts/shelf_gridfinity.py     new
examples/notch/parts/shelf_gridfinity.md     new
src/nurb/builder.py       load() puts the project root on sys.path so a part can
                          `from system import ...`, and forgets the project's own
                          modules afterwards so editing a shared one is picked up
src/nurb/server.py        watch the project root too; a change outside parts/ is
                          treated as a shared module and rebuilds every part
src/nurb/viewer.html      parts sit on the grid instead of hanging under it
```

---

## Architectural decisions

Carried from research and the questions answered during planning.

| Decision | Rationale |
|---|---|
| build123d / OCCT as the kernel | Same class of B-rep kernel as Fusion's ASM, runs headless, real chamfers and STEP |
| Keyword defaults are the parameters | One declaration serves the agent, CLI, slider UI, tests, and any future configurator. A separate `PARAMS` dict would drift. |
| Checks run on in-memory B-rep, not files | Exact face areas and normals instead of triangles. Costs standalone usefulness; accepted. |
| Notch ports to nurb | Its 16 parts become the test corpus and the calibration set for the rules |
| Systems extracted, never scaffolded | Notch did not begin as a system; `block_width` exists because a wall got measured. `nurb extract`, not `nurb new system`. |
| No MCP server | The existing Fusion MCP needed a hand-written HTTP client to be usable. A CLI works in every harness. |
| Boring command names | The primary user is a model. It can guess `build` and `check`; it cannot guess a themed alias. |
| Persistent process is mandatory | 2.28s warm import per rebuild would make the loop unusable |
| Do not port Fusion's scaffolding | `ChannelTool`, the 16-lobe comb, `CombWeb`, `JoinComb` exist only because combine tool lists never grow. Use a `for` loop. |
| Name: nurb, command `nurb` | Clean on PyPI, npm, nurb.dev. NURBS is the geometry primitive, so the search overlap is on-topic rather than misleading. |
| A project's own modules are importable and reloadable | `system.py` is the whole point of a parts library. A part says `from system import ...`; the loader puts the root on `sys.path` and forgets project modules after each build so an edit lands on the next rebuild. |
| The grid is the build plate | Where a part's origin falls is a modeling datum. Notch hangs everything below z=0, which put every part under the plate. The viewer drops the part onto z=0 instead. |
| Chamfer selection uses `new_edges`, never frozen geometry | It is what survives a `bracket_count` flex, and it is the algebra-mode `Select.LAST` CLAUDE.md asks for. |

---

## Lessons learned

**Three bugs from building the runtime, all non-obvious:**

1. **Black render.** trimesh welded a box to 8 shared corners and dropped the normal
   attribute, leaving the shader nothing to light. Fix: `process=False` on the
   `Trimesh` constructor, and touch `mesh.vertex_normals` before export. OCCT already
   splits vertices at face boundaries, which is the layout you want.
2. **Hot reload silently dead.** The watchdog `Observer` and the asyncio drain task
   were both created without holding a reference, and asyncio keeps only weak
   references to tasks. Failed by never firing, with no error.
3. **Canvas stacking regression.** Fixing a ResizeObserver feedback loop by making
   the canvas `position: absolute` turned it into a positioned element appended after
   the overlay divs, so it painted over the HUD. Needed explicit `z-index`.

**Process lessons:**

- A repro that starts at equilibrium proves nothing. Reapplying the old canvas CSS
  live failed to reproduce the resize loop because the canvas was already the right
  size; the loop needs an initial mismatch to ratchet against. Nearly filed it as
  "not the cause."
- `elementFromPoint` skips `pointer-events: none` elements, so it reported the canvas
  covering the HUD when painting was fine. Screenshots were the real evidence.
- Redirect stdout early. The first hot-reload debugging session was blind because
  Python buffers stdout when it is not a tty and none of the prints had `flush=True`.

**From Phase 1:**

- **Read the real model, do not derive it from the notes.** The Notch constants table
  documents the bracket pocket; the channel is the pocket plus clearance, and that
  clearance is 0.2mm in depth but 0.5mm per side in width. Nothing said so. Dumping
  the actual faces off the live Fusion part took one script and settled it, and the
  trapezoid area matching to 72.912mm² proved the port before any part was written.
- **A batch chamfer failure is not a bad edge.** Every edge in the shelf's polish set
  chamfered fine on its own; only the set failed. Testing edges individually says
  "everything is fine" and is worthless. Bisecting pairwise found the real rule in
  one pass.
- **Predict the baseline before looking.** Working out that the hook should have
  exactly 6 corner triangles, from the polish exclusions alone, turned the sliver
  count into a test of the rule instead of a number to write down. It came out 6.
  The shelf then came out 18 without tuning. Two independent confirmations that the
  port matches, for free.
- **Fusion's workarounds are sometimes real constraints wearing a disguise.** The
  gusset's 2mm drop looked like pure kernel scaffolding. It is a kernel workaround,
  but the underlying constraint (a chamfer needs room to land) is physics-adjacent
  and applies to OCCT too, at a different number. Deleting it would have been wrong;
  restating it as a rule was right.
