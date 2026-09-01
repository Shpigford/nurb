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

**When a configuration cannot work, refuse it with `reject`, never a bare raise.** A holder whose hole is narrower than the tool it holds should not build, and `reject("drill_hole_width 14 is under the 14.27mm pin vise plus print shrink: raise it above 14.77", param="drill_hole_width")` is how a part says so. The message states what is wrong and what value fixes it; `param` names the offending parameter so the viewer marks its slider. The viewer presents a refusal as a limit of the design, in amber with the last good geometry still on screen, where a bare `ValueError` arrives as a red traceback that reads as the part being broken. Guard only what would print wrong or not work at all; taste stays a slider.

## Printability

- **Minimum wall 2 to 3mm**, except where fit geometry says otherwise. Fit-critical
  dimensions are already tuned; do not round them for tidiness.
- **Print support-free. No floating features.** Parts print bottom down, building up in
  +z, so every functional feature is grounded. A vertical extrusion or a vertical
  through hole is self-supporting. A shelf, loop, or band floated partway up with a gap
  underneath is not.
- **Support material is a declaration, never a default, and never yours to make.** A part that genuinely cannot be corbelled or tilted says so and prints with supports: `supported(shape, why)` around the feature in the part file, or `supports = true` under `[part]` in the card when the whole body is that case. Reach for the marker first; the card flag excuses every cantilever in the part, including the one added next month by mistake. Either way the overhang finding becomes a note rather than disappearing, because support material is a cost paid on every print and a scar to clean off every copy, not a fault that got fixed. It is the user's call and not the agent's: it is their printer, their cleanup, and their tolerance for the mark it leaves. Offer it, say what it buys, and wait to be told.
- **A counterbore prints mouth toward the bed, and that floats its ceiling.** The shelf the screw head bears on is laid flat over the open pocket, and the smaller hole's first rim is a circle drawn on air; the `hole_ceiling` finding is this exact case, and it appears on any hole rising out of a bridged roof, not just screw pockets. Never answer it with supports inside a pocket nobody can clean, which is why neither `supported()` nor the card flag touches a `hole_ceiling` finding: cut the hole with `counterbore(hole_dia, head_dia, head_depth, depth)`, which steps the transition through two sacrificial bridge layers, a slot bridged chord-to-chord across the pocket and the same slot turned ninety degrees across the first, so each layer spans only what the one before it laid and the whole stack prints support-free. Reach for it whenever a design wants a screw head, a nut, or any wider recess on the bed side of a hole.
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
- **A large first layer peels its corners as it cools.** Every layer shrinks as it cools and pulls toward the middle of the part, and the pull lands hardest on a sharp plan corner, farthest from the middle and holding on at a point. Past about 20,000mm2 of first layer the accumulated pull beats corner adhesion, and `warp_risk` names the corners that will lift. The fixes are in the outline, which is what makes this a CAD problem where elephant's foot is not: round the vertical corners at 8mm or more, so the peel front is a curve instead of a point, and give a big plate a ribbed floor rather than a solid slab, which is stiffer per gram and halves what contracts. A 1mm polish chamfer is not relief here; it moves the point half a millimetre. The brim and the clean bed are the slicer's share, and they treat the symptom the outline caused. Material multiplies the pull: the threshold is calibrated on PLA, and naming what the machine prints in `printer.toml`, `material = "abs"` next to the profile line, tightens it fivefold, because ABS contracts 1 to 2% as it cools where PLA holds under half a percent. PETG judges as PLA, ASA as ABS, and PC and PP tighter still. At the far end the rule stops being about corners: a bed-covering part in ABS, ASA or PC is the wrong material, and the fix is PETG or PLA, not a wider brim.
- **Elephant's foot is a slicer setting**, not a CAD problem. Do not model around it.
- **A pin under 5mm across is perimeters with nothing inside.** There is no room between the walls for infill, so a thin printed pin is a tube, loaded in bending at the weakest weld it has, its base. Under 3mm the nozzle is re-melting each ring as it lays the next, and the pin may not survive its own printing. `pin` fires on a free-standing vertical cylinder taller than twice its diameter; a stub or a locating nub has nothing to lever with and stays silent. The fixes, in order: thicken it past 5mm, give its base a structural chamfer sized like any other loaded junction, or model the hole instead and press in a metal pin, the same trade the fastener rules already make, because off-the-shelf steel beats printed plastic everywhere they compete.

