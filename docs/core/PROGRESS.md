# nurb core progress

## Status: Phases 1 through 5 complete, and the README's "not built yet" list built.

**The whole Notch catalog is in nurb.** Sixteen catalog entries out of thirteen part
files and nineteen shipped configurations, every one a single solid matching its Fusion
bounding box, every one clean under `nurb check --strict`, every export watertight. The
fit line each catalog card recorded by hand is an assertion that runs, and it is able to
fail: a deliberate 0.1mm per interval pitch error is in the suite and gets caught.

**The kernel question was answered in Phase 1 and thirteen parts have not moved it.**
The architecture stands. What thirteen parts did move is the rules: two of the eight
fired at geometry the doctrine prescribes, and the shared polish selector had a gap in
one of its three vetoes. All three were found by a part rather than by review, which is
the argument for a port being a calibration set and not just a corpus. See Findings
under Phase 5.

The agent surface is in, and the viewer has sliders, a section view and no network
dependency.

**The loop is about 20x faster than Phase 1 recorded, and the reason invalidates that
finding rather than improving on it.** What Phase 1 measured as tessellation was almost
entirely one pathological iterator in build123d, not geometry. Several assumptions
carried in from research did not survive contact with a real part or a real profiler.
See Findings below, and prefer them to anything in RESEARCH.md that sounds like a
measurement.

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
**Status:** Complete (2026-07-26)

Printability rules on the in-memory B-rep, calibrated to zero false positives.

#### Tasks completed
- [x] `checks.py`: `Finding`, `Context`, a rule registry, `run()`
- [x] Convexity test, with both cases unit-tested
- [x] Rule `sliver`, silent at a declared baseline
- [x] Rule `build_volume`
- [x] Rule `overhang`, with curved faces sampled and bridges told from cantilevers
- [x] Rule `stability`
- [x] Accepted baselines, declared in each part's card
- [x] `nurb check` CLI, with `--strict` for CI
- [x] Rule `projection_ratio`
- [x] Rules `concave_cosmetic` and `bed_bevel`
- [x] Rule `min_wall`, by ray cast, with its limits documented rather than hidden
- [x] Findings in the viewer: a panel plus a pin at each reported point
- [x] **Zero false positives on all three parts**, which is the credibility bar

42 tests. Every rule has both cases against shapes whose answers were worked out by
hand, and the example parts are asserted against the numbers their Fusion cards
recorded. Checks run in 7ms on the hook and 277ms on the shelf.

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
- **The build direction is a setting, not an assumption**, so `Context.up` carries it.
  Notch parts print exactly as modelled, top up, so +z is right for them and the
  default holds. That was worth asking rather than deriving: the same hook reports 3,
  1 or 4 findings depending on which face goes down, and every one of those answers
  looks equally confident. Nothing generalises the Notch case to other projects.
- **A bridge is not an overhang.** Both are 90 degrees to the build direction and the
  normal cannot tell them apart, which is why an angle-only rule reports a channel
  roof and a cantilevered shelf as the same problem. What separates them is whether
  material sits on both sides, so the rule probes just outside and just below the
  face. Under `bridge_limit` a bridge is silent, over it a warning, and a cantilever
  past 45 degrees is a failure. Without this both parts fire two findings per
  channel, on geometry that has printed fine for months.
- **The baseline lives in the card, next to the sentence that justifies it.** A count
  on its own is a magic number; the reason it is allowed is the part that matters, and
  a card is where a part already explains itself. It is a TOML fence, so `tomllib`
  reads it and no dependency is added. A card can also carry printer settings, and a
  typo in a setting name is an error rather than a silently ignored line.
- **A shallow ledge is not an overhang.** The raised label on the calibration coupon
  produced a hundred 90-degree findings at a third of a square millimetre each. What
  makes an unsupported ledge droop is how far it protrudes, not its area or its
  length, so a ledge under `overhang_reach` is silent. Same physics as the bridge
  limit, applied to the cantilever case.
- **`min_wall` is the weakest rule here and the docstring says so.** A ray cast is
  exact on flat parallel walls and wrong in two directions everywhere else, and both
  showed up on the first run: it read the shelf's knife-edge mouth rim as a 0.76mm
  wall, and the coupon's 0.5mm raised label as a 0.5mm wall. Neither is a defect and
  all three parts print. It also misses what an inscribed sphere would catch, a thin
  spot in an inside corner. So a clean result means "no thin walls found", not "no
  thin walls", and the parts declare their own floor next to the reason on the card.

  The one real filter it needed: only count a surface the ray leaves *through*, whose
  outward normal points along the ray. A hit facing back means the ray had already
  left the material, which is how a chamfer two corners away read as a 0.89mm wall on
  a 6mm slab.
- **The rules found a real defect in Phase 1's output.** `concave_cosmetic` flagged
  four 1mm chamfers at the shelf's gusset roots, which are inside corners, and both
  the convexity test and independent ring sampling confirm it. Phase 1 had reasoned
  that the only concave edges were the ones the structural pass made; that was
  untrue, and nothing in the build, the export or the print said so. This is the
  argument for the whole phase in one finding: it is invisible in code, the selector
  reads as an ordinary exposed-edge query, and the part looked fine by every other
  measure. Bounding box, solid count and the sliver baseline are unchanged by the fix.
- **`is_convex` and `concave_edges` are public API now.** A polish pass cannot be
  written correctly without them, which the above demonstrates, so they belong in the
  vocabulary a part file gets rather than inside the checker.
- **Neither chamfer rule identifies chamfers.** `bed_bevel` looks for a face touching
  the plate that is neither flat on it nor square to it, which a bevel is and nothing
  else is. `concave_cosmetic` looks for a strip about as wide as the polish pass
  makes, whose long edges are concave and which leans against what it joins. Trying to
  recognise a chamfer as such was the fragile version; describing the defect is not.
- **`projection_ratio` reproduces the card's own number.** grid_y 3 gives 3.24 against
  a card that says "a ratio of 3.2 at item_height 42", and 55mm clears it exactly as
  the card claims. That is the third rule to land on a figure recorded by hand in
  another kernel, after the two sliver baselines, and it is the strongest evidence
  available that these rules measure what they claim to.
- **A part opts in to `projection_ratio` by naming which way it reaches.** The rule is
  meaningless for anything not cantilevered off a wall, and a default guess would
  either fire on everything or nothing. Cards carry it as `[part] forward`.
- **Checks are broadcast after the geometry, not with it.** Checking the shelf costs
  about as much again as building it, so running them inline would push the live loop
  past 1.5s. The model swaps at the speed it always did and the panel fills in a beat
  later.
- **Cards are watched too.** A card carries what the part has justified, so editing
  one changes the answer even though no geometry moved. Without this, editing a
  baseline did nothing until the next code change.
- **The sliver baseline is a count, not a set of faces.** Which face is which shifts
  as soon as anything upstream of the polish pass moves; the count is the stable
  assertion. Hook 6, shelf 18, both silent when declared and both reported exactly
  when not.

#### Results against the success criteria

| Criterion | Result |
|---|---|
| Rules run on the in-memory B-rep | Yes, eight of them |
| Zero false positives on the calibration set | Yes, all three parts report clean |
| Convexity test verified empirically | Two independent methods, both cases, 484 real edges |
| Baselines per part, so a new finding is a regression | On the card, next to the reason |
| `nurb check` exists and is usable | Reports by default, `--strict` for CI |
| Findings visible in the loop | Panel and 3D pins in the viewer |

It also caught a real defect in Phase 1's output: four 1mm chamfers on concave gusset
roots, invisible in code and in every other measure.

#### Deferred, deliberately

