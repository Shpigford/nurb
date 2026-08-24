from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Wall clip for a taped cable bundle, one M4 pan-head screw.

    bundle_diameter: caliper reading across the taped bundle
    """
    if bundle_diameter < 3.0:
        reject(
            "bundle_diameter is under 3mm: raise it to the taped-bundle reading",
            param="bundle_diameter",
        )

    clearance = 0.4
    seat = bundle_diameter + clearance
    wall = 2.4
    back_t = 2.6
    length = 12.0
    hole_d = 4.4
    hole_r = hole_d / 2.0
    driver_r = 8.4 / 2.0
    driver_gap = 1.2
    pad_above = 2.8

    lip_h = wall + seat
    screw_z = lip_h + driver_r + driver_gap
    total_h = screw_z + hole_r + pad_above
    equator_z = wall + seat / 2.0
    seat_x = back_t + seat / 2.0
    x_lip = back_t + seat
    x_front = x_lip + wall

    back = Pos(back_t / 2.0, 0, total_h / 2.0) * Box(back_t, length, total_h)

    # Channel profile in XZ, extruded along Y: rounded trough opening +Z.
    chan_plane = Plane(
        origin=(0, length / 2.0, 0),
        x_dir=(1, 0, 0),
        z_dir=(0, -1, 0),
    )
    with BuildSketch(chan_plane) as chan_sk:
        with BuildLine():
            Line((back_t, 0), (x_front, 0))
            Line((x_front, 0), (x_front, lip_h))
            Line((x_front, lip_h), (x_lip, lip_h))
            Line((x_lip, lip_h), (x_lip, equator_z))
            ThreePointArc((x_lip, equator_z), (seat_x, wall), (back_t, equator_z))
            Line((back_t, equator_z), (back_t, 0))
        make_face()
    channel = extrude(chan_sk.sketch, amount=length)
    body = back + channel

    # M4 clearance through the back plate, axis along +X.
    hole = Cylinder(
        hole_r, back_t + 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    hole = Pos(-0.5, 0, screw_z) * Rot(Y=90) * hole
    body = body - hole

    if draft:
        return body

    bed = body.bounding_box().min.Z
    xmin = body.bounding_box().min.X
    forbidden = concave_edges(body)

    def keep_edge(e):
        if e in forbidden:
            return False
        bb = e.bounding_box()
        if bb.min.Z <= bed + 0.05:
            return False
        if bb.min.X <= xmin + 0.05:
            return False
        c = e.center()
        if (
            abs(c.Z - screw_z) < hole_r + 0.6
            and abs(c.Y) < hole_r + 0.6
            and c.X < back_t + 0.6
        ):
            return False
        in_trough_x = back_t - 0.05 < c.X < x_lip + 0.05
        in_trough_z = wall - 0.05 < c.Z < lip_h + 0.05
        if in_trough_x and in_trough_z:
            return False
        if bb.min.Z > total_h - 0.08:
            return False
        if bb.min.Z > lip_h - 0.08 and c.X > back_t + 0.5:
            return False
        return True

    keep = body.edges().filter_by(keep_edge)
    return polish(body, keep, 1.0)