### Holes

- **No hole under 2mm across.** Below that the perimeters converge and the bore prints as a smear or closes outright. A locating hole that small is a drill's job: model a 1mm dimple to centre the bit and let steel cut the diameter.
- **Every vertical bore prints small**, by the same few tenths the fastener table's medium column already absorbs for screws, and the physics does not care that a dowel or a shaft is not a screw. Any bore gets the medium column's slack against its rod's true diameter, and when the diameter genuinely matters, printing is the wrong finisher: model half a millimetre under and drill to size, because a drill holds a tolerance no printer does.
- **A horizontal hole's crown is a bridge.** Under the printer's span limit no rule minds it, but the crown sags into the bore and prints out of round exactly where a fit would bear. Prefer standing the hole vertical; the orientation rules usually allow it. When the axis cannot move and roundness matters, roof the bore with two 45 degree chords meeting in a point above the crown, a teardrop, which is the counterbore's idea turned sideways: every layer leans on the one before instead of spanning air.

### Fasteners

**A published standard is not a guess.** Measurements says never improvise a dimension, and a screw is the one place that rule gets misread: nobody has to measure an M3 cap screw, because ISO fixed its head at 5.5mm across in every box you will ever open. Take these from the table and spend the question you saved on something the table cannot answer.

| Thread | Clearance hole, close | medium | Cap head dia | Cap head height | Nut across flats | across corners | Nut thickness |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M2 | 2.2 | 2.4 | 3.8 | 2.0 | 4.0 | 4.4 | 1.6 |
| M2.5 | 2.7 | 2.9 | 4.5 | 2.5 | 5.0 | 5.5 | 2.0 |
| M3 | 3.2 | 3.4 | 5.5 | 3.0 | 5.5 | 6.1 | 2.4 |
| M4 | 4.3 | 4.5 | 7.0 | 4.0 | 7.0 | 7.7 | 3.2 |
| M5 | 5.3 | 5.5 | 8.5 | 5.0 | 8.0 | 8.8 | 4.7 |
| M6 | 6.4 | 6.6 | 10.0 | 6.0 | 10.0 | 11.1 | 5.2 |
| M8 | 8.4 | 9.0 | 13.0 | 8.0 | 13.0 | 14.4 | 6.8 |

Clearance is ISO 273, cap head is ISO 4762 socket head, nut is ISO 4032 hex. In mm. Across corners is the one a round pocket has to clear, and it is the number people reach for the wrong column of: an M3 nut is 5.5 across the flats and will not go into a 5.5 hole.

**Reach for the medium column.** A printed hole comes out under its modelled size, by a few tenths that vary with the machine, the material and how fast the perimeter was laid, so the close column is a fit you have to earn with a coupon rather than one you can assume. Medium already carries that much slack, which is why it is the default here and close is the exception a fit coupon has justified.

**Give a screw head its pocket through `counterbore`, never a plain wider hole.** Head diameter plus about 0.4, head height plus a layer, and the pocket faces the bed with the shaft rising out of it: that is the shape the table above is sized for, and it is the shape `counterbore` cuts.

**A nut pocket is a hex prism, and `counterbore` cannot cut one.** It cuts a cylinder, so the pocket is modelled by hand: `extrude(RegularPolygon(across_corners / 2, 6), thickness + 0.2)` sized on the across-corners column, or a round pocket at across-corners plus 0.2 if the nut is free to spin. A hex takes about 0.2 of slack across the flats, and rotating the prism so a flat rather than a point faces up prints a cleaner socket. It floats its own ceiling exactly the way a screw head does and earns the same `hole_ceiling` finding, so the two sacrificial bridge layers still apply; that trick is the part of `counterbore` worth copying, and the cylinder is not.

**Heat-set inserts are the exception that proves the rule.** Their boss diameter is set by the insert a particular vendor ships and not by any standard, the same nominal thread differs by half a millimetre between brands, and the number that matters is the one on the bag in the user's drawer. Ask, or measure one, and record it with `measured()`.

