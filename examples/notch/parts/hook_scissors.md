# hook_scissors

Ported from Fusion `Hook - Scissors - 1x` v4.

## What it is

Single-channel J-hook for hanging scissors by their finger holes. A 6mm arm projects
28mm forward at the bottom of the slab with a 15mm upstand at the far end; the
scissors drop into the cradle the two of them make.

It is also the simple case in this library. The gridfinity shelf is the part that
tests the kernel; this one exists so that a failure over there is unambiguously a
kernel problem and not unfamiliarity with the API.

## Design notes

- Bottom-weighted: the arm and upstand sit on the floor of the slab, so the load
  hangs under the channel stop rather than levering against it.
- 30mm slab is the light-part default: 28mm for full bracket engagement plus 2mm
  spare. The 0.93:1 projection-to-height ratio is inside the no-gusset band.
- The J is drawn once as a section on `Plane.XZ` and swept. The Fusion original built
  it as two extrusions plus a chamfer feature; one polygon says the same thing and
  keeps the arm and upstand in one solid, so their junction is an interior edge.
- Structural chamfers are 3mm at the two concave junctions the load runs through.
  The arm-to-slab pair comes from `new_edges`, which reports exactly what the fuse
  created, so it stays correct when `bracket_count` moves.
- The cosmetic pass is 1mm on everything `polish_edges` allows, minus the edges the
  structural pass just made.
- Verified: channel floor at x=-4.2, y-center exactly 0, floor span the full 21.56mm.
  Flexes 1 -> 2 -> 3 -> 1 with the floors landing on exact pitch every time.
- Sliver baseline is 6 faces at 0.866mm², all of them the corner triangles where
  three 1mm chamfers meet. That is the same count the Fusion part carried, and it
  is what confirms the polish exclusions match.

## Accepted

Six faces under 1mm2, and all six are the corner triangles where three 1mm chamfers
meet at a convex corner. That is the only tiny face the doctrine allows. A seventh
means the polish pass has started cutting something it should not.

The thinnest section is 1.0mm, behind the detent dimple: 6mm slab less the 4.2mm
channel less the 0.8mm dimple. It is a consequence of the fit geometry rather than
a choice, and it prints.

```toml
[part]
min_wall = 1.0
forward = [-1, 0, 0]

[accepted]
sliver = 6
```

## Don't

- **Don't chamfer the channel mouths.** The 1.5mm lead-in was retired on 2026-07-22
  because it made tiny compound facets that print badly on other people's machines.
  `polish_edges` already excludes them; do not add them back.
- **Don't run a feature's back face behind x=-4.2.** It fills the dovetail and the
  part will not go on the wall. `MERGE_X` is the constant to use.
- **Don't chamfer the detent dimple.** Its walls are 0.8mm, so a 1mm chamfer fails
  outright, and it is fit geometry regardless.
- **Don't lengthen the slab to fix a projection ratio without checking it first.**
  v1 was 45mm and got cut to 30mm for looking wrong on a small hook.

## Changelog

- 2026-07-26: channel clearance 0.5 -> 0.3mm per side, from a printed calibration
  ladder. The first nurb print of this hook was loose side to side, and being a 1x it
  has only one channel constraining yaw. Geometry is otherwise untouched: same
  bounding box, same 6 slivers.
- 2026-07-25: ported to nurb. Geometry matches the Fusion v4 bounding box exactly
  (34 x 25.16 x 30mm) and the sliver baseline is unchanged at 6.
