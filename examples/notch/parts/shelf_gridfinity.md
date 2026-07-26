# shelf_gridfinity

Ported from Fusion `Shelf - Gridfinity 2x2 - 4x` v4.

## What it is

A bracket-mount shelf whose platform is a spec-true gridfinity baseplate, `grid_x` by
`grid_y` sockets, 2x2 by default. Any standard gridfinity bin drops in and is located
by the spec's z-profile. The anti-lift detent is what keeps the shelf on the wall when
a bin is pulled straight up.

This is the hardest part in the library and the reason Phase 1 exists: four lofted
sockets, a grid array, two gussets, two chamfer passes, and a known sliver baseline.

## Design notes

- **Socket geometry is the gridfinity spec.** Per cell, cut down from the platform
  top: mouth 42.0 r4 -> 45 degree band 2.15 -> vertical 1.8 at 37.7 r1.85 -> 45 degree
  band 0.7 -> floor 36.3 r1.15 -> 0.35 clearance recess, 5.0mm total. Bins seat on the
  two bands with 0.25mm/side clearance and must never bottom out, so the recess is
  required rather than optional. Verified against gridfinity-rebuilt-openscad.
- Built as a single 5-section `loft(ruled=True)` rather than Fusion's four features.
  The widths and radii fall out of the two chamfer depths, so the 45 degree bands are
  exact by construction instead of by dimension.
- `GridLocations` replaces `SocketArray` outright. No pattern feature, no instance
  counting, no seed-inclusion trap.
- `shelf_thickness` 7mm = 5mm pocket + 2mm floor. That is the floor of the parameter:
  below it the pocket floor goes under 2mm and gets drummy under load.
- `back_gap` 4mm stands the grid off the slab. It is bin insertion clearance and it is
  the land the 3mm structural chamfer needs, whose forward leg takes 3 of those 4mm.
- Gussets double as side cheeks, so `platform_width = grid + 2 x gusset_thickness`.
  Their inner faces are flush with the outer cells' mouths.
- **Front and outer mouth rims are sharp 45 degree knife edges** flush with the
  platform edge, exactly like a real baseplate. They are left out of the cosmetic pass
  on purpose, not by oversight.
- Sliver baseline is 18 faces: 16 recess-corner segments at 0.632mm² (spec geometry,
  four per cell) plus 2 three-chamfer corner triangles at 0.866mm². It generalizes as
  `4 * grid_x * grid_y + 2`, confirmed at 1x2, 2x2, 2x3 and 3x2.
- Verified: channel floors at x=-4.2 with y-centers exactly 0, 25.16, 50.32, 75.48,
  every floor the full 21.56mm span. Flexes 4 -> 6 -> 4 with the baseline unchanged.

## Accepted

Eighteen faces under 1mm2 at the default 2x2: sixteen recess corners at 0.632mm2,
which are gridfinity spec geometry and come four to a cell, plus two three-chamfer
corner triangles at 0.866mm2. It generalizes as `4 * grid_x * grid_y + 2`, so a
different grid wants a different number here. A nineteenth at 2x2 is a regression.

```toml
[accepted]
sliver = 18

[part]
forward = [-1, 0, 0]
```

## Don't

- **Don't set `gusset_drop` to 2mm.** Fusion needed exactly 2mm to keep the gusset peak
  off the slab-top chamfer boundary, and OCCT needs more: the peak and the slab top
  both get a 1mm chamfer, and if the two bands meet the kernel cannot build the corner
  and raises "BRep_API: command not done". The rule is that `gusset_drop` must clear
  twice `chamfer_size`. 3mm leaves a millimeter of clean face.
- **Don't run a grid wider than the slab.** Two polished edges need more than twice
  the chamfer between them, which is where the pairings come from: grid_x 1 needs 3
  brackets, 2 needs 4, 3 needs 6. The part raises a `ValueError` saying so rather than
  failing in the chamfer.
- **Don't read that one guard as general cover.** It checks the grid against the slab
  and nothing else, and there are four more places on this part where the same
  clearance rule bites, each one notch from a default: `chamfer_size` 1.5 (collides
  with both `gusset_drop` and `gusset_thickness`), `back_gap` 3 or less and
  `structural_chamfer` 4 or more (the structural band runs into the first socket
  mouth at x=-10), and `gusset_thickness` 2. All four fail with the bare OCCT message.
  They are not guarded on purpose, since four more checks would cost more than they
  return, but do the arithmetic before you move any of them.
- **Don't chamfer anything in the socket band or along the gusset-platform junction.**
  The rims are meant to be sharp and the junctions are concave.
- **Don't add a `gusset_count`.** The Fusion part carries one because the shelf family
  shares a template, but here the gussets are the side cheeks. A third one lands in
  the middle of a cell and blocks a bin.
- **Don't raise `grid_y` past 2 without raising `item_height`.** At grid_y 3 the
  projection is 136mm, a ratio of 3.2 at item_height 42. About 55mm brings it back
  under 2.5.
- **Don't add magnet holes** unless a print asks for it. Bins sit in the sockets and
  the detent handles anti-lift.

## Changelog

- 2026-07-25: ported to nurb. Bounding box matches the Fusion v4 exactly
  (94 x 100.64 x 42mm) and the 18-face sliver baseline reproduces. `gusset_drop`
  raised 2 -> 3mm for OCCT; see Don't.