**Never model a thread under M5.** A printed thread below that is slivers arranged in a helix: the crests print as smears, and what does print strips the first time it is torqued. The hardware above is the answer, a nut in its pocket or a heat-set insert, and even past M5 a modelled thread is a choice the card justifies, never a default.

**A loaded hole earns a fastener diameter of wall.** An M5 screw wants 5mm of material around its bore. Thinner, and the boss bulges as the screw seats, then splits along a layer weld, which is the one direction a boss cannot spare. The clearance columns say where the hole is; this says how much part has to be around it.

### Fits between printed parts

The fastener table covers steel meeting plastic. Two printed faces that work together get a designed gap of their own, sized by what the pair does, and stated as the total extra on the opening: a bore over its shaft, a pocket over its tongue, whatever dimension the pair shares.

| Fit | Extra on the opening | What it feels like |
| --- | --- | --- |
| press | 0.1 | driven together once, holds by friction |
| snug | 0.2 | slides on by hand, no rattle |
| moving | 0.3 | swings and slides through its whole travel, the hinge floor |
| free | 0.5 | drops in every time, on any printer, in any material |

In mm. The table is where a fit starts, never what lets it skip the coupon: anything fit-critical is still measured, printed as a coupon, and corrected before the part prints. Two limits: below 0.1 is not a tighter press, it is a bind that varies by machine, and a moving pair never ships at less than 0.3, because the 0.2 that swings freely on the printer that made it seizes on the next one.

## Print orientation

Parts print the way they are modelled, +z up, and for most parts that is the end of it. Orientation becomes a decision in exactly two situations: an overhang a corbel cannot carry without disfiguring the part, and a load that wraps a corner, where no flat orientation keeps every member strong.

- **The remedies for an overhang finding are a corbel, a tilt, and only then supports.** Reach for the corbel first: it is local, it keeps the part on its natural face, and it disappears into the design. Reach for the tilt when the whole part fights the bed. Supports come last and come from the user, because the first two are free once printed and this one is paid for on every copy: ask before proposing it, and when a feature really has no other answer, mark that feature with `supported()` rather than declaring the whole part. An open box printed upright wants support inside; printed flat it has one huge first layer that warps and three finishes that do not match; stood on a corner at 45 degrees, nothing needs support and every face is printed as perimeters, one finish.
- **Layer bonds are about half strength**, measured near 50% of in-plane tensile for PLA and worse for ASA. A part loaded around a corner, which is every bracket and every L, has no flat orientation that keeps both legs loading in-plane: one of them always pulls its layers apart. Stood at 45 degrees neither does, and the load path never lies in a single weld plane. A tilt moves the weak plane rather than deleting it, so it is not automatic: a hook printed at an angle fails at the same load with the break somewhere else. It earns its keep on corners, not on straight pulls.
- **`stand(part, tilt, axis, facet)` is the verb.** It rotates the part about a horizontal axis, seats it, and shaves the down corner flat, because a part standing on an unshaved corner meets the bed along a single extrusion line, and that line peels. The facet is 2mm minimum, measured across the flat. 45 degrees is the usual tilt and is not sacred: a shallow part stands at whatever angle brings everything inside the limit. Run the polish pass before standing, in the functional orientation.
- **Stand a part on the corner that grounds every region, and prefer the lowest stance that does.** For an L that is the outside of its elbow, legs up in a V. The sign of the roll depends on which way the model faces, so check rather than reason: the same L rolled the other way stands on the end of one leg as a chevron, still grounded, still legal, but 60% taller on the same facet, and height on a facet is what spends the adhesion margin. The stance to refuse is the tent, elbow up, one leg's tip hanging in air, and it is easy to miss by eye because nothing about it looks steep: every face of the floating tip can sit at exactly 45 degrees, silent to the overhang rule. The `floating` rule fails any region whose first layer has nothing to sit on and `stability` judges the height, so `nurb check` on the stood variant settles the corner choice. Past grounded, inside the limit, and low, the tilt is taste: what remains is where the facet scar lands, which is the user's call.
- **A diagonal print is a variant, and it is offered, never imposed.** The facet is cut from visible geometry, and whether that corner may go is not a printability question: only the user knows whether it shows. The pattern is a bool parameter, `diagonal=False`, that applies `stand()` when true, and a card variant that sets it, so it builds, checks against its own baselines, exports its own STL and shows in the viewer like any variant. Give the variant a `note` saying what the tilt buys and costs in plain words, "prints tilted on a flattened corner: no supports, and stronger across the corner", never in the doctrine's. That phrase is also the argument for trying a tilt before declaring supports: it deletes the cost rather than accepting it. Build it speculatively and link it, `?part=x&variant=x_diagonal`; the user judges by looking, and two lines delete it if they pass.
- **Past about twenty times the facet width in height, adhesion is holding a lever, and `stand()` grows fins.** A compact part holds its facet by first-layer adhesion; a tall one needs support fins modelled into the part, never slicer supports, whose loose grip lets warp tension spring the part free mid-print. This is the one place declaring supports is the wrong answer even though the part is asking for help, and the rules will not let you: neither `supported()` nor the card flag touches a `stability` finding, and turning slicer supports on around a finned stance is actively worse than either alone, since the slicer fills the tine gaps the fins were shaped to leave. Nothing checks for that combination, so it is on you not to build it. The recipe is print-farm practice with fixed numbers, so it is generated rather than judged: a thin blade at each side of the part hugging the lean across a small gap, each on a 1mm pad for its own adhesion, joined to the part only by horizontal tines a single layer tall and a bead wide, about 0.5 x 0.5mm, five or so, biased toward the bottom where the young print is least stable. After printing the fins lift off whole and the tine stubs rub off with a fingernail. The tines cost a handful of sub-millimetre faces, declared on the card like any other earned sliver. The stability warning remains the referee for what `stand()` did not build: pass `fins=False` to see it, and a part tilted by hand still gets it.

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

