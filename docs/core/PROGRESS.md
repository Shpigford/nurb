# nurb core progress

## Status: Phases 1, 2 and 3 complete. Phase 4 next.

**The kernel question is answered: OCCT builds both parts and both match the Fusion
originals dimension for dimension.** The architecture stands. `nurb check` now runs
seven rules against them, clean, and has already caught one real defect in what
Phase 1 shipped. Two assumptions carried
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