- **`chamfer_clearance` is not a `nurb check` rule.** Phase 1 earned the underlying
  rule (two chamfered convex edges need more than `2 * chamfer_size` between them), but
  it is a question about geometry that does not exist yet. By the time `nurb check`
  runs, a violation has already failed the build with an OCCT error. It belongs at
  build time, wrapping the chamfer call with a better message, which is a different
  piece of work from a rule.
- **`nurb check` does not gate `nurb export`.** The open question from RESEARCH,
  answered the way it leaned: report only. A part with a justified warning still has to
  be exportable, and a check that blocks work gets switched off. `--strict` is there
  for CI, which is where blocking belongs.
- **`min_wall` is approximate and says so.** The inscribed-sphere method is the real
  answer if wall thickness ever matters more than it does now.

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
- ~~The concave-edge exclusion is done structurally rather than by testing convexity,
  which works because the only concave edges in these parts are the ones the
  structural pass just made.~~ **Wrong, and Phase 2 proved it.** The shelf's gusset
  roots are concave too, and all four were carrying a 1mm cosmetic chamfer in the
  shipped part. `polish_edges` now vetoes concave edges outright.

#### Blockers
- (none)

---

### Phase 3: Agent interface
**Status:** Complete (2026-07-26)

The doctrine ships in the package, cards regenerate their own facts, and a part can be
looked at without a human at the keyboard.

#### Tasks completed
- [x] `src/nurb/doctrine.md`, the single source, printed by `nurb rules`
- [x] `SKILL.md` and `AGENTS.md`, ~20 lines each, pointing at `nurb rules`
- [x] `nurb card`: the AUTO block from a build, grafted under the title
- [x] Card template already carried the four sections; `nurb card` now reports an empty
      one, `## Don't` included
- [x] Accepted baselines are in the card already, from Phase 2, and the AUTO block prints
      the measured sliver count next to the accepted one
- [x] `measurements.toml` plus `measured()`, provenance required
- [x] Headless PNG through Playwright against the running viewer
- [x] `nurb render <part>` writing `build/<part>.png`
- [x] 23 new tests, 77 total

#### Results against the success criteria

| Criterion | Result |
|---|---|
| `nurb rules` is complete enough that no doctrine lives in harness files | 236 lines covering the part contract, printability, load path, polish, kernel traps, cards, measurements, verification. `SKILL.md` and `AGENTS.md` carry no doctrine, only the command list. |
| Editing a part updates its card without hand-editing the AUTO block | `nurb card`, idempotent, and a test asserts the three real cards are current |
| An agent can call `nurb render` and read the resulting image | Yes, verified by looking at all three parts plus a top view and a `--chrome` view |
| A fresh session, given only the repo, can build a part correctly without asking | **Not verified.** See below. |

The last one is the phase's whole objective and it has not been tested the only way it
can be, which is a cold session working a part. What exists is the material it would
need. Treat it as unproven until someone runs it.

The AUTO blocks reproduced, unprompted, the numbers the cards had recorded in prose:
34 x 25.16 x 30 and 94 x 100.64 x 42 for the bounding boxes, 6 and 18 slivers with
smallest faces at 0.866 and 0.632mm², and a 2.24 projection ratio against a card that
predicted grid_y 3 would reach 3.2. That is the fourth time a Phase 2 or 3 measurement
has landed on a figure recorded by hand in another kernel.

`nurb render` costs ~9s for one part cold and 13.4s for all three, since one browser and
one server serve the whole list. The OCCT import is most of the first number.

#### Decisions made

- **`measurements.toml`, not `measurements.yaml`.** The plan said YAML. There is no YAML
  parser in the standard library, `tomllib` is, and cards already use a TOML fence for
  their check settings. Adding PyYAML would be a fifth dependency to read one small file
  in a second format. One format for both, no new dependency.
- **The AUTO block carries no timestamp.** The Fusion cards had "synced 2026-07-22 from
  Fusion v7", which churns on every regeneration and makes a diff meaningless. Without
  one the block is a real cache: regenerating on unchanged geometry produces no diff, so
  `git diff` is the staleness check, and a test can assert the committed cards match what
  the parts build to today. That test earned itself immediately, as the regression check
  on the `measured()` refactor below.
- **The AUTO block does not repeat the parameters**, which the plan asked for. Keyword
  defaults *are* the parameters and a part file is readable text, so copying them into the
  card is the parallel `PARAMS` dict the contract forbids, one level removed. The Fusion
  cards listed them because the geometry lived in a binary file nobody could read. The
  block now holds only what a build can tell you and the reader cannot: bounding box,
  volume, solid count, face count, sliver count against the accepted baseline, projection
  ratio, check verdict.
- **No fit checks in the AUTO block**, also asked for by the plan. "Channel floors at
  x=-4.2" is Notch, and nothing in `src/nurb/` should know what a channel is. The generic
  version already exists: a card names which way the part reaches and gets its projection
  ratio. Notch's own fit assertions belong in the Phase 5 test suite, which is where the
  plan already puts them.
- **Playwright is an optional extra, not a dependency.** It is the fifth-dependency rule
  applied: one command wants a browser, the download is larger than everything else in
  the tree, and the answer is `[project.optional-dependencies] render`. Asking for
  `nurb render` without it prints the two commands that fix it.
- **The default headless shell renders WebGL, so no `channel="chromium"` pin.** Measured
  both: each reports WebGL 2.0 through SwiftShader and each draws the scene. Pinning the
  channel would only narrow which Playwright installs work, including
  `playwright install --only-shell`.
- **`nurb render` hosts its own server.** Requiring `nurb dev` to be running is a
  precondition an agent has to discover, and the whole point is one command that works
  cold. It starts the server on a free port, serves the viewer, screenshots, stops. The
  file watcher is deliberately not started, since nothing changes during a render.
- **The image is geometry only by default.** `--chrome` keeps the HUD and the findings
  panel. The reason to keep that flag is not the panel, it is the 3D pins: "overhang at
  (12, 3, -8)" is a coordinate, and a pin is a place. Everything else the panel says, the
  CLI says better.
- **`--width` is the width of the file.** Dropped `device_scale_factor=2`, which silently
  doubled it, and in `--chrome` mode the screenshot is the page rather than the canvas,
  because otherwise the sidebar quietly took 220px off what was asked for.
- **`measured()` raises rather than defaulting, and provenance is required.** A value with
  no `how` is a guess with a filename on it. The three refusals (no file, unknown name, no
  provenance) all exist because the failure they prevent is invisible: an invented
  dimension builds, checks clean, exports and prints.
- **`MeasurementError`, not `KeyError`.** `KeyError` reprs its argument, so a message
  containing a worked TOML example came out as one quoted string full of backslash-n with
  the useful part unreadable. Found by looking at the output rather than at the code,
  which is the only way that class of bug shows up.
- **The example splits measured hardware from chosen fit.** Six constants moved out of
  `examples/notch/system.py` into `measurements.toml`: the bracket pitch, height, pitch
  slop, and the three pocket dimensions, all of them facts about a bracket that nothing
  can derive. `CLEARANCE` and `SIDE_CLEARANCE` stayed, because they came out of printed
  coupons rather than off a bracket: they are decisions informed by measurement, and their
  reasoning is worth more than their number. That line is the one worth keeping, since it
  is what stops the file becoming a bag of constants.
- **An empty required section is reported, not enforced.** `nurb card` names any of the
  four that is missing or blank. A part that will not build until its changelog is written
  is a tool nobody keeps, but `## Don't` left empty is how the retired lead-in chamfer
  comes back.
- **CLAUDE.md keeps its kernel rules.** The doctrine is the authority for designing parts
  and the harness shims are `SKILL.md` and `AGENTS.md`, as the plan says. CLAUDE.md is
  instructions for developing nurb itself, a different audience, and the two chamfer traps
  it names are worth having in automatically loaded context. `nurb rules` is the full
  statement of both.