### Features that flex

Everything above stiffens. A clip or a snap arm works by bending instead, and bending is the load layer welds carry worst, so flexure gets one veto and a few numbers.

- **Flex lies in the layer plane, never across it.** A snap arm built standing up bends around a layer weld and peels on the first deflection, or the fiftieth, and both are failures. Printed lying down, the same bend stretches continuous strands and the arm is as good as the plastic. This is the anisotropy rule with the load reversed: a static part carries load across welds badly, a flexing one not at all, so orientation is decided by the flexing feature before anything else gets a vote.
- **A snap arm is at least 5mm wide, relieved at the root by half its own thickness, and tapered toward the tip.** The root relief is structural, sized with the load and cut before polish like the 3mm inside-corner rule it echoes, because the root is where every snap arm breaks. The taper spreads strain along the arm instead of parking it all at the root.
- **A clip deflects during assembly and never while engaged.** Plastic creeps: an arm parked under bend is an arm slowly letting go. Give the engaged position 0.5mm of clearance so holding on costs the arm nothing.
- **A living hinge is a proof of concept, not a part.** A printed one lasts tens of flexes, not thousands: the web is one or two beads thick, and every flex works the weld between them. A hinge that has to live is two parts and a pin, which the assemblies rules already know how to swing.

## Aesthetics

Function is not the whole job. A part gets looked at every day it hangs on the wall, and among the shapes that all work, pick the one worth looking at. The priority is fixed: a measured fit is never rounded for looks and structure is never thinned for elegance. But most dimensions on a part are neither fit nor structure, they are choices, and a choice made with intent is what separates a designed object from an extruded one.

- **Free dimensions get deliberate proportions.** When nothing constrains a ratio, pick one and mean it, rather than letting a dimension land wherever the arithmetic left it. Near-equal reads as a mistake: make two dimensions equal or make them clearly different.
- **Visual weight follows load.** Material where the stress is and air where it is not makes a part look strong in the same places it is strong. A uniform slab reads as unconsidered; a gusseted, relieved shape explains itself.
- **Symmetry is the default.** An asymmetric feature is earned by function, a cable exit, a handed mount, and once earned it is committed to rather than half-hidden.
- **Features align.** Holes share a centerline, faces land on shared planes, repeated features sit on an even rhythm. An edge that almost lines up with another is worse than either placement.
- **Restraint is the ornament.** The faceted language, one chamfer size, every facet at 45 degrees, is already the decoration. Nothing decorative gets added that printability has to pay for, and nothing arbitrary breaks the system.

