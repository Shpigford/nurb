# nurb design doctrine

Printed via `nurb rules`. This file is the single source; harness files point at it
rather than repeating it.

These are standing rules for FDM-printed parts, and several are vetoes rather than
preferences. Most of them are physics, so they outlive any particular CAD kernel. The
ones that are specific to OCCT are marked as such and were measured, not reasoned.

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

Keyword defaults are the parameters. That one declaration feeds the agent, the CLI, the
viewer, the tests, and any future configurator. Never add a parallel `PARAMS` dict; the
two would drift.

**Write a continuous dimension as a float.** The type of a default is the only thing
that says whether a value is a count or a measurement, and the viewer reads it: an `int`
default gets a slider that steps by one, a `float` default one that moves continuously.
`bracket_count=4` is a count and `chamfer_size=1.0` is a millimetre, so the trailing
`.0` is doing work. Nothing else has to be declared, and there is no annotation to keep
in sync, because the type is already there in the signature.

`draft` is optional and injected by the runtime, never passed by a caller. When it is
true, skip the polish pass. It is worth about 20% on a real part, not the 18x a cube
suggests.

Return one solid. A function that returns two loose bodies still reports a plausible
bounding box and still exports, so nothing downstream catches it.

## Printability

- **Minimum wall 2 to 3mm**, except where fit geometry says otherwise. Fit-critical
  dimensions are already tuned; do not round them for tidiness.
- **Print support-free. No floating features.** Parts print bottom down, building up in
  +z, so every functional feature is grounded. A vertical extrusion or a vertical
  through hole is self-supporting. A shelf, loop, or band floated partway up with a gap
  underneath is not.
- **Corbel rule.** Grounded does not mean a column to the bed. Support-free means no
  layer overhanging past 45 degrees. Where material would run to the plate only to
  satisfy printing, carry the feature on a 45 degree underside instead: a short vertical
  tip of 4 to 6mm below the floor at the front face, then a 45 degree plane falling back
  into the body. Every layer then overhangs by at most half a bead and bonds to the wall
  behind it.
- **Corbels are always exactly 45 degrees**, the same as every other facet. Never
  steepen one or match it to a ratio. Let the landing point fall where 45 degrees puts
  it. Mismatched facet angles are a veto: every facet on the part, cosmetic or
  structural or corbel, has to read as one system.
- **Elephant's foot is a slicer setting**, not a CAD problem. Do not model around it.

## Load path

Work out where the weight sits and what it does at the mount before drawing anything.

- **Shear**, a straight down load close to the wall, is handled well and rarely needs
  reinforcement.
- **Bending moment**, a load projecting forward, is the dominant failure mode. Load
  times distance levers the top of the part off its mount and concentrates stress at
  the inside corner where the platform meets the body.
- **Lateral load and torsion** are answered by a second mount point, not by thickening.
  A single-mount part carrying an off-center load twists.
- **FDM is anisotropic.** Layer bonds are the weak direction and a cantilever moment
  peels them apart. Spread load into the body with gussets rather than adding section
  thickness.

**Projection-to-height ratio** decides the reinforcement. A loaded shelf pries at the
wall as a force couple, and those forces scale with projection divided by the height of
the supporting back. Doubling the height halves the pull-out force, and height in the
wall plane is nearly free: no forward mass, almost no material.

```
<= 1.5x    chamfers only
1.5 - 2.5x end gussets
> 2.5x     raise the height until it is back under 2.5, then gussets
```

Do not oversize either. A light part sits near the mounting system's minimum height. An
oversized back on a small hook is wasted material and looks wrong. `nurb check` reports
this ratio for any part whose card names which way it reaches.

### Reinforcement, in order of preference

1. **Gussets**, triangular webs joining the platform top to the body front. The most
   effective cantilever fix, because they turn bending into compression along the
   diagonal. Depth about half the projection, height as tall as the body allows while
   staying low. **Outer ends only, never mid-surface**: a mid-surface gusset obstructs
   the usable area.
2. **Inside-corner relief**, 3mm, at every load-bearing junction. Cheap, always worth it.
3. **Ribs** under a large platform to stop plate flex, 2 to 3mm wide, front to back.
4. **Another mount point.** When in doubt, add one. The wall interface is stronger than
   the printed part.

**Gussets are truncated quadrilaterals, never sharp triangles.** End the outer tip with
a short vertical face of about 6mm, drawn in the profile. Do not chamfer thin-web edges
afterwards: slope chamfers leave runout slivers and tip chamfers make compound-angle
artifacts where they meet the platform. **Shape problems on a thin web get fixed in the
profile, not with a dress-up feature.**

## Polish pass

The polish pass runs last, after structure is finished.

1. **Chamfers are the default on exposed edges**, 1mm, never below 0.8mm. A consistent
   faceted look that prints reliably beats a fillet default.
