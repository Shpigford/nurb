# nurb design doctrine

Printed via `nurb rules`. This file is the single source; harness files point at it
rather than repeating it.

These are standing rules for FDM-printed parts. Most are physics, so they outlive any
particular CAD kernel. Rules specific to OCCT are marked as such and were measured, not
reasoned.

## Form follows function

- These rules are defaults for printability and visual consistency, not requirements
  that outrank the part's job.
- A working mechanical fit or a usable product always wins over a rule here.
- Several rules below can conflict with function: support-free printing, overhang
  limits, corbel angle, chamfer placement. Treat them as guidance, not constraints to
  design around.
- When a rule would force a functional compromise, don't contort the geometry to
  satisfy it. Ask the user for their preference and state the tradeoff.

## The part contract

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

- Keyword defaults are the parameters. Never add a parallel `PARAMS` dict; the two
  would drift.
- Write a continuous dimension as a float, and a count as an int. The viewer reads the
  type to decide the slider: `bracket_count=4` steps by one, `chamfer_size=1.0` moves
  continuously.
- `draft` is injected by the runtime, never passed by a caller. When true, skip the
  polish pass.
- Return one solid. A function that returns two loose bodies still reports a plausible
  bounding box and still exports, so nothing downstream catches it.
- Refuse a configuration that cannot work with `reject`, never a bare exception.
  - `reject("drill_hole_width 14 is under the 14.27mm pin vise plus print shrink: raise it above 14.77", param="drill_hole_width")`
  - `param` names the offending parameter so the viewer marks its slider.
  - The viewer shows a refusal in amber with the last good geometry on screen. A bare
    exception reads as a red traceback, as if the part were broken.
  - Guard only what would print wrong or not build at all. Taste stays a slider.

## Printability

- Minimum wall 1 to 2mm, except where fit geometry says otherwise. Don't round
  fit-critical dimensions for tidiness.
- Avoid floating features that aren't required by a mechanical constraint. Parts print
  bottom-down, building in +z, so an ungrounded feature (a shelf, loop, or band with a
  gap underneath) usually wants a corbel, a tilt, or support. But if the design
  genuinely needs the overhang, that's how it is. Don't distort the geometry to avoid
  it.
- Support material is a user decision, never a default. Try, in order: corbel the
  feature, tilt the part, or mark it with `supported(shape, why)` (one feature) /
  `supports = true` in the card (whole part). Say what the corbel or tilt costs before
  assuming they're free wins, and ask before adding supports.
- A counterbore prints mouth toward the bed, which floats its ceiling: the screw-head
  shelf lays flat over the open pocket, and the smaller hole's rim is drawn on air.
  This is the `hole_ceiling` finding, and it fires on any hole rising out of a bridged
  roof, not just screw pockets. Cut it with
  `counterbore(hole_dia, head_dia, head_depth, depth)`, which steps the transition
  through two crossed sacrificial bridge layers so the pocket prints support-free.
  Never answer `hole_ceiling` with supports inside a pocket nobody can clean.
- Corbel rule: carry an overhang on an angled underside instead of running material to
  the bed.
  - A short vertical tip below the floor, then an angled plane falling back
    into the body.
  - Keep the angle within whatever overhang limit the printer/material can hold.
    Matching the part's own facet system is fine when one is already established, but
    don't force a fixed angle if it compromises the design.
  - Aim for every layer overhanging by at most about half a bead, bonding to the wall
    behind it.
- A large first layer (past about 20,000mm2) risks peeling at its corners as it cools.
  `warp_risk` names the corners likely to lift.
  - Fix it in the outline: round vertical corners at 8mm or more, and give a big plate
    a ribbed floor instead of a solid slab.
  - Material tightens the threshold: ABS, ASA and PC contract more than PLA or PETG.
    Name the material in `printer.toml` so `warp_risk` accounts for it.
  - At the extreme, a bed-covering part in ABS, ASA or PC is the wrong material.
    Switch to PETG or PLA rather than widening the brim.

### Holes

- Small or tight-tolerance holes need a fit coupon before the full part prints. Don't
  assume a modeled diameter matches the printed one.
- Vertical bores print undersized by a few tenths, machine- and material-dependent. Use
  the fastener table's medium-column slack even for a non-screw rod. When the diameter
  genuinely matters, us a coupon or model half a millimetre under and drill to size.
- A horizontal hole's crown is a bridge and sags into the bore. Prefer standing the
  hole vertical. When the axis can't move and roundness matters, roof it with two
  chords meeting above the crown at the overhang angle (a teardrop).