Beyond these, proportion is taste, and taste is a slider: expose the parameter and let the user's eye decide in the viewer rather than defending a number in chat.

## Polish pass

The polish pass runs last, after structure is finished.

1. **Chamfers are the default on exposed edges**, 1mm, never below 0.8mm. A consistent faceted look that prints reliably beats a fillet default. The one sanctioned round-edge treatment is `crown`, for the top rim of a closed perimeter wall, and it is **asked for, never assumed**: reach for it when the user wants a rounded rim, or when a mating part genuinely requires one, and chamfer the rim like any other edge otherwise. It exists because filleting a variable-height roofline directly dies in OCCT's corner capping, not because rims want beads.
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
  stops building, so `chamfer` says this much at the point of failure rather than
  leaving the kernel's advice to stand: taking "try a smaller length" at its word is how
  a part ends up with a 0.4mm chamfer that lands and then prints as a defect.
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
- **A loft through three or more sections wanders unless `ruled=True`.** With two sections the flag changes nothing, measured to the same volume, so a plain taper is fine either way. At three, the smooth default fits one spline through all of them and the wall between sections is nowhere the numbers say: lofting a 20mm square through a 10mm waist, the wall halfway there reads 12.5mm across where the straight line says 15. Every wall thickness and overhang worked out from the section dimensions drifts by that much, silently, between the stations. `ruled=True` puts the wall exactly on the straight line between sections, which is why the gridfinity shelf builds as one five-section ruled loft. Mismatched sections are not the hazard they look like: a square lofts to a hexagon or to its own 45 degree twin without complaint, so there is no vertex-matching rule, only the spline one.
- **A ruled loft between polygons polishes like a prism; a smooth loft to a curve does not.** The rim where a square meets a circle refuses a 1mm chamfer and accepts 0.5, and taking the kernel's "smaller length" advice there walks straight under the 0.8mm floor. When a lofted part is going to be polished, prefer ruled polygonal sections; a rim that has to be round anyway is `crown`'s case, not a shrinking chamfer's.
- **Loft does not police its sections.** Two sections landing nearly in one plane, the shape a `Pos` typo makes, return a fraction-of-a-mm3 sliver solid instead of raising. It builds, exports and passes the one-solid check, so the bounding box and the render are what catch it. A loft whose result looks wrong by eye is wrong at a section, not at the surface.
- **A subtraction that misses is a legal no-op.** Cut a solid that sits entirely outside the body, the way a honeycomb pattern does once its spacing walks it off the face, and OCCT returns the untouched body without complaint. The build is green, the code ran, and nothing was removed, so a cut is never confirmed by the fact that it built. Confirm the material left: the volume dropped by roughly what the cutter should have taken, the openings show in `nurb inspect` or `nurb diff`, or a `--section` render shows them. A pattern of cuts also fails partly, some landing and some missing, which averages into a volume that looks plausible, so count the openings rather than trusting the total.
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
  override any check setting machine-wide. A printer is really a fact about the workshop,
  not the project, so `~/.config/nurb/config.toml` takes the same schema and covers every
  project on the machine; `printer.toml` overrides it where they disagree.

```toml
[part]
min_wall = 1.0
forward = [-1, 0, 0]
supports = true

[accepted]
sliver = 6
```

`supports` needs its sentence more than any of the others do, because it is the only one that is not a number: a count can at least be checked against the geometry, while a bare `true` records that somebody decided something and nothing about what. Say which feature forced it and what stopped a corbel and a tilt from carrying it. If you can name the feature, `supported()` in the part file is the better home for both the decision and the sentence, and it keeps the rest of the part honest. `supports` is refused in `printer.toml` and in the global config: it is a judgement about one part, and machine-wide it would quietly excuse every cantilever in every project.

### Variants