2. **No chamfers lying in the back face or the bottom face.** The back sits against the
   wall and the bottom is the bed-contact face. Chamfering an edge that lies in either
   buys nothing, and where a bottom chamfer meets another one it makes sliver facets and
   notch points that are very hard to print.
   **An edge that merely ends there is fine**, and this is the distinction to get right,
   because reading the rule as "nothing touching the bed" throws away the vertical corner
   chamfers, which are the most-handled edges on the part. A vertical corner's chamfer
   stands square to the plate and the first layer keeps its full width. A *sloped* edge
   arriving at the plate is the case that is not fine: its chamfer lands tilted and lays
   a knife edge into the first layer. That is exactly what `bed_bevel` measures, and it
   tells a corbel from a chamfer by reach, since a chamfer's reach is its size.
3. **Never touch fit-critical mating geometry**: channels, dovetails, sockets, anything
   that has to slide onto something else. Lead-in chamfers at a mating mouth sound
   helpful and are not. They make tiny compound facets that print badly on someone
   else's machine.
4. **Never polish a concave edge.** A cosmetic chamfer on an inside corner adds a thin
   wedge instead of taking a corner off: it prints as a feather edge and collects stress
   where the part is already weakest. A concave junction that needs relieving gets a
   deliberate 3mm structural chamfer, sized for the load, before the polish pass runs.
   `is_convex` and `concave_edges` are in the vocabulary a part file gets, because this
   is the one polish mistake that is invisible in code: the selector reads as an
   ordinary exposed-edge query and the part builds, exports and prints without
   complaint. It shipped in this library once.
5. **Select chamfer edges by filtering, never blanket-chamfer.** Mating edges, back-face
   edges, bottom-face edges and concave edges all have to be excluded.
   **Filter for what must not be touched, then let the kernel refuse the rest.** A
   chamfer call is all or nothing, so one edge that cannot land takes the whole pass
   down, and the tempting response is to keep narrowing the set by hand until it builds.
   That is how a part ends up with three chamfered edges out of ninety. Narrow the set
   for reasons you can name, then chamfer greedily: try the set, and where it fails,
   bisect and keep the halves that build. Refuse any batch that makes a face smaller
   than the corner triangle three chamfers leave, about `0.866 * size ** 2`, since
   anything smaller is chamfers colliding. Chamfer the original solid with the whole
   accepted set each time, never the result of the last attempt: an edge belongs to the
   shape it was selected from, and applying batches in sequence quietly re-chamfers the
   first body and returns it.
6. **No text labels on parts.** File naming carries catalog identity. There is a second
   reason beyond taste: a glyph's outline comes from a system font, so a part with text
   on it builds to different geometry on a different machine. The calibration coupon,
   which needs a label because four of them come off one plate looking identical, comes
   out at 2600.6mm3 with 88 faces on one machine and 2601.0 with 83 on another. Nothing
   about its fit moves, but its card cannot be asserted anywhere but where it was
   written.
7. **Consistency is the polish.** One chamfer size across a family is what makes it read
   as a designed system rather than a pile of prints.

**Sliver check after every polish pass.** Faces under 1mm² are a polish bug unless
justified. The only ones the doctrine allows outright are the corner triangles where
three 1mm chamfers meet at a convex corner, about 0.87mm². Anything else is usually
chamfers colliding near a mating mouth, or a chamfered concave edge. A part declares the
count it has earned on its card, so a new one is a regression and a known one is silent.

## Kernel rules

Specific to OCCT, and measured on real parts rather than reasoned about.

- **Two chamfered convex edges need more than `2 * chamfer_size` of face between them.**
  Closer and OCCT raises `BRep_API: command not done`, which build123d surfaces as
  "Failed creating a chamfer, try a smaller length value(s)". At 1mm the shelf fails
  with 1.66mm between the edges and builds with 2.16mm; at 0.5mm it builds with 1.16mm.
  The threshold tracks the chamfer exactly. This is the single most common way a part
  stops building.
- **One chamfered edge needs more than `chamfer_size` of face**, which is the same rule
  with one chamfer instead of two and is easy to miss because it looks like plenty of
  room. It bites wherever a polished edge sits beside something that is never polished:
  a concave junction, a structural chamfer's toe, a pocket wall. Measured on three
  different parts, all at the same threshold: 1.08mm builds and 1.00mm fails at a 1mm
  chamfer.
- **A batch chamfer failure is not a bad edge.** Every edge in a failing set chamfers
  fine on its own, so testing them one at a time reports that nothing is wrong. Bisect
  the set pairwise instead. "Try a smaller length" would never have found the rule above.