### Fasteners

Take these from the table instead of measuring or guessing standard hardware.

| Thread | Clearance hole, close | medium | Cap head dia | Cap head height | Nut across flats | across corners | Nut thickness |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M2 | 2.2 | 2.4 | 3.8 | 2.0 | 4.0 | 4.4 | 1.6 |
| M2.5 | 2.7 | 2.9 | 4.5 | 2.5 | 5.0 | 5.5 | 2.0 |
| M3 | 3.2 | 3.4 | 5.5 | 3.0 | 5.5 | 6.1 | 2.4 |
| M4 | 4.3 | 4.5 | 7.0 | 4.0 | 7.0 | 7.7 | 3.2 |
| M5 | 5.3 | 5.5 | 8.5 | 5.0 | 8.0 | 8.8 | 4.7 |
| M6 | 6.4 | 6.6 | 10.0 | 6.0 | 10.0 | 11.1 | 5.2 |
| M8 | 8.4 | 9.0 | 13.0 | 8.0 | 13.0 | 14.4 | 6.8 |

In mm. Clearance is ISO 273, cap head is ISO 4762 socket head, nut is ISO 4032 hex.
Across corners is the dimension a round pocket has to clear; an M3 nut is 5.5 across
the flats and will not go into a 5.5 hole.

- Default to the medium clearance column, not close. A printed hole comes out
  undersized, so close is a fit you earn with a coupon, not one you assume.
- Cut a screw pocket with `counterbore()`, never a plain wider hole.
- A nut pocket is a hex prism; `counterbore()` cuts a cylinder, so model it by hand:
  `extrude(RegularPolygon(across_corners / 2, 6), thickness + 0.2)`, or a round pocket
  at across-corners + 0.2 if the nut is free to spin. Add about 0.2mm slack across the
  flats, and rotate so a flat rather than a point faces up. It floats its own ceiling
  the same way a screw head does, so the same two-bridge-layer trick applies.
- Heat-set insert boss diameter is set by the vendor's insert, not by a standard.
  Ask or measure, and record with `measured()`.
- Never model a thread under M5. Above M5 a modeled thread is still a choice the card
  justifies, never a default.
  - Below M5, the options are a captured nut, a heat-set insert, or a self-tapping
    hole sized for the screw to cut its own thread.
  - Ask the user which they prefer when the choice matters (assembly/disassembly,
    cost, hardware on hand).
- A loaded hole wants a wall thickness equal to its fastener diameter (an M5 screw
  wants 5mm of surrounding material), or the boss splits along a layer weld as the
  screw seats.

### Fits between printed parts

The fastener table covers steel meeting plastic. Two printed faces that work together
get a designed gap of their own, sized by what the pair does and stated as the total
extra on the opening.

| Fit | Extra on the opening | What it feels like |
| --- | --- | --- |
| press | 0.1 | driven together once, holds by friction |
| snug | 0.2 | slides on by hand, no rattle |
| moving | 0.3 | swings and slides through its whole travel, the hinge floor |
| free | 0.5 | drops in every time, on any printer, in any material |

In mm.

- The table is a starting point, not a substitute for a coupon on anything
  fit-critical.
- Below 0.1mm is a bind that varies by machine, not a tighter press.
- A moving pair never ships below 0.3mm; 0.2mm that swings freely on the printer that
  made it seizes on the next one.

## Print orientation

Parts print the way they are modelled, +z up. Orientation becomes a decision in two
cases: an overhang a corbel can't carry without disfiguring the part, or a load that
wraps a corner, where no flat orientation keeps every member strong.

- Overhang fix order is a starting point, not a mandate:
  - Try a corbel first. It's local and free.
  - If the corbel would hurt fit, function, or a surface the user cares about, ask
    whether they'd rather have the corbel's shape or accept supports. Don't corbel
    through a functional problem.
  - Tilt the whole part when a corbel would fight the whole design.
  - Supports come last, are the user's call, and get marked with `supported()` on a
    feature or `supports = true` on the card.
- Layer bonds are about half of in-plane tensile strength (varies based on material).
  - A part loaded across a layer weld in its natural orientation may need a different
    orientation to keep that load in-plane.
  - Supports can be the right tradeoff here: choosing an orientation for its layer
    strength, then accepting supports and a worse finish where that orientation
    creates an overhang. Raise this as an option, not a rule.