#### Findings

- **Generated text has to be ASCII, and it was not.** The first AUTO block said `mm³` and
  `mm²`, copied from the hand-written prose a few lines below it. `checks.py` had already
  settled this by writing `mm2` in all five of its messages, and the reason is not
  cosmetic: measured, a block written on a cp1252 machine comes back as **invalid UTF-8**
  elsewhere, so nothing can read that card at all. A card's prose can say `mm²` because a
  human wrote it once; a generated line that has to be byte-identical on every platform
  cannot. Fixed both ways, since the two are separate problems: generated lines are ASCII
  now, and every read and write of a card or the doctrine passes `encoding="utf-8"` instead
  of trusting the locale, including the pre-existing read in `from_card`. A test asserts
  the blocks on disk are ASCII while allowing the prose around them not to be.
- **Findings pins were invisible on the geometry they annotate.** Phase 2 shipped them with
  the default `depthTest`, and a rule reports a point *on a face*, so the pin sits half
  inside the material. Measured on a deliberately cantilevered test part: two findings, two
  pins in the scene at the right coordinates and colours, and only one visible, because the
  `fail` pin on the shelf underside is behind the shelf from every angle that shows the
  shelf. A marker you cannot see is worse than no marker, because the panel still says it
  is there. Pins now draw through the solid (`depthTest: false` plus a per-mesh
  `renderOrder`, since a Group's `renderOrder` only reaches its children in some three.js
  versions). This is Phase 3 finding a defect in Phase 2's output, the same way Phase 2
  found one in Phase 1's, and it was only found because `--chrome` had no reason to exist
  except those pins, so it had to be tested against a part that actually fires a rule. All
  three example parts report clean, which is exactly why this went unnoticed.
- **The measurement lookup walked out of the project.** `_find` climbed to the filesystem
  root, so a part could silently answer with an unrelated `measurements.toml` from an
  ancestor directory: a wrong dimension that builds, checks clean and prints, which is the
  one failure this module exists to prevent. It now stops at the project root, meaning the
  directory holding `parts/`.
- **The AUTO block was found by its exact opening sentence.** Changing that wording once
  would have left every card on disk holding an unrecognised block, and the next
  `nurb card` would have added a second one underneath it. It now matches on `<!-- AUTO`,
  so any block, whatever its opener, is replaced.
- **The projection ratio was computed in two places.** `nurb check` judged one and the card
  printed another, agreeing today by construction. Both now call `checks.projection`.
  Re-verified against the figures the card records: `grid_y` 3 gives reach 136mm and ratio
  3.24 and fires, and `item_height` 55 brings it to 2.47 and clears, which is what Phase 2
  measured.
- **`nurb render` inherits the viewer's CDN dependency, and it fails closed.** Measured
  with unpkg blocked: the server serves, the page loads, the canvas exists, and three.js
  never arrives, so nothing is ever drawn. That promotes Phase 4's "vendor three.js" from
  polish to a prerequisite for rendering offline or in a sealed CI container. The render
  now says so when it times out, because a bare Playwright timeout sends the reader to
  look at their geometry instead of their network.
- **A top view is degenerate in a Z-up scene.** `camera.up` parallel to the view
  direction gives an undefined orientation rather than a wrong one, so `?view=top` needed
  an explicit up flip. Worth knowing before Phase 4 adds a view widget.
- **A still does not need orbit headroom.** The viewer frames a part at 2.1x its span,
  which is right for orbiting and wastes most of a screenshot. A named view is only ever
  asked for by a still, so it frames at 1.45x. The interactive default is untouched.
- **`window.__nurb.ready` is false in a hidden tab, and that is correct rather than
  broken.** It is set from a `requestAnimationFrame` pair, and rAF does not fire while
  `document.visibilityState` is `hidden`. Found while verifying the live loop in a
  backgrounded browser pane: the camera held its position exactly across a rebuild and
  `ready` stayed false, which looked like a bug for a minute. It is not. `ready` means the
  geometry has been painted, and a hidden tab never paints, so a screenshot taken then
  would be stale whatever the flag said. The consequence for the code is one line of copy:
  the render's timeout error named the network as *the* cause, and now names both, because
  a confidently wrong error message sends the reader to inspect their geometry.

#### Deferred, deliberately

- **No `nurb card --check`.** The block is idempotent, so `git diff --exit-code` already
  answers "is this card stale" in CI, and the test suite asserts it. A flag would be a
  third way to ask the same question.
- **No command to write a measurement.** An agent editing a TOML file needs no help. What
  it needed was the refusal, and that is in `measured()`.
- **No section filter on `nurb rules`.** 236 lines is cheaper for a model to read than a
  topic name is to guess, and a filter would invite writing doctrine that nobody prints.

#### Blockers
- (none)

---

### Phase 4: Viewer and human UX
**Status:** Complete (2026-07-26)

Drag a parameter and the part rebuilds. The loop it rebuilds in turned out to be the
real story.

#### Tasks completed
- [x] Parameters over the API, derived from the existing signature introspection
- [x] A slider and a number field per numeric parameter, with an inferred range
- [x] Live rebuild on drag, coalesced, in draft mode
- [x] "Write N defaults to <part>.py", which edits the file's keyword defaults
- [x] three.js vendored, so the viewer and `nurb render` need no network
- [x] All five overlays confirmed on screen: HUD, checks, error, reframe, empty
- [x] Section view, with a stencil cap
- [x] 24 new tests, 101 total

#### Results against the success criteria

| Criterion | Result |
|---|---|
| Dragging a parameter rebuilds live without touching the file | Yes. Dragged `grid_y` 2 to 3 with the mouse and watched the bbox go 94 to 136mm, the sixth socket appear, and `projection_ratio` fire at 3.24, the figure Phase 2 recorded. |
| The viewer works with networking disabled | Yes. The network log shows every request going to the viewer's own server, three.js included. |
| All four overlays confirmed on screen | Five, counting the checks panel. Each was made to happen rather than simulated: reframe by growing a part 6x in one save, the error overlay by a real chamfer failure, the empty state by an empty project. |

The loop, measured on this machine, in milliseconds:

```
                     build    tessellate + GLB        loop      was
hook, draft            29             1.3             ~30       ~92
hook, polished         58             2.6             ~61      ~166
shelf, draft          401            30.4            ~431      ~900
shelf, polished       605            30.4            ~635     ~1090
```

`nurb render` for all three parts went from 13.4s to 6.2s, and the test suite from 58s
to 20s, both without being touched.

#### Decisions made

- **Read the triangles by index instead of iterating them.** `builder._triangulate`
  replaces `Shape.tessellate` for the same reason nurb does anything else itself: the
  loop latency is the product. It reaches past build123d into OCP, which is a real cost
  in coupling, and it buys 22x to 109x on every rebuild, export and render. The
  vertices and faces are asserted bit-identical to what build123d returns, on all three
  parts, so the risk is confined to build123d changing an internal that this now
  duplicates. The right long-term fix is upstream, in a one-line change to build123d.
- **A guessed range, half the default to double it.** No part annotates a range and
  none should have to, so the viewer guesses. `0..2x` was the obvious alternative and is
  wrong: it puts `item_depth=0` and `chamfer_size=0` one drag away, and both are errors
  rather than designs. The guess is soft, and a number typed into the field widens it
  rather than being clamped, because the range is a guess and the number someone typed
  is not.