- **The second way a chamfer dies, where bisecting does not help**, is an edge whose end
  lands on a vertex with four faces around it and only three edges between them. Two of
  those faces touch at a point without sharing an edge, and OCCT has no cap for that
  corner. The edge fails on its own, on a clean body, at every length down to 0.05mm, so
  nothing about the failure looks like a clearance problem. The fix is to chamfer in two
  passes so that the first one gives those two faces a real edge to meet along, then
  reselect from the result. Found on the parts bin, where the front drop and the side
  taper land at the same height by design.
- **Prefer `new_edges` over geometric selectors.** Each chamfer changes topology, so a
  selector resolved against pristine geometry drifts once an earlier chamfer runs.
  `new_edges(before, combined=after)` returns exactly the edges an operation created. It
  is the algebra-mode equivalent of a builder's `Select.LAST`, and algebra mode is what a
  part file uses, so `part.edges() - last` is not available. It is what makes a part
  survive flexing its counts.
- **A Fusion workaround is sometimes a real constraint wearing a disguise.** The gusset
  drop that existed only to escape `ASM_BL_NO_MATE` turned out to be the same "a chamfer
  needs room to land" constraint at a different number. Deleting it would have been
  wrong; restating it as a rule was right.

## Cards

A part file carries geometry, not rationale. Every part worth keeping has a card next to
it, same basename. **Read the card before editing the part, and update it when done.**

Four sections, and one of them does work nothing else does:

- `## What it is`
- `## Design notes`, why the key dimensions are what they are
- `## Don't`, **required**, what was tried and rejected. Geometry records what is; only
  this records what is deliberately absent. Without it an agent helpfully re-adds the
  lead-in chamfer that was retired on purpose.
- `## Changelog`, dated

Plus two machine-facing pieces:

- The **AUTO block**, regenerated by `nurb card`. Never hand-edit it. It is a cache, not
  a source of truth, and it holds no timestamp so regenerating it on unchanged geometry
  produces no diff.
- The **accepted baselines**, a TOML fence carrying what this part has already justified:
  its sliver count, its real minimum wall, its printer settings. The number goes next to
  the sentence that earns it, because a count on its own is a magic number. Machine facts
  stay out of it: a bed size belongs to the machine, so it lives in `printer.toml` at the
  project root, which names a shipped profile (`profile = "bambu_a1_mini"`) and can
  override any check setting machine-wide.

```toml
[part]
min_wall = 1.0
forward = [-1, 0, 0]

[accepted]
sliver = 6
```

### Variants

A catalog entry that is the same function at different numbers is a variant, not a new
file. It goes in the same fence, and `build`, `check`, `card` and `export` all walk it
exactly as they walk the part's own defaults, so it gets its own STL, its own baselines
and its own line in the AUTO block.

```toml
[variants.shelf_gridfinity_3x2.params]
grid_x = 3
bracket_count = 6

[variants.shelf_gridfinity_3x2.accepted]
sliver = 26
```

The test is whether it is the same geometry. A wider cradle on the same J is a variant.
A different mechanism is a part, however similar the slab looks.

## Measurements

The bottleneck on a one-off is not geometry, it is dimensions. A wrong number produces a
perfect model of the wrong object, and nothing downstream can catch it.

**Ask for a measurement. Never improvise one.** A guessed clearance that happens to
build is worse than a failure, because it prints. Record what you are told in
`measurements.toml` at the project root, with how it was obtained, and read it with
`measured()`:

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

An unknown name raises, naming what is on file. That failure is the point: it is the
moment to ask rather than to pick something plausible.

**When there is nobody to ask**, write the guess down and mark it `provisional = true`.
The danger was never the guess, it is that a guess and a measurement look identical six
months later. `how` is still required, because "eyeballed against a broom" tells the
next person how far to trust it, and `nurb check` lists every provisional value until
somebody picks up a caliper.

A measured value pays for itself across a family. Notch measured one bracket pitch and
amortized it over sixteen parts.

## Verification

"It built" is not verification. `nurb verify` runs the machine-checkable part of
this list: one solid per configuration, every count flexed upward, the rules clean,
and the card agreeing with the geometry. The two it cannot do are the two that need
you, and they are items 2 and 6.

Before presenting a part:

1. **Flex the driving parameters up as well as down**, for example 4 to 6 to 2 to 4.
   Growth is what catches a frozen selector; shrinking alone passes a broken part.
2. **Check fit-critical faces by coordinate** after any polish or resize.
3. **Confirm the solid count**, which is almost always one.
4. **Run `nurb check`.** Zero findings is the bar, and a finding fired at a part that
   prints fine is a bug in the rule, not something to accept quietly.
5. **Predict a baseline before you look at it.** Working out what the sliver count
   should be from the polish exclusions turns the number into a test of the rule instead
   of something to write down.
6. **Render it and actually look.** `nurb render <part>` writes a PNG. A part can pass
   every numeric check and still be visibly wrong.