- `stand(part, tilt, axis, facet)` rotates the part, seats it, and shaves the down
  corner flat, because a part standing on an unshaved corner meets the bed along a
  single extrusion line, which peels.
  - The facet is 2mm minimum, measured across the flat.
  - 45 degrees is a common tilt, not mandatory. A shallow part stands at whatever
    angle keeps everything inside the limit.
  - Run the polish pass before standing, in the functional orientation.
- Stand a part on the corner that grounds every region, and prefer the lowest stance
  that does.
  - The sign of the roll isn't obvious by reasoning; check it. The same part rolled
    the other way can ground the same regions and stand much taller on the same
    facet.
  - Watch for the "tent" stance: a region floats even though every face reads at a
    legal 45 degrees. `nurb check` catches this via `floating`/`stability`; eyeballing
    often doesn't.
- A diagonal-print stance is a variant, offered, never imposed.
  - Pattern: a bool parameter `diagonal=False` that applies `stand()`, plus a card
    variant.
  - Give the variant a plain-language `note`: what the tilt buys and costs.
  - Build it speculatively and link it (`?part=x&variant=x_diagonal`) so the user
    judges by looking.
- Past about 20 times the facet width in height, `stand()` needs modelled support
  fins, never slicer supports (their looser grip lets warp tension spring the part
  free mid-print).
  - Neither `supported()` nor the card flag applies to a `stability` finding here;
    catching this combination is on the agent.
  - Recipe: a thin blade at each side, hugging the lean, each on its own 1mm pad,
    joined to the part by single-layer tines about 0.5 x 0.5mm, five or so, biased
    toward the bottom.
  - `fins=False` shows the stability warning without them.

## Load path

If the part is a bracket or mechanical attachment, work out where the weight sits and
what it does at the connection points before drawing anything.

- Shear perpendictular to the attachment face is handled well and rarely needs
  reinforcement.
- Bending moment (a load parallel with the attachment face) is the dominant failure 
  mode. It levers the part off its mount and concentrates stress at an inside corner.
- Lateral load and torsion get a second attachment point, not thicker material. A
  single-mount part carrying an off-center load twists.
- FDM is anisotropic. Layer bonds are the weak direction, so spread load into the body
  with gussets rather than adding section thickness.

Projection-to-height ratio decides the reinforcement:

```
<= 1.5x    chamfers only
1.5 - 2.5x end gussets
> 2.5x     raise the height until it is back under 2.5, then gussets
```

- Doubling the height halves the pull-out force.
- Don't oversize either. A well designed part minimizes the material needed to meet 
  the requirements.

### Reinforcement, in order of preference

1. **Gussets**, triangular webs joining the platform top to the body front. Depth
   about half the projection, height as tall as the body allows while staying low.
   Outer ends only, never mid-surface.
2. **Inside-corner relief**, 3mm, at every load-bearing junction.
3. **Ribs** under a large platform, 2 to 3mm wide, front to back.
4. **Another mount point.** The mounting interface is stronger than the printed part.

- Gussets are truncated quadrilaterals, never sharp triangles. End the outer tip with
  a short vertical face.
- Don't chamfer thin-web edges afterward; fix web shape in the profile, not with a
  dress-up feature.

### Features that flex

Everything above stiffens. A clip or a snap arm works by bending instead, and bending
is the load layer welds carry worst.

- Flex must lie in the layer plane, never across it. A snap arm built standing up
  bends around a layer weld and peels; printed lying down, the same bend stretches
  continuous strands.
- A snap arm is at least 5mm wide, relieved at the root by half its own thickness, and
  tapered toward the tip. The taper spreads strain along the arm instead of parking it
  at the root.
- A clip should deflect during assembly and never while engaged. Give the engaged
  position 0.5mm clearance; plastic under sustained bend creeps.
- A living hinge is a proof of concept, not a durable part. A printed one lasts tens
  of flexes. A hinge that has to live is two parts and a pin or bolt.

## Aesthetics

A part gets looked at every day it's in use. Among shapes that all work, pick
the one worth looking at. A measured fit is never rounded for looks, and structure is
never thinned for elegance, but most dimensions are neither: they're choices.

- Free dimensions get deliberate proportions. Near-equal reads as a mistake: make two
  dimensions equal, or make them clearly different.
- Visual weight follows load: material where the stress is, air where it isn't.
- Symmetry is the default. An asymmetric feature is earned by function, then committed
  to.