- **The type of the default is the annotation, and it has to be carried explicitly.**
  An `int` default is a count and steps by one; a `float` default is a continuous
  millimetre. This is the only signal available that does not require a parallel
  declaration, and it cost one character in two example files. It cannot be inferred in
  the browser: JavaScript has a single number type, so Python's `1.0` arrives as `1` and
  `Number.isInteger` says true. The first build of the panel had integer sliders on
  every chamfer for exactly that reason. `kind` now travels in the payload.
- **One rebuild in flight, carrying the newest values, instead of a fixed debounce.**
  The round trip spans 30ms on the hook and 431ms on the shelf, and no constant is right
  for both. The reply checks whether newer input arrived while it was away, so nothing
  queues and nothing is lost, and it clocks itself off whatever part is being edited.
- **Only the numbers go stale, never the mesh.** Fading the geometry already means "this
  build failed", and overloading it would make errors invisible. The HUD and the checks
  panel dim instead, after a 0.25s delay, so anything that lands inside one round trip
  never shows a state change at all.
- **A skipped write is reported, not refused.** `fit_coupon` defaults `side_clearance`
  to `SIDE_CLEARANCE`, and writing `0.31` over that name would keep the number and throw
  away the only record of where it came from. Refusing the whole write was the first
  design and it is a dead end: one such parameter would block every other parameter
  forever. It now writes what it can and says what it left alone and why.
- **The viewer sends only what differs from the file.** So the server's override map is
  exactly "what is not in the source", clearing it is an empty message, and a write that
  lands makes the corresponding override disappear on its own.
- **The section plane lives on the materials, never on the renderer.** A global plane is
  merged into every material including ones that set none, which would clip away the
  finding pins at the moment they matter and z-fight the cap against itself.
- **The websocket takes an Origin check.** It now accepts commands that write to the
  user's source, and any page in any tab can open a socket to localhost.
- **A stale override on a renamed parameter is dropped, not reported.** `UnknownParams`
  exists as its own exception so the server can tell this apart from a real build
  failure. The file is the authority, and reporting it as a broken part would name a
  parameter the user never typed.
- **Vendored r169, the version already in use, rather than the current r185.**
  Vendoring and upgrading are separate changes and only one of them belongs in this
  diff. r185 was checked and works. The upgrade path is written down next to the files,
  because the import graph has grown since r169 in two ways that both fail as a blank
  canvas rather than an error: r171 split `three.core.js` out of `three.module.js`, and
  later releases add `SkeletonUtils.js` to what `GLTFLoader` imports.

#### Findings

- **The parameter panel must not be rebuilt while a slider is being held.** The server
  echoes values back on every rebuild, and applying them blindly yanks the control out
  from under the finger mid-drag. Values from the server are applied to every control
  except the focused one, which is also why a file save updates the sliders (focus is in
  the editor) while a drag does not.
- **A failed build reports no parameters, and clearing the panel on that is a trap.**
  Set a slider to a value that breaks the build and the panel vanishes with it, leaving
  no way to drag back. Found by giving a part a validation guard and pushing a slider
  past it. The panel now survives an error unless it belongs to a different part.
- **Reset was rebuilding the panel from the entry it was trying to discard**, so every
  slider snapped straight back to the override. It goes through the same setters a drag
  uses now. The bug was invisible in code review and obvious the moment it was clicked.
- **The confirmation of a write was destroyed by the rebuild the write caused.** Writing
  changes the defaults, which changes the panel's signature, which rebuilds it. It
  mattered least for "wrote grid_y" and most for "left `side_clearance` alone, and here
  is why", which is the case a user needs to read.
- **`nurb new` into a running `nurb dev` filled the part list and left the canvas saying
  "no parts yet".** The first part of an empty project arrives as a `rebuilt` message,
  and nothing was selected, so nothing was ever painted. A pre-existing bug in the
  first-run path, found only because the empty state finally got looked at on screen.
- **`nurb dev` on a taken port dumped a raw `OSError` traceback**, which buries both
  what happened and the one-word fix. Found by running a second one. It now names the
  port and prints the flag.
- **The checks panel printed `projection_ratio` on top of its own message.** The rule
  column was 92px and the longest rule name does not fit. It had never been seen because
  all three example parts report clean, and it took a slider that pushed one into a
  warning to show it. Phase 3 found a defect in Phase 2's output the same way.
- **In draft mode a chamfer that cannot be built never fails**, because the polish pass
  is skipped entirely. `nurb dev` runs draft by default, so a part can look fine in the
  viewer and fail in `nurb build`. Not a defect, but worth knowing before trusting the
  live loop as proof that a part builds.

#### Found in review, after the phase read as done

Five defects survived building the feature and watching it work. Each was found by
reading the diff adversarially and then reproducing it, not by reasoning about it, and
each now has a test that fails when its fix is reverted.

- **`nurb render` would write to a part file.** It stands up a `Server` with no watcher
  and no queue, purely to serve one screenshot, and that server accepted the same
  websocket commands the dev server does: `params` crashed on the absent queue, and
  `apply` rewrote the user's source. A read-only server has to say so.
- **A command's `name` could escape `parts/`.** `{"type": "apply", "name": "../victim"}`
  resolved to a real file and rewrote it. The Origin check made this hard to reach and
  did not make it safe. A command names a part, never a path.
- **The kind of a parameter was read off its current value.** A float parameter whose
  slider landed on a whole number reported `int`, because JSON carries 2.0 as 2, so
  after a reload a chamfer came back with an integer slider. The whole point of the
  `chamfer_size=1.0` convention, undone by reading the wrong field.
- **Switching parts mid-rebuild killed every slider in the session.** The in-flight flag
  was a boolean, so a rebuild the user had walked away from never released it and every
  later drag was silently dropped. Both the in-flight and pending markers are part names
  now, which also stopped values collected for one part being sent under another's name.
- **The section cap was centred on the world origin.** A part's own origin is a modeling
  datum: the shelf lives entirely at `x <= 0`, so the cap left the far 49mm of its cut
  face bare and spent half its area on empty space. It is centred on the part's bounding
  box now. This one had been looked at on screen and passed, because the uncapped end was
  the far end.

The pattern in four of the five: **the happy path was verified and the second path was
not.** One part, one drag, one server, one origin. Every defect lived in the second of
something.

#### Deferred, deliberately

- **No drag-to-scrub on the labels.** A third input mode next to a slider and a number
  field, and `<input type=range>` already gives arrow keys, Home, End and PageUp/Down
  for free.
- **No parameter grouping.** Every tool that groups needs an authored declaration of the
  groups, which is the parallel declaration the contract forbids. Signature order is
  already authored order, and the examples use it: the mount interface first, geometry
  next, chamfers last.
- **No tolerance tiering during a drag.** Measured across tolerance 0.1 to 2.0: meshing
  time is flat and only the triangle count moves. It was never the cost.
- **No draft/polished switch on drag release.** Draft is worth about 20% of the build,
  and after the tessellation fix the build is nearly all of the loop, so the switch
  would buy ~100ms on the shelf at the cost of two states to reason about.
- **No `?section=` URL parameter.** `nurb render` has no use for a cut it cannot aim,
  and aiming it needs the bounding box the viewer already has.

#### Blockers
- (none)

---

### Phase 5: Full port, extract, tests
**Status:** Complete (2026-07-26)

The whole Notch catalog in nurb, with the fit line every card recorded by hand turned
into an assertion that runs.

#### Tasks completed
- [x] Ported the remaining 14 catalog parts
- [x] Collapsed the four catalog clones into variants
- [x] `nurb extract`, and then the extraction it found
- [x] pytest over every part: pitch, span, floor count, one solid, baselines
- [x] Parametrized flex test, upward, over every part
- [x] Check baselines asserted for every configuration
- [x] CI workflow
- [x] 178 tests, up from 105