A catalog entry that is the same function at different numbers is a variant, not a new
file. It goes in the same fence, and `build`, `check`, `card` and `export` all walk it
exactly as they walk the part's own defaults, so it gets its own STL, its own baselines
and its own line in the AUTO block.

```toml
[variants.shelf_gridfinity_3x2]
note = "The same shelf sized for the wide bin: three columns instead of two."

[variants.shelf_gridfinity_3x2.params]
grid_x = 3
bracket_count = 6

[variants.shelf_gridfinity_3x2.accepted]
sliver = 26
```

The test is whether it is the same geometry. A wider cradle on the same J is a variant.
A different mechanism is a part, however similar the slab looks.

A variant inherits the part's own settings before its own are applied, and that runs the wrong way for `supports`: a part declared on supports hands the flag to every variant, including the diagonal one whose whole point is not needing them. Turning it off is explicit, `supports = false` under `[variants.<name>.part]`, and it is worth checking for on any part that has both.

`note` is one sentence saying why the variant exists, written in the user's words rather than the doctrine's, because the viewer shows it next to the variant and its reader is whoever is about to print the thing. The params are the how and never the why: `diagonal = true` explains nothing to someone who has not read the doctrine, and "prints tilted so it needs no supports" does.

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

**A published number is a measurement, not a guess.** When the part mates with a manufactured product or a published standard, a VESA mount, a gridfinity bin, a camera thread, the number already exists in a datasheet, and making somebody caliper a hole pattern a standards body fixed is friction wearing rigor's clothes. Research it, record it like any other measurement with `how` naming the source ("VESA MIS-D 100, manufacturer product page"), and ask only for what nobody published, like the opening the finished thing has to fit. Two limits keep this honest: the user's actual object outranks the spec when the two disagree, because clones drift, and a number inferred from a product photo or a listing's marketing copy was never published at all, so it is a guess and gets marked like one.

**A photo is a shape, never a dimension.** It can identify the standard, that the siding is dutch lap, that the rail is 2020 extrusion, and the published profile carries the numbers from there. Pixels carry no millimetres, so a dimension read off a photo is a guess and gets marked like one.

**A phone scan is reference geometry, not metrology.** Its error changes with the phone, capture mode, surface and technique, so no universal millimetre threshold makes it a caliper. `nurb scan` reads the mesh in mm, states the units it used, and slices profile polylines to sketch against. Record what it gave with `how` naming the file and the slice, and keep every scan-derived fit `provisional` until a coupon proves it against the real object.

**A fit coupon turns a loose measurement into a tight one.** Before printing a part modelled against a scan or a photo, print the mating surface alone: a thin strip carrying just the profile, minutes of filament. Held against the real object it shows every gap the numbers hid, the parameters get corrected, and only then does the full part print. A coupon that fits is what takes the provisional flag off.

**When there is nobody to ask**, write the guess down and mark it `provisional = true`.
The danger was never the guess, it is that a guess and a measurement look identical six
months later. `how` is still required, because "eyeballed against a broom" tells the
next person how far to trust it, and `nurb check` lists every provisional value until
somebody picks up a caliper.

A measured value pays for itself across a family. Notch measured one bracket pitch and
amortized it over sixteen parts.

## Assemblies

Every rule above judges one solid being manufactured. An assembly judges solids being
used together: a door on its mount, a lid over the machine it covers. The failure it
exists for built clean, checked clean, exported watertight and printed beautifully,
then jammed at 45 degrees of its swing, because the collision between two correct
parts existed only in the physical world. No per-solid rule can have an opinion about
motion.

The contract mirrors a part's. An assembly is a function in `parts/` whose keyword
defaults are its parameters; what it returns is placed solids rather than one solid.
`use(name)` builds a sibling part where it was modelled, `hinge(solid, axis, through,
at)` declares a revolute joint and poses it, and `obstacle(solid, name)` adds what the
parts mount into: the machine, the wall, the shelf above. The joint angle is an
ordinary keyword default, so the viewer's slider swings it live, and the slider ends
exactly where the declared range does.