- Features align: shared centerlines, shared planes, an even rhythm.
- Rounded features (fillets, `crown()`) are fine where they don't hurt mechanical
  performance.
  - Avoid them on overhanging faces: rounding there reduces bridge effectiveness and
    can create steeper unsupported angles than needed.
  - Otherwise, use a round where it genuinely helps function or looks. Don't add one,
    or a chamfer, with no purpose.
- Minimize the number of distinct chamfer sizes and fillet radii across a part family.
  Fewer distinct sizes reads as one designed system.
- Proportion beyond this is taste. Expose it as a parameter and let the user's eye
  decide in the viewer rather than defending a number in chat.

## Polish pass

The polish pass runs last, after structure is finished.

1. Chamfers are a reasonable default on exposed edges, 1mm, never below 0.8mm. A
   consistent faceted look prints more reliably than a fillet default. Rounded
   treatments are fine where they help function or looks and don't fall in an
   overhanging area (see Aesthetics). `crown()` specifically rounds the top rim of a
   closed perimeter wall, a case direct filleting fails at in OCCT's corner capping.
2. Chamfer where it contributes to function or aesthetics. Don't add a chamfer with no
   purpose.
3. Never touch fit-critical mating geometry: channels, dovetails, sockets, anything
   that has to slide onto something else. Lead-in chamfers can be used with restraint,
   but make sure not to interfere with fit.
4. Avoid chamfering a concave edge if it could cause mechanical interference.
   Otherwise it's an edge like any other. `is_convex` and `concave_edges` are in the
   part-file vocabulary if you need to filter them out; a concave selector otherwise
   reads as an ordinary query and builds without complaint.
5. Select chamfer edges by filtering, never blanket-chamfer.
   - Exclude mating edges, purposeless back/bottom-face edges, and any concave edge
     that would interfere.
   - Filter for what must not be touched, then chamfer the rest greedily. If the batch
     fails, bisect and keep the halves that build, rather than narrowing the set by
     hand.
   - Refuse any batch that leaves a face smaller than the corner triangle three
     chamfers make, about `0.866 * size ** 2`; smaller than that is chamfers
     colliding.
   - Chamfer the original solid with the whole accepted set each time, never the
     result of the last attempt.
6. No text labels on parts. File naming carries catalog identity, and a glyph's
   outline comes from a system font, so identical code builds different geometry on a
   different machine.
7. Consistency, few chamfer sizes and few fillet radii across a family, is itself the
   polish.

Sliver check after every polish pass. Faces under 1mm2 are a bug unless justified. The
one case the doctrine allows outright is the corner triangle where three 1mm chamfers
meet at a convex corner, about 0.87mm2. Anything else is usually chamfers colliding
near a mating mouth. Record the count a part has earned on its card.

## Kernel rules

Specific to OCCT, and measured on real parts rather than reasoned about.

- Two chamfered convex edges need more than `2 * chamfer_size` of face between them.
  Closer, and OCCT raises `BRep_API: command not done` ("Failed creating a chamfer,
  try a smaller length value(s)"). Measured: at a 1mm chamfer, 1.66mm between edges
  fails and 2.16mm builds; at 0.5mm, 1.16mm builds. The threshold tracks the chamfer
  size, so don't just shrink the chamfer to satisfy the kernel's own suggestion; a
  0.4mm chamfer that lands can still print as a defect.
- One chamfered edge alone needs more than `chamfer_size` of face next to it. Easy to
  miss because it looks like plenty of room. Measured on three parts at the same
  threshold: 1.08mm builds and 1.00mm fails at a 1mm chamfer.
- A batch chamfer failure is not one bad edge. Every edge in a failing set chamfers
  fine alone, so testing them one at a time reports nothing wrong. Bisect the set
  pairwise instead.
- A second failure mode, where bisecting doesn't help: an edge ending on a vertex with
  four faces and only three edges between them has no OCCT cap for that corner. It
  fails at every length down to 0.05mm, with nothing about the failure looking like a
  clearance problem. Fix by chamfering in two passes, so the first pass gives those
  faces a real edge to meet along, then reselect from the result.
- Prefer `new_edges(before, combined=after)` over geometric selectors. Each chamfer
  changes topology, so a selector resolved against pristine geometry drifts once an
  earlier chamfer runs.
- A loft through three or more sections wanders unless `ruled=True`. Two sections are
  fine either way. At three, the smooth default fits one spline through all of them,
  and wall thickness between sections drifts from what the numbers say (measured: a
  20mm-to-10mm taper reads 12.5mm at the midpoint where the straight line says 15).
  `ruled=True` puts the wall exactly on the straight line between sections.
- A ruled loft between polygons polishes like a prism; a smooth loft to a curve
  doesn't (its rim refuses a 1mm chamfer and walks under the 0.8mm floor at 0.5). When
  a lofted part will be polished, prefer ruled polygonal sections; a rim that has to
  be round anyway is `crown`'s case.
- Loft doesn't validate its sections. Two sections landing nearly in one plane (a
  `Pos` typo) return a fraction-of-a-mm3 sliver solid instead of raising. Check the
  bounding box or render, not just that it built.