#### Results against the success criteria

| Criterion | Result |
|---|---|
| All 16 parts build | 19 configurations out of 13 files, every one a single solid |
| `pytest` green across the library | 178 passed |
| Fit assertions catch a deliberately introduced pitch error | Yes, and the test that proves it is in the suite: a 0.1mm per interval error is reported by name |
| Exports match the Fusion STLs dimensionally | Every configuration matches its catalog card's bounding box to 0.05mm, which is the card's own rounding. The STLs live in the Fusion project and not in this repo, so the recorded box is the comparison. |

Every one of the 19 exports is watertight and a single body, with a genus that matches
the design rather than a constant: 5 for the pliers holder's five through-pockets, 1 for
the tape mount's slot, 0 for everything else. Phase 1's "euler 2" check was right for
three parts that happen to have no holes and wrong as a general test.

Two volumes could be checked against Fusion directly and both reconcile. The pliers
holder is 39.98cm3 against a recorded 40. The AkroBin rail is 60.29 against 60.1, and
the difference is entirely the channel side clearance, which was 0.5mm/side when Fusion
measured and is 0.25 now; the same arithmetic recovers the card's 1798mm2 of pad area to
the decimal.

**Three sliver baselines came out above what the Fusion cards recorded, and in each case
the port is right and the original was under-polished.** `shelf_basic` earns 6 rather
than 2 because Fusion's `Chamfer_Edges` was a hand-picked list that missed the lip's two
top ends; nurb selects by filter and finishes them. `holder_pliers` earns 4 rather than 2
because Fusion excluded the slab-front verticals to work around a selector limitation
OCCT does not have. Both were confirmed by reproducing the Fusion number on demand: put
the missed edges back out of the polish set and the count drops to exactly what the card
says. That is the difference between a port that disagrees and a port that knows why.

#### Decisions made

- **Four of the sixteen catalog entries are variants, not files.** `Hook - Utility - 1x`
  and `Hook - Utility Long - 1x` are the scissors hook at a wider cradle and a longer
  reach; `Shelf - Gridfinity 2x1` and `3x2` are the archetype at another grid, and the
  existing part already built both. A catalog entry is a name, some overrides and its
  own baselines, so that is what a variant is: a `[variants.<name>]` block in the card,
  which `build`, `check`, `card` and `export` all walk exactly as they walk the part's
  own defaults. The alternative was four near-copies of two functions, free to drift.
  Sixteen catalog entries now come out of twelve part files.

  The accepted baselines had to be per variant rather than per part, which is the
  detail that makes the shape right: the gridfinity sliver count is
  `4 * grid_x * grid_y + 2`, so 18, 10 and 26 across the family. A single number on the
  part would have been wrong for two thirds of it.

- **`nurb extract` reports and does not rewrite.** Lifting a run of statements into a
  shared function means choosing which of its free names become parameters and what the
  function is called, and both are judgements about what the thing *is*. The expensive
  part is noticing, and noticing is mechanical: it matches statement runs across part
  files up to alpha-equivalence, canonicalizing the names a part binds while leaving
  imported names alone, so two parts that wrote the same construction with different
  local names match and `Box(a, b, c)` and `Pos(a, b, c)` do not.

  Run over the finished port it found one thing worth having, and found it in six
  files at once: the plate, its channels and its dimples, written out character for
  character. That is `system.slab()` now, with `plate_width()` beside it. Three parts
  do not use it, and they are the test of whether the extraction was real rather than
  convenient: the scraper holder decouples its width from the bracket run, the AkroBin
  rail carries a rib above z=0 and steps its channels, and the calibration coupon
  sweeps the clearance. A helper with a flag for each of those would have been the
  wrong abstraction wearing the right name.

  **The extraction is provably geometry-neutral.** Every configuration was fingerprinted
  by bounding box, volume, face count, solid count and sliver count before and after,
  and the two are identical. That is what makes a refactor of thirteen part files
  something other than an act of faith.

  What it reports now is 2-statement runs, all of them idiom rather than geometry: `if
  draft: return body`, a `mid = span(...)` followed by a list comprehension. Those are
  the shape of the part contract, not duplication, and lifting them would make every
  part harder to read to save nothing.

- **Notch's bins are hardware, so they went in `measurements.toml`.** The AkroBin rail's
  8.75mm standoff is the leg thickness plus the slot depth, both off Josh's bins with
  calipers, and neither can be derived. The file was for the bracket; it is for anything
  the library has to mate with.

#### Findings

##### 1. A structural chamfer goes across a weld, not around it

The two utility hooks want a 20mm cradle on a single 25.16mm bracket, which leaves
2.58mm of slab standing either side of the arm. Phase 1's hook chamfered the whole
arm-to-slab junction, all three edges of it, and that set cannot build at any cradle
wider than 17mm: the 3mm band has to land on that strip, and then the slab's own front
corner needs another 1mm of it for the polish pass.

Measured, at `chamfer_size` 1.0: builds with 1.08mm of strip left, fails with 1.00mm.
Flush, with no strip at all, builds again. So the rule is `margin > chamfer_size` or
`margin == 0`, and the part raises rather than letting OCCT say it.

The fix is not a smaller chamfer. Relieving only the full-width edge where the arm's
top meets the slab keeps the family's 3mm at every cradle width, holds the sliver
baseline at 6, and leaves the slab's exposed corners polished. The two vertical legs
carry almost none of the moment; they were in the set because in Fusion selecting "the
junction" picks up the whole chain.

Two wrong answers came first, and both build:

1. `structural_chamfer` 1.5 on the wide variants. It builds and `nurb check` fires
   `concave_cosmetic` at it, because a 1.5mm facet in an inside corner is close enough
   to polish that the rule cannot tell, which is the rule correctly noticing that a
   1.5mm relief is barely a relief.
2. Leaving the slab's front verticals out of the polish pass instead. Also builds, and
   trades a chamfer on the most-handled exposed edge on the part for one on an inside
   corner nobody sees. The doctrine ranks those the other way round.

##### 2. `concave_cosmetic` was firing at the geometry its own message prescribes

The rule looks for a strip about as wide as the polish pass makes whose long edges are
all concave. Its limit was **twice** that width, and twice is what a 2mm structural
chamfer measures: 2.6mm for the chamfer face itself, 1.9mm for the wall left standing
between two of them. So it fired six times at `mount_tape_measure` and again at
`mount_akrobin_rail`, both of which use a 2mm relief for the reason the doctrine gives,
because the material is 2mm thick. Two shipped, printed parts, told they had polish in
an inside corner at exactly the spot where they had put a deliberate relief.

Phase 2's own bar catches this: a rule that fires at a part which prints fine is a bug
in the rule. The fix is that a relief is *bigger* than polish, and being bigger is the
only thing that distinguishes the two, so the window is now the strip a polish chamfer
leaves plus 15% rather than twice it.

It cost a true positive: a 1mm chamfer in a concave junction shallower than about 105
degrees now leaves a strip wide enough to read as deliberate. That is the right way
round to be wrong. `polish_edges` vetoes concave edges outright, so this rule is the
backstop for a part that rolls its own selector, and a backstop that cries wolf at
correct geometry gets switched off.

Found twice independently, once here and once by the agent porting the tape mount,
which is the useful part: the port is a second opinion on Phase 2's calibration, and it
had only three parts to calibrate against.

##### 3. The one-edge form of the clearance rule, which the doctrine was missing

The kernel rule everyone knows on this project is that two chamfered convex edges need
more than `2 * chamfer_size` of face between them. Three parts hit the other half of it
independently and measured the same threshold: **one chamfered edge needs more than
`chamfer_size`**, and it bites wherever a polished edge sits beside something that is
never polished. A concave junction. A structural chamfer's toe. A pocket wall.