**The declared range is a claim, and `nurb check` audits it** the way min_wall audits
a wall: each hinge sweeps through it against everything else in the scene, and a
finding is the angle where it jams plus the coordinates of the contact. Declare what
the design needs, never what happens to pass. A door that must stay open by gravity
needs past 90 degrees; declaring (0, 90) because that sweeps clean is writing the test
to match the bug.

**Nothing full width may cross the pivot line.** The mount that carries a hinge has to
reach the pin from somewhere, so some of it always lives above or behind the pin, and
any full-width material on the moving part that reaches past the pivot sweeps straight
into it. The door that jammed at 45 did so against its own top edge, carried past the
pin to support the knuckles; the knuckles got narrow tabs instead, sized to pass
beside the mount, and the panel now starts at the pivot line.

**Obstacles are boxes and prisms, never thin hand-drawn profiles.** Three nearly
collinear points make a razor sliver, and OCCT answers a boolean against a degenerate
solid with chunks of the other operand: measured once as a 152,000mm3 phantom
collision at a pose that was actually clear. The sweep refuses any intersection that
is not a subset of its inputs and names the solid to fix, but the fix is to model the
obstacle as something with honest volume in the first place.

**Tangent is clear, and clear is not clearance.** Collision is intersection volume, so
two faces that kiss at zero volume pass, the closed door resting on its stop included.
In plastic a zero-clearance pass is already a bind. The declared range should carry
the same honesty about clearance that a tongue's `fit` carries about width. The fits
table puts numbers to that honesty: 0.3mm is the least a moving pair carries through
its whole travel, and 0.5mm is what never binds.

**The stop the sweep finds can be the detent the design wants.** The door that
motivated all of this rests open at 240 degrees against the back of its own mount,
held there by gravity, and that contact is a feature with a card entry, not a finding
to engineer away. Read a jam before redesigning around it.

**Never trust a swing worked out by hand.** The same hinge was hand-modelled three times and gave three answers, one of them "impossible"; the wrong one ran a convex test against a non-convex profile, which is exactly the kind of quiet modelling error a kernel boolean cannot make. The sweep is the authority.

**The sweep is priced per pose, and the declaration sets the pose count.** Every step is a kernel boolean against the rest of the scene, so a door walking 90 degrees at the default 3-degree step is cheap, while a full-circle rotor at the same step is 120 poses and can hold the check for seconds on real geometry. A clean sweep pays the whole walk, since only a jam stops it early. `through=(0, 360)` at the default step is a fine-grained jam audit, not a formality: a free spinner that only needs a gross clearance check should declare a larger `step`, and a range wider than the design actually claims buys nothing but poses.

One hinge sweeps at a time; the others hold their pose, which is the conservative
reading of a mechanism you can only move one hand at a time. Printability rules stay
off assemblies entirely: each part already answered them alone, and overhang measured
on an assembled scene reports confident nonsense.

## Verification

"It built" is not verification. `nurb verify` runs the machine-checkable part of
this list: one solid per configuration, every count flexed upward, the rules clean,
and the card agreeing with the geometry. `--report` writes the verdict into
`build/renders/<part>.verify.md` with the renders that back it beside it, one still
per finding. The two it cannot do are the two that need you, and they are items 2 and 6.

Before presenting a part:

1. **Flex the driving parameters up as well as down**, for example 4 to 6 to 2 to 4.
   Growth is what catches a frozen selector; shrinking alone passes a broken part.
2. **Check fit-critical faces by coordinate** after any polish or resize. `nurb inspect`
   lists them, with each finding resolved to the face it fired on. Which faces are
   fit-critical is still yours to know, which is why this is not something `nurb verify`
   can run for you.
3. **Confirm the solid count**, which is almost always one.
4. **Run `nurb check`.** Zero findings is the bar, and a finding fired at a part that
   prints fine is a bug in the rule, not something to accept quietly.
5. **Predict a baseline before you look at it.** Working out what the sliver count
   should be from the polish exclusions turns the number into a test of the rule instead
   of something to write down.
6. **Render it and actually look.** `nurb render <part>` writes a PNG, `--section
   z:4mm` cuts it open where outside views cannot reach, and `nurb inspect --render`
   stands a camera at every finding with the guilty face painted. A part can pass
   every numeric check and still be visibly wrong.