- A subtraction that misses is a legal no-op. Cut a solid that sits entirely outside
  the body, and OCCT returns the untouched body without complaint. Confirm the
  material actually left: volume dropped by roughly what the cutter should have
  taken, or the opening shows in `nurb inspect` / `nurb diff` / a `--section` render.
- A Fusion workaround can be a real constraint wearing a disguise. Restate it as a
  rule rather than assuming it was scaffolding to delete.

## Cards

A part file carries geometry, not rationale. Every part worth keeping has a card next
to it, same basename. Read the card before editing the part, and update it when done.

Four sections:

- `## What it is`
- `## Design notes`, why the key dimensions are what they are
- `## Don't`, **required**, what was tried and rejected. Without it an agent
  re-adds the feature that was retired on purpose.
- `## Changelog`, dated

Plus two machine-facing pieces:

- The **AUTO block**, regenerated by `nurb card`. Never hand-edit it.
- The **accepted baselines**, a TOML fence carrying what the part has already
  justified: sliver count, real minimum wall, printer settings. Put the number next
  to the sentence that earns it.

```toml
[part]
min_wall = 1.0
forward = [-1, 0, 0]
supports = true

[accepted]
sliver = 6
```

- Machine facts (bed size) stay out of the card: they live in `printer.toml` at the
  project root, or `~/.config/nurb/config.toml` for a workshop-wide default.
- `supports` needs its own sentence saying which feature forced it and what ruled out
  a corbel or tilt. If you can name the feature, prefer `supported()` in the part file
  over the card flag. `supports` is refused in `printer.toml` and the global config;
  it's a judgment about one part, and machine-wide it would excuse every cantilever in
  every project.

### Variants

A catalog entry that's the same function at different numbers is a variant, not a new
file. It shares the fence and is walked by `build`, `check`, `card` and `export` like
the part's own defaults, with its own STL, baselines and AUTO-block line.

```toml
[variants.shelf_gridfinity_3x2]
note = "The same shelf sized for the wide bin: three columns instead of two."

[variants.shelf_gridfinity_3x2.params]
grid_x = 3
bracket_count = 6

[variants.shelf_gridfinity_3x2.accepted]
sliver = 26
```

- The test is whether it's the same geometry. A wider cradle on the same part is a
  variant; a different mechanism is a new part, however similar it looks.
- A variant inherits the part's settings first, then applies its own. Check
  `supports` specifically: a part declared on supports hands the flag to every
  variant, including a diagonal one whose whole point is not needing them. Turn it
  off explicitly with `supports = false` under `[variants.<name>.part]`.
- `note` is one sentence in the user's words, saying why the variant exists, not what
  parameter changed.

## Measurements

The bottleneck on a one-off is not geometry, it's dimensions. A wrong number produces
a perfect model of the wrong object, and nothing downstream catches it.

- Ask for a measurement. Never improvise one. A guessed clearance that happens to
  build is worse than a failure, because it prints.
- Record it in `measurements.toml` at the project root, with how it was obtained, and
  read it with `measured()`.

```toml
[shelf_depth]
value = 340
unit = "mm"
how = "tape measure, freezer middle shelf, 2026-07-20"
```

```python
from nurb import measured

depth = measured("shelf_depth")
```

- An unknown name raises, naming what's on file. That failure is the point: it's the
  moment to ask, not to pick something plausible.
- A published number (a VESA mount, a gridfinity bin, a camera thread) is a
  measurement, not a guess. Look it up and record it with `how` naming the source. Two
  limits: the user's actual object outranks the spec when they disagree, since clones
  drift, and a number inferred from a product photo or listing copy was never
  published, so it's a guess and gets marked like one.
- A photo is a shape, never a dimension. It can identify a standard; pixels carry no
  millimetres.