- the hook's slab strip beside the arm: builds at 1.08mm, fails at 1.00mm
- the pliers holder's pocket back wall against the 3mm relief: `structural_chamfer`
  builds at 0.99 and fails at 1.00 with 1.0mm of face
- the tall-tools slab reveal above the block: builds at 2mm, fails at 1mm

It looks like plenty of room, which is why all three found it the hard way. It is in
the doctrine now.

##### 4. A part can be wrong in a way every number agrees with

Porting the needle-file holder, an agent drew the keyhole throat profile clockwise.
`Polygon` takes its face normal from the winding and `extrude` follows it, so the cut
went downward, landed a millimetre under the part and removed nothing. What came out was
four plain round holes with no throats and no flared mouths: a snap-fit clip with
nothing to snap.

Bounding box, solid count, sliver count, channel fit and `nurb check` were all exactly
what a correct part reports. What caught it was measuring one seat: the cylindrical face
came back 65.97mm2, a full 360 degrees, and a seat with a throat cut into it can only be
248.

The doctrine already says "it built" is not verification, and this is the sharpest case
of it in the project so far. Every check that exists passed. The thing that failed was
the one feature the part is for.

##### 5. `bed_bevel` could not tell a corbel from a chamfer

The rule looks for a face touching the build plate that is neither flat on it nor square
to it, on the reasoning that such a face can only be a bevel. The calipers holder
disproved that: the doctrine's own corbel is a 45 degree underside, and where it lands on
the plate rather than dying into the body it is exactly such a face. 46mm2 of prescribed
structure, reported as polish.

Rise separates them: a bottom chamfer rises by its size, measured at 1.00, 2.00 and
3.00mm, against 4.29mm for the corbel. Rise is also independent of the edge's path,
where plan-view reach is not: a 1mm chamfer around a 20mm cylinder has a 20mm bounding
box in both horizontal directions and is still only 1mm high.

The same part turned up a real defect on the way, which is the reason to keep the rule
rather than weaken it: the 1mm polish on the corbel's own side edges ran down to the
plate and laid two 9.3mm2 tilted facets into the first layer. `polish_edges` vetoed an
edge lying in the bottom face and allowed a vertical corner that merely ends there, which
is right, and let the case in between through. It vetoes that now.

##### 6. The second way a chamfer batch dies, where bisecting does not help

Every chamfer failure this project had seen was a clearance problem, and the standing
advice is to bisect the set. The parts bin found one that is not: an edge whose end lands
on a vertex with four faces around it but only three edges between them. Two of those
faces touch at a point without sharing an edge, and OCCT has no cap for that corner.

It fails alone, on a clean body, at every length from 2.4mm down to 0.05mm. So both of
the usual moves report nothing: bisecting isolates a single edge that still fails, and
"try a smaller length" never reaches a length that works. The fix is to chamfer in two
passes, letting the first give those two faces a real edge to meet along, then reselect
from the result.

##### 7. A part with text on it is not the same part on another machine

CI is the first time this library built anywhere but one Mac, and it failed three tests,
all of them the calibration coupon. The coupon carries a raised label, because four of
them come off one plate looking identical and a gauge you cannot identify is no use. A
label is glyph outlines, glyph outlines come from a system font, and the font on the
runner is not the font here. Same part, 2600.6mm3 with 88 faces and 65 slivers on one
machine, 2601.0 with 83 and 60 on the other.

Nothing about the fit moves, which is the only surface a gauge has to get right. What
moves is everything the card records, and what `min_wall` finds: the ray cast reaches the
label before it reaches anything structural, so it returns 0.500 on one machine and 0.480
on the other, at different places in the same word.

The first attempt at a fix was to widen the rule's slack, and it was the wrong shape:
those two numbers are not one number with noise on it, they are measurements of different
geometry. The card sets `min_wall = 0` now, which says the rule cannot measure this part,
and states the walls that actually matter and are not in doubt. The AUTO-block test skips
a part that renders text and says why.

**The doctrine already said no text labels on parts, for looks.** It has a second reason
now, and it is a stronger one: text makes a part unreproducible.

Two things generalize past the coupon. A checker's thresholds are claims about a
measurement, so the tight ones need to be stable across kernel builds, and `min_wall` now
carries one percent of slack for that reason alone. And **a card is a record of what one
machine built**, which is fine as long as nothing asserts it somewhere else, and CI is
exactly somewhere else.

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

> **Wrong, and Phase 4 measured why.** None of those three levers was the answer and
> none was needed. Almost all of that "tessellation" time is a Python iterator, not
> geometry: `Shape.tessellate` reads triangles with `for t in poly.Triangles()`, and
> OCP's iterator over `Poly_Array1OfTriangle` costs 536ms for the shelf's 7790
> triangles against 6.8ms to read the same array by index. OCCT's actual meshing is
> 10ms. Reading by index gives bit-identical vertices and faces 22x to 109x faster, and
> the shelf's loop went to ~430ms draft without touching tolerance, caching, or the
> rebuild path. The lesson is narrower than the finding: **a number this far off the
> work being done is a measurement of the wrapper, not the workload.** Profile inside
> the thing you are about to design around.

### 4. `new_edges` is the algebra-mode `Select.LAST`

`new_edges(before, combined=after)` returns exactly the edges an operation created.
Used for the structural chamfers and to exclude them from the cosmetic pass. This is
what makes the parts survive a `bracket_count` flex, and it is a genuine improvement
over the strict-ordering rule Fusion needed. CLAUDE.md's preference for it is correct
and now has evidence.

---

## Session log

### 2026-07-27: The viewer shows the polished part, and says so

The polish pass was invisible from the user's chair: the dev server defaulted to `draft=True`, so every build the viewer ever painted was the unchamfered draft, and the chamfers existed only in the export path. A user watched a raw block all session, downloaded an STL, and nothing anywhere ever mentioned polish as a thing that was happening or could happen. `nurb dev --polish` existed but opt-in correctness is the wrong polarity for a saving measured at 20%: what the user judges on screen should be the part that prints. The default flipped to polished, and the escape hatch is now a `polish` button in the viewer toolbar, lit by default, which flips draft mode over the websocket and rebuilds the whole project so no part is left in the old mode. `nurb dev --draft` starts with it off for whoever wants the fastest loop, and the sync message carries the mode so the button never lies after a reconnect. `--polish` is gone. The skill shims (skill.md, AGENTS.md, SKILL.md, all one body) gained a paragraph telling the agent to keep the polish pass through its edits and to say so when handing the part over, because the user can only ask for sharp edges if they know the chamfers are there on purpose. A side effect worth naming: the checks pass in `nurb dev` now runs on polished geometry, so the sliver findings the viewer shows finally match what `nurb check` and CI see. Verified live on a scratch project: template box builds at 23931.3mm3 with the chamfers on screen, the button flips it to exactly 24000.0 and back, and the draft rebuild is visibly faster (0.8ms against 3.8ms).

### 2026-07-27: The viewer says what version it is, and whether PyPI has a newer one

`__version__` now comes from `importlib.metadata`, so `pyproject.toml` is the only place the number lives; the old second copy in `__init__.py` was already one release away from drifting. The dev server sends the installed version in the sync message and the viewer shows it in a sidebar footer next to github and send-feedback links. Once a day (localStorage remembers) the viewer asks `pypi.org/pypi/nurb/json`, which sends `Access-Control-Allow-Origin: *`, and a newer release turns the badge into `v0.1.0 → 0.2.0` in the accent color with the upgrade command in the tooltip. The server does the same check on `nurb dev` startup, in a daemon thread with a one-day disk cache under `~/.cache/nurb/`, and prints one stdout line, because the primary user is an agent that reads stdout and never opens the page. Every failure path is silence: offline, slow, or odd response, the badge is just the version. `?bare=1` renders never fetch, so `nurb render` in CI stays off the network, and the check lives in `Server.run()`, which `nurb render`'s `_host` does not call. The "viewer works offline" rule in CLAUDE.md was reworded from a ban on network to what it always meant: everything the viewer *needs* is vendored, and a nudge that degrades silently is allowed.

