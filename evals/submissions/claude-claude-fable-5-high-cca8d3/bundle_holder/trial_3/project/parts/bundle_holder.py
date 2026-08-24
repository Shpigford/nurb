from nurb import *

# The screw is an M4 pan head, and its numbers are fixed by the standard, not by
# the bundle: 4.4 clearance bore, 8.4 head-and-driver envelope, 3.2 head height.
SCREW_BORE_DIA = 4.4
SCREW_HEAD_DIA = 8.4


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), holder_length=12.0,
                  draft=False):
    """Wall clip for a horizontal cable bundle, mounted with one M4 screw.

    An open-top channel: back plate against the wall, floor under the bundle,
    front lip so it cannot pull away. The bundle threads in along its run.

    bundle_diameter: how thick the cable bundle is across
    holder_length: how long the clip runs along the bundle
    """
    if bundle_diameter < 2.0:
        reject("bundle_diameter under 2mm leaves nothing worth clipping: "
               "raise it above 2", param="bundle_diameter")
    if holder_length < 10.0:
        reject("holder_length under 10mm gives too little wall contact: "
               "raise it to 10 or more", param="holder_length")

    r = bundle_diameter / 2
    back = 2.8                        # M4 head needs 2.4 of seat depth; 2.8 gives margin
    floor_t = 2.4                     # channel floor, blocks the bundle falling
    lip_t = 2.4                       # front lip, blocks the bundle pulling away
    channel = bundle_diameter + 0.6   # 0.4 clearance required for the fit, 0.6 given
    lip_top = floor_t + r + 1.0       # past the bundle's centre: it cannot ride out
    # The head plus driver must clear the seated bundle entirely on its way in.
    screw_z = floor_t + bundle_diameter + SCREW_HEAD_DIA / 2 + 1.4
    top = screw_z + SCREW_HEAD_DIA / 2 + 1.8   # 1mm top chamfer stays off the seat
    width = back + channel + lip_t

    plate = Pos(back / 2, 0, top / 2) * Box(back, holder_length, top)
    floor = Pos(width / 2, 0, floor_t / 2) * Box(width, holder_length, floor_t)
    lip = Pos(width - lip_t / 2, 0, lip_top / 2) * Box(lip_t, holder_length, lip_top)
    body = plate + floor + lip

    bore = (Pos(back / 2, 0, screw_z) * Rot(0, 90, 0)
            * Cylinder(SCREW_BORE_DIA / 2, back + 2))
    body -= bore

    if draft:
        return body

    concave = concave_edges(body)

    def keepable(e):
        bb = e.bounding_box()
        if bb.max.X < 1e-6:           # lies in the back face, against the wall
            return False
        if bb.max.Z < 1e-6:           # lies in the bottom face, on the bed
            return False
        # Top end edges stay sharp: a third chamfer at those corners leaves
        # the sub-mm2 triangle facet the sliver rule rightly refuses.
        if bb.min.Z > top - 1e-6 and bb.max.X - bb.min.X > 1e-3:
            return False
        c = e.center()
        # Bore rims stay sharp: a chamfer there spends the head's seat depth.
        if (c.Y ** 2 + (c.Z - screw_z) ** 2) ** 0.5 < SCREW_BORE_DIA / 2 + 1.2:
            return False
        return not any(e.is_same(ce) for ce in concave)

    keep = body.edges().filter_by(keepable)
    return polish(body, keep, 1.0)
