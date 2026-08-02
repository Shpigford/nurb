from nurb import *


@part
def bundle_holder(
    bundle_diameter=measured("bundle_diameter"),
    holder_length=12.0,
    draft=False,
):
    """A J-hook that cradles a horizontal cable bundle against the wall.

    bundle_diameter: how wide the cable bundle measures across
    holder_length: how long the holder runs along the bundle
    """
    back_thickness = 3.0        # screw bore runs through this; head seats on its front
    shelf_thickness = 2.0       # floor under the bundle
    lip_thickness = 2.0         # front wall that keeps the bundle from sliding off
    bundle_fit = bundle_diameter + 0.4   # what must drop into the cradle
    pocket_width = bundle_fit + 0.2      # cradle opening, back face to lip

    screw_head_radius = 4.2     # M4 pan head and driver envelope, 8.4 across
    bore_radius = 2.2           # 4.4 clearance bore for the M4 shank

    lip_top = shelf_thickness + pocket_width / 2 + 1.0
    bundle_top = shelf_thickness + bundle_fit
    screw_height = bundle_top + screw_head_radius + 0.8
    plate_height = screw_height + screw_head_radius + 1.5
    reach = back_thickness + pocket_width + lip_thickness

    plate = Box(
        back_thickness, holder_length, plate_height,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    shelf = Box(
        reach, holder_length, shelf_thickness,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    lip = Pos(back_thickness + pocket_width, 0, 0) * Box(
        lip_thickness, holder_length, lip_top,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    body = plate + shelf + lip

    bore = Pos(back_thickness / 2, 0, screw_height) * Rot(0, 90, 0) * Cylinder(
        bore_radius, back_thickness + 2
    )
    body -= bore

    if draft:
        return body

    lip_inner = back_thickness + pocket_width
    concave = [e.center() for e in concave_edges(body)]

    def wants_chamfer(e):
        bb = e.bounding_box()
        if bb.max.X < 1e-6:                 # lies in the back face, against the wall
            return False
        if bb.max.Z < 1e-6:                 # lies in the bed face
            return False
        if e.geom_type == GeomType.CIRCLE:  # bore rims: the seat stays flat
            return False
        if abs(bb.min.X - lip_inner) < 1e-6 and abs(bb.max.X - lip_inner) < 1e-6:
            return False                    # lip inner face: the cradle mouth stays sharp
        if bb.size.Y < 1e-6 and bb.size.Z < 1e-6:
            return False                    # end-face top edges: a third chamfer at a
                                            # corner leaves a sliver triangle
        c = e.center()
        return all((c - cc).length > 1e-3 for cc in concave)

    keep = body.edges().filter_by(wants_chamfer)
    return polish(body, keep, 1.0)