Three items, and the middle one produced this session's finding.

**Printer profiles ship in the package.** `src/nurb/printers.toml` holds machine facts,
a project names one in `printer.toml` at the root, and `nurb check --printer x` tries
another machine without touching the file. The split the docs kept circling is now
enforced by layering: Context defaults, then the profile, then the file's own overrides,
then the card, so a card keeps winning for exactly what its part has justified and
nothing else. The watcher now rebuilds the project when `printer.toml` or
`measurements.toml` changes; the second was an existing gap the first exposed, since
editing a measurement always could change geometry and never triggered a rebuild.

**`min_wall` grew its inscribed sphere, and the naive version was disproved before it
shipped.** A tangent sphere at every probe, which is what the literature describes,
reads curvature as thickness: every detent dimple in the library reported its bowl's
0.8mm, and the shelf reported 0.033mm at a knife edge. Values like that do not measure
walls and cannot be carded. What shipped instead is a correction of the ray: any chord
thin enough that the true section could still be under `min_wall` gets the shrinking
ball, on exact `distance_to_with_closest_points` queries so the check stays on the
solid, and the gate follows from the ray's own exit filter (an accepted chord leaves
within a 0.3 cosine, so a chord past `min_wall / 0.3` cannot be hiding a failure).

The filter that matters was found by a part, again. The scraper measured 1.07mm sitting
in a 2.3mm web: a sphere wedged between the channel floor and the detent dimple's bowl,
two surfaces bounding the same air. The fix is the ray's own rule applied to the
sphere's contact, whose normal comes free as `(q - c) / r`: the far surface has to face
back at the measurement, same 0.3 floor. Algebraically that is `|w|^2 / 2r^2 - 1 > 0.3`,
one comparison. With it, every library value lands exactly on its card or above:
flat-parallel parts unchanged at 1.0, akrobin's 1.98 chord corrected to a true 1.64
diagonal, the spool 1.42 to 1.18, the shelves 1.0 to 0.84 at the mouth chamfers against
a 0.7 card. Nothing fires. The whole-library strict check went from ~9s to ~14s, which
is what "correct and expensive" was supposed to cost. The skew case has a hand-derived
test: a wedge where the shortest chord is 10.0mm and the tangent sphere is
2 * 8 / 1.8 = 8.89mm, with the limit between them.

**The viewer is the configurator.** `/export/<part>.stl|step` builds at whatever the
sliders hold, polished regardless of the draft economy, behind the same lock as the
rebuild loop so two OCCT builds cannot overlap. Verified in a real browser: slider from
200 to 150, download, and the STL measures 150 x 200 x 10 and is watertight. What
remains of "publish a configurator" is hosting without a running kernel, which is a
different problem and stays on the list; MakerWorld's customizer runs OpenSCAD, which
build123d does not transpile to, so that path is closed rather than pending.

### 2026-07-27 (later): `nurb skill`

The discovery chain used to start inside a project: `nurb new` seeds AGENTS.md, the
agent finds `nurb rules`. Before a project exists, an agent has never heard of nurb, so
`nurb skill` prints an installable skill for whatever harness the user's model lives in:
frontmatter trigger on top ("the user wants a printable part"), the agents.md shim
underneath. Printed rather than installed, because every harness keeps instructions
somewhere different and those paths change faster than this tool should chase. One body
serves all three copies (packaged skill.md, repo SKILL.md, agents.md), and a test
asserts the containment instead of hoping for it.

### 2026-07-26 (last): Phase 5

Fourteen parts is the first piece of work here big enough that how it was done matters as
much as what came out. It was done as ten parallel ports, one agent per part, each given
the Fusion card, the datums, the verified build123d facts, and a verification list it had
to answer in full: bbox against the card, one solid, floors on pitch, flex upward,
predict the sliver count *before* measuring it, run the checks, render it and look.

Two things about that are worth keeping.

**Predicting the baseline first is what turned the port into a test.** Six of the ten
predictions were exactly right, and the interesting ones are the four that were not.
`shelf_basic` predicted 6 against a card that said 2, went and reproduced the 2 by
putting the missed edges back, and so could say which was wrong rather than guessing.
`bin_small_parts` predicted 2 and measured 0, and the reconciliation is a fact about
chamfer ordering nobody would have gone looking for. A number written down after the
fact would have taught none of that.

**Every rule bug in this phase was found by a part, not by review.** `concave_cosmetic`
firing at a prescribed 2mm relief, `bed_bevel` firing at a prescribed corbel, the
bottom-face veto's gap, two new kernel rules. Phase 2 calibrated those rules against
three parts and they were clean; thirteen parts is a different instrument. The general
version: a checker's false-positive rate is a function of how much geometry it has seen,
and the only way to find out is more geometry.

The thing that nearly went wrong is worth recording too. Everything the runtime measures
about the needle-file holder was correct while the part had no working clip in it, because
a profile drawn clockwise extruded the wrong way and cut air. Bounding box, solid count,
sliver count, channel fit, all eight rules: green. What caught it was measuring a single
face and finding 360 degrees where 248 belonged.

### 2026-07-26 (later still): Phase 4

The phase's biggest change was not on its task list. Researching how other tools debounce
an expensive rebuild turned up the claim that build123d's tessellation is mostly a slow
iterator, which contradicted a Phase 1 finding recorded as a measurement. Profiling it
first, before designing anything around a ~1s loop, is what made the rest of the phase
easy: the debounce question mostly dissolved once the shelf answered in 431ms instead of
900ms. **The order that mattered was measuring the constraint before designing for it**,
and the only reason the constraint got questioned is that a recorded number looked too
large for the work it claimed to describe.

Everything in the panel was verified by clicking it, and that is where the bugs were.
Reset, the write confirmation, the panel disappearing on a failed build, the first-run
empty project and the overflowing rule column were all invisible in code and immediate
on screen. The section view went the other way: it looked broken in a screenshot for
several minutes and was correct all along, because a Notch shelf's platform sits low and
its back plate rises, so a mid-height cut leaves the sockets standing. Hiding the cap and
the stencil writers and looking at the clipped mesh alone is what settled it. **A
screenshot is evidence of what is on screen, not of what it means.**

### 2026-07-26 (later): Phase 3

Order of work: doctrine, then the pieces that reference it. Writing `doctrine.md` first
was the right call for a reason that was not obvious going in: assembling the whole
doctrine in one place is what surfaced that the plan's `measurements.yaml` needed a YAML
parser nobody had, and that the AUTO block's parameter list contradicted the part contract
three sections above it. Both would have been written before being noticed otherwise.

The `measured()` refactor of `system.py` was done after `nurb card` existed rather than
before, which turned it from a risky edit into a checked one: the cards record exact
bounding box, volume, face count and sliver count, so moving six constants out to
`measurements.toml` and getting byte-identical blocks back is a real regression test. It
was written for documentation and paid off as verification within the hour.

Verified by looking, not by reasoning: five renders read back as images (three parts, a
top view, a `--chrome` view), the missing-measurement error read back from a real CLI run
twice, and the stale-card test watched to fail on a perturbed digit before being trusted.
The `KeyError` formatting bug and the wasted screenshot framing were both invisible in
code and obvious on screen.

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

Phase 3:

