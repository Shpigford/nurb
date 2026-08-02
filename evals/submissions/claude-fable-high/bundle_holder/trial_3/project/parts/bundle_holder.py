from nurb import *

SCREW_HOLE_DIAMETER = 4.4   # M4 clearance bore
SCREW_HEAD_DIAMETER = 8.4   # pan head plus driver envelope
BUNDLE_CLEARANCE = 0.6      # slack across the channel so the bundle threads freely


@part
def bundle_holder(
    bundle_diameter=measured("bundle_diameter"),
    length=12.0,
    draft=False,
):
    """Wall-mounted holder for a horizontal cable bundle, one M4 screw.

    bundle_diameter: how wide the cable bundle measures across
    length: how far the holder runs along the wall
    """
    back_thickness = 2.8    # screw seat depth, comfortably past the 2.4 minimum
    floor_thickness = 2.4
    lip_thickness = 2.4

    gap = bundle_diameter + BUNDLE_CLEARANCE
    depth = back_thickness + gap + lip_thickness
    lip_height = floor_thickness + 0.6 * bundle_diameter

    # Screw sits above the channel so the installed head never reaches the bundle.
    screw_z = floor_thickness + bundle_diameter + SCREW_HEAD_DIAMETER / 2 + 0.4
    # 1.5 keeps the seat face solid past the head circle even after the
    # plate's 1mm front-top chamfer.
    height = screw_z + SCREW_HEAD_DIAMETER / 2 + 1.5

    corner = (Align.MIN, Align.MIN, Align.MIN)
    body = Box(depth, length, floor_thickness, align=corner)
    body += Box(back_thickness, length, height, align=corner)
    body += Pos(depth - lip_thickness, 0, 0) * Box(
        lip_thickness, length, lip_height, align=corner
    )
    body -= Pos(back_thickness / 2, length / 2, screw_z) * Rot(0, 90, 0) * Cylinder(
        SCREW_HOLE_DIAMETER / 2, back_thickness + 2
    )

    if draft:
        return body

    concave_centers = [e.center() for e in concave_edges(body)]

    def keepable(e):
        if e.geom_type == GeomType.CIRCLE:  # screw bore stays sharp
            return False
        bb = e.bounding_box()
        if bb.max.X < 1e-6:  # lies in the back face
            return False
        if bb.max.Z < 1e-6:  # lies in the bottom face
            return False
        vertical = (bb.max.X - bb.min.X) < 1e-6 and (bb.max.Y - bb.min.Y) < 1e-6
        if vertical and bb.max.Z > lip_height + 1e-6:
            # The plate's tall front corners stay sharp: a third chamfer
            # meeting the two top chamfers leaves sliver corner triangles.
            return False
        p = e.center()
        return all((p - q).length > 1e-6 for q in concave_centers)

    keep = body.edges().filter_by(keepable)
    return polish(body, keep, 1.0)
