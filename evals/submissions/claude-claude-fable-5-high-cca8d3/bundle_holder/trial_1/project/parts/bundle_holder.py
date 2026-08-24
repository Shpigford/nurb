from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), holder_length=12.0, draft=False):
    """Wall-mounted J-channel clip for a horizontal cable bundle, one M4 pan-head screw.

    bundle_diameter: how thick the cable bundle is across
    holder_length: how long the holder runs along the wall
    """
    if bundle_diameter < 1.0:
        reject(
            "bundle_diameter under 1mm leaves no channel to hold: raise it above 1",
            param="bundle_diameter",
        )
    if holder_length < 10.0:
        reject(
            "holder_length under 10mm gives the clip too little grip on the bundle: raise it to 10 or more",
            param="holder_length",
        )

    d = bundle_diameter
    length = holder_length
    clearance = 0.4          # total extra across the channel so the bundle threads in
    back_t = 3.0             # wall plate; also the bore length the screw head seats against
    floor_t = 2.4            # shelf under the bundle, blocks it falling
    lip_t = 2.4              # outer lip, blocks it pulling off the wall
    gap = d + clearance      # channel opening, back plate face to lip face

    head_r = 4.2             # M4 pan head + driver clearance radius
    hole_dia = 4.5           # ISO 273 medium clearance for M4

    lip_top = floor_t + d / 2.0 + 1.0
    bundle_top = floor_t + d
    screw_z = bundle_top + head_r + 0.5   # head clears over the seated bundle
    plate_top = screw_z + head_r + 2.0    # flat seat all around the head, past the chamfer
    outer_x = back_t + gap + lip_t

    plate = Pos(back_t / 2.0, 0, plate_top / 2.0) * Box(back_t, length, plate_top)
    shelf = Pos(back_t + (gap + lip_t) / 2.0, 0, floor_t / 2.0) * Box(gap + lip_t, length, floor_t)
    lip = Pos(back_t + gap + lip_t / 2.0, 0, lip_top / 2.0) * Box(lip_t, length, lip_top)
    body = plate + shelf + lip

    bore = Pos(back_t / 2.0, 0, screw_z) * Cylinder(
        hole_dia / 2.0, back_t + 2.0, rotation=(0, 90, 0)
    )
    body -= bore

    if draft:
        return body

    # Polish everything except the bed face, the wall face, the bore rims
    # (the head must seat on a flat ring) and the concave channel junctions.
    concave = concave_edges(body)
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > 1e-6
        and e.bounding_box().max.X > 1e-6
        and e.geom_type != GeomType.CIRCLE
        and e not in concave
    )
    # 1.1 rather than 1.0: the corner triangles three chamfers leave scale as
    # 0.866 * size**2, and 1.1 puts them just over the 1mm2 sliver floor.
    return polish(body, keep, 1.1)