```
src/nurb/doctrine.md              new  the single source, printed by nurb rules
src/nurb/card.py                  new  the AUTO block: facts, graft, thin
src/nurb/measurements.py          new  measured(), MeasurementError
src/nurb/render.py                new  headless PNG, the only browser dependency
SKILL.md, AGENTS.md               new  thin shims, no doctrine
examples/notch/measurements.toml  new  six measured bracket dimensions with provenance
examples/notch/system.py          six constants now come from measured()
examples/notch/parts/*.md         AUTO block grafted under each title
src/nurb/cli.py                   rules, card, render
src/nurb/__init__.py              measured() joins the part vocabulary
src/nurb/viewer.html              ?part= ?view= ?bare, window.__nurb.ready, tighter
                                  framing for a still, Z-up top view fixed
pyproject.toml                    render extra, doctrine.md in the sdist
tests/test_card.py                AUTO block, plus "the real cards are current"
tests/test_measurements.py        new  every way a measurement can refuse
tests/test_render.py              new  two views of a part are two different pictures
```

Phase 4:

```
src/nurb/edit.py                  new  writes values back into a part's keyword defaults
src/nurb/vendor/three/            new  r169: build, three addons, LICENSE, a README
src/nurb/builder.py               _triangulate reads triangles by index, 22x to 109x;
                                  params rows carry default, value and kind;
                                  UnknownParams so a stale slider is not a broken part
src/nurb/server.py                per-part overrides, websocket commands, /vendor route,
                                  Origin check on the socket
src/nurb/viewer.html              parameter panel, one-in-flight rebuilds, section view
                                  with a stencil cap, vendored importmap, five overlays
                                  verified, first part in an empty project is selected
src/nurb/render.py                the render server takes the same Origin check
src/nurb/cli.py                   a busy port says so instead of raising OSError
src/nurb/doctrine.md              a continuous dimension is written as a float
pyproject.toml                    vendor/ in the sdist
examples/notch/parts/*.py         chamfer sizes are floats, so their sliders are
tests/test_edit.py                new  what it writes, and what it refuses to touch
tests/test_params.py              new  signature to payload to override and back
README.md, CLAUDE.md              three.js redistribution, layout, current state
```

Phase 5:

```
examples/notch/parts/            10 new parts and their cards: shelf_basic,
                                 holder_pliers, holder_tall_tools, holder_calipers,
                                 holder_bambu_scraper, holder_needle_files,
                                 holder_filament_spool, mount_tape_measure,
                                 mount_akrobin_rail, bin_small_parts
examples/notch/system.py         slab() and plate_width(), extracted from six parts;
                                 polish_edges also vetoes a sloped edge reaching the bed
examples/notch/measurements.toml the AkroBin's three measured dimensions
src/nurb/extract.py              new  duplication across parts, up to alpha-equivalence
src/nurb/checks.py               configurations() reads a card's variants; a relief is
                                 not polish (concave_cosmetic); a corbel is not a
                                 chamfer (bed_bevel)
src/nurb/card.py                 the AUTO block carries a line per variant
src/nurb/cli.py                  build/check/card/export walk variants; extract
src/nurb/doctrine.md             variants; the one-edge clearance rule; the four-faces
                                 three-edges chamfer failure
tests/test_notch_fit.py          new  the hanging interface, and a pitch error it catches
tests/test_extract.py            new  alpha-equivalence, and what must not match
.github/workflows/test.yml       new  pytest, then nurb check --strict
hook_scissors, shelf_gridfinity  the structural chamfer goes across the weld; the other
                                 four catalog entries arrive as their variants
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
| The doctrine is a file in the package | `nurb rules` prints it, harness files point at it. A copy in `SKILL.md` and another in `AGENTS.md` would drift within a phase, and the drifted copy is the one an agent reads. |
| The AUTO block is idempotent and holds no timestamp | It makes the block a cache rather than a competing source of truth: no diff unless the geometry moved, so `git diff` is the staleness check and a test can assert cards are current. |
| The card does not restate the parameters | The signature is the parameters. Restating them anywhere, including in generated text, is the `PARAMS` dict the contract forbids. |
| A dimension that was measured lives in `measurements.toml`, and asking for a missing one raises | An invented dimension builds, checks clean, exports and prints. Nothing downstream can catch it, so the only place to catch it is at the moment of asking. |
| Rendering reuses the viewer rather than an offscreen stack | The image is then what a human would see, and nothing new has to know how to light a scene. It costs an optional browser, which is why it is an extra. |

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

**From Phase 3:**

- **Build the recorder before the refactor.** Moving six constants out of `system.py`
  looked like an edit that needed careful review. Done after `nurb card` existed, it
  needed none: the cards hold exact bounding box, volume, face count and sliver count, so
  identical blocks afterwards is proof nothing moved. A document written to explain a part
  turned into the regression test for changing it, in the same session.
- **Assemble the whole doctrine in one file before writing the code that references it.**
  Two of the plan's own instructions did not survive being written down next to each other:
  `measurements.yaml` needed a parser nobody had, and listing parameters in the card
  contradicted the part contract stated three sections above it. Both would have been built
  before being noticed.
- **A message inside a `KeyError` is not the message you wrote.** `KeyError` reprs its
  argument, so a worked example with newlines in it prints as one quoted string full of
  backslash-n. Any other exception class formats it properly. Invisible in code, obvious
  the first time the command was run.
- **A flag whose only justification is a feature nobody has exercised is untested by
  construction.** `--chrome` exists to show findings in place, and all three example parts
  report clean, so the pins it renders had never once been looked at. Building a throwaway
  part that deliberately fails a rule took four lines and found that half the pins were
  invisible. Where a codebase is clean by design, the clean cases cannot verify the code
  that handles the dirty ones, and something has to be made dirty on purpose.
- **Non-ASCII in generated output is a portability bug, not a typography choice.** It only
  shows up on a machine with a different locale, which is to say on somebody else's, which
  for source-available code is most of them.

**From Phase 4:**

- **Profile the constraint before designing around it.** The whole phase was planned
  against a ~1s rebuild that Phase 1 had measured and written down. Almost all of it was
  a Python iterator inside a library call. A recorded number is evidence about the code
  that produced it, not about the work it names, and this one was 50x larger than the
  geometry it claimed to describe. The tell was available in Phase 1: 620ms to walk 7790
  triangles is not a plausible cost for walking 7790 of anything.
- **The clean cases cannot verify the code that handles the dirty ones.** Phase 3 wrote
  this down about findings pins and it repeated here almost exactly: the checks panel's
  rule column had been too narrow since Phase 2, and could not be seen until a slider
  pushed a part into a warning. The same phase found it twice for the same reason.
- **Interactive state has to be clicked, not read.** Reset, the write confirmation, the
  panel vanishing on a failed build and the blank canvas on a fresh project were four
  bugs in code that reads correctly. Every one of them took a single click to find and
  none of them would have been found by re-reading the file.
- **A screenshot proves what is on screen, not what it means.** The section view looked
  broken for several minutes because a mid-height cut through a Notch shelf leaves the
  socket platform standing, which is correct and looks like nothing happened. Isolating
  the mesh from the cap and the stencil writers answered in one step what squinting at
  three screenshots did not.
- **Guard the dead ends, not just the errors.** Two designs here were correct and still
  wrong to ship: refusing an entire write because one parameter is a named constant, and
  clearing the parameter panel when a build fails. Both leave a user in a state with no
  way out except editing the file by hand, which is the thing the panel exists to avoid.
- **A type distinction does not survive JSON.** Python's `1.0` is JavaScript's `1`, and
  `Number.isInteger` agrees. Anything the browser needs to know about a Python type has
  to be sent as data, not recovered from the value.
