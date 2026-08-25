from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Wall clip for a taped cable bundle, one M4 pan-head screw.

    bundle_diameter: how wide the cable bundle is, across the tape
    """
    # 0.5mm across the opening so an 8.0 bundle has 8.5 to sit in (need >= 8.4).
    # Extra height keeps the 1mm rim chamfer above the bundle's side.
    # Wall at min X blocks the bundle toward the wall; the trough floor blocks
    # -Z; the front wall blocks +X.
    opening = bundle_diameter + 0.5
    wall = 2.4
    back = 3.2
    length = 11.0
    screw_hole = 4.4
    pad_height = 11.0
    rim_clear = 1.0

    if bundle_diameter < 4.0:
        reject(
            f"bundle_diameter {bundle_diameter} is under 4mm; raise it so the "
            "clip still has room for the M4 and a printable wall",
            param="bundle_diameter",
        )

    cradle_h = wall + opening + rim_clear
    height = cradle_h + pad_height
    depth = back + opening + wall
    screw_z = cradle_h + pad_height / 2.0
    bundle_x = back + opening / 2.0
    bundle_z = wall + opening / 2.0

    back_plate = Box(back, length, height, align=(Align.MIN, Align.CENTER, Align.MIN))
    cradle = Box(depth, length, cradle_h, align=(Align.MIN, Align.CENTER, Align.MIN))
    body = back_plate + cradle

    # Open-top U along Y, rounded trough so the bundle nests. Overshoot the rim
    # so the boolean does not leave a film.
    trough = Pos(bundle_x, 0, bundle_z) * Rot(X=90) * Cylinder(
        opening / 2.0,
        length + 4.0,
    )
    slot = Pos(back, 0, bundle_z) * Box(
        opening,
        length + 4.0,
        opening / 2.0 + rim_clear + 2.0,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    body = body - (trough + slot)

    # M4 medium clearance, axis along X, mouth on the wall face. Seat is the
    # pad's +X face; nothing of the clip sits in front of it for the driver.
    hole = Pos(-2.0, 0, screw_z) * Rot(Y=90) * Cylinder(
        screw_hole / 2.0,
        back + 4.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    body = body - hole

    if draft:
        return body

    bed = body.bounding_box().min.Z
    xmin = body.bounding_box().min.X
    concave_at = {
        (
            round(e.center().X, 3),
            round(e.center().Y, 3),
            round(e.center().Z, 3),
            round(e.length, 3),
        )
        for e in concave_edges(body)
    }

    def polishable(edge):
        # Long exposed edges only. Chamfering all three edges of a 1mm corner
        # leaves a 0.87mm2 triangle the sliver rule will not forgive.
        if edge.length < 6.0:
            return False
        bb = edge.bounding_box()
        if bb.min.Z <= bed + 1e-3:
            return False
        if bb.max.X <= xmin + 1e-3:
            return False
        c = edge.center()
        key = (round(c.X, 3), round(c.Y, 3), round(c.Z, 3), round(edge.length, 3))
        if key in concave_at:
            return False
        if abs(c.Y) < 0.8 and abs(c.Z - screw_z) < screw_hole:
            return False
        return True

    keep = body.edges().filter_by(polishable)
    return polish(body, keep, 1.0)