- A phone scan is reference geometry, not metrology. `nurb scan` reads a mesh in mm
  and states the units it used. Mark every scan-derived fit `provisional` until a
  coupon proves it.
- A fit coupon turns a loose measurement into a tight one: print the mating surface
  alone, minutes of filament, and correct the parameters against the real object
  before the full part prints. A coupon that fits removes the provisional flag.
- A downloaded model (an STL, OBJ or GLB from a listing) is a measurement, not a
  starting point. A mesh is triangles, so no dimension in it is an editable
  parameter; measure it and rebuild the part properly. Never mark a download
  `provisional` or ask for a fit coupon over it: unlike a scan, it's exact to the
  micron.
- `import_stl` returns a real solid only from a closed, low-poly mesh with flat
  faces, like a plate, a bracket, or a machined blank someone exported. Prefer
  rebuilding whenever the user might want to change a dimension, which is nearly
  always.
- STEP is the exception worth asking for. Take it over STL when a listing offers
  one: it imports as real B-rep with its curves intact, and chamfers like anything
  modelled.
- When there's nobody to ask, write the guess down and mark it `provisional = true`
  with an honest `how` ("eyeballed against a broom"). `nurb check` lists every
  provisional value until somebody picks up a caliper.
- A measured value pays for itself across a family: Notch measured one bracket pitch
  and amortized it over sixteen parts.

## Assemblies

Every rule above judges one solid being manufactured. An assembly judges solids being
used together: a door on its mount, a lid over the machine it covers. Two parts can
each build clean, check clean, and export clean, then jam mid-swing, because collision
between correct parts exists only in the physical world.

- An assembly is a function in `parts/` whose keyword defaults are its parameters,
  same as a part, but it returns placed solids. `use(name)` builds a sibling part
  where it was modelled; `hinge(solid, axis, through, at)` declares and poses a
  revolute joint; `obstacle(solid, name)` adds what the parts mount into.
- The declared range is a claim, and `nurb check` audits it by sweeping each hinge
  through it against everything else in the scene, reporting the jam angle and the
  contact point. Declare what the design needs, never what happens to sweep clean.
- Nothing full-width may cross the pivot line on the moving part. Use narrow tabs
  instead if the mount has to reach the pin.
- Model obstacles as boxes and prisms with honest volume, never thin hand-drawn
  profiles. A near-degenerate profile can produce a large phantom collision (measured
  once as a 152,000mm3 phantom at a pose that was actually clear).
- Tangent is not clearance. Two faces meeting at zero volume pass a collision check,
  but that's already a bind in plastic. Carry the fits table's numbers (0.3mm minimum
  for a moving pair, 0.5mm for never-binds) into the declared range.
- A stop the sweep finds can be an intentional detent, a feature with a card entry,
  not a finding to engineer away.
- Never trust a swing worked out by hand. A hand-modelled convexity check can be
  quietly wrong in a way a kernel boolean can't; the sweep is the authority.
- Sweep cost scales with pose count. Set `step` to match what the design needs; a
  full 360-degree sweep at a fine step is expensive and often unnecessary for a gross
  clearance check.
- One hinge sweeps at a time; the others hold their pose.
- Printability rules stay off assemblies entirely: each part already answered them
  alone, and overhang measured on an assembled scene reports confident nonsense.

## Verification

"It built" is not verification. `nurb verify` runs the machine-checkable part of this
list: one solid per configuration, every count flexed upward, the rules clean, and the
card agreeing with the geometry. `--report` writes the verdict into
`build/renders/<part>.verify.md` with the renders that back it. Items 2 and 6 need a
human.

Before presenting a part:

1. Flex the driving parameters both up and down, for example 4 to 6 to 2 to 4. Growth
   catches a frozen selector; shrinking alone passes a broken part.
2. Check fit-critical faces by coordinate after any polish or resize. `nurb inspect`
   lists them, each finding resolved to the face it fired on. Knowing which faces are
   fit-critical is still on you.
3. Confirm the solid count, almost always one.
4. Run `nurb check`. Zero findings is the bar. A finding on a part that prints fine is
   a bug in the rule, not something to accept quietly.
5. Predict a baseline before you look at it. Work out the sliver count from the
   polish exclusions, which turns the number into a test of the rule.
6. Render it and actually look. `nurb render <part>` writes a PNG, `--section z:4mm`
   cuts it open, and `nurb inspect --render` stands a camera at every finding. A part
   can pass every numeric check and still be visibly wrong.
