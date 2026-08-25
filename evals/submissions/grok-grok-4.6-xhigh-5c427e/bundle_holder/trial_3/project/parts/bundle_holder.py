from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Wall clip for a horizontal cable bundle, one M4 pan-head screw.

    bundle_diameter: measured width of the taped cable bundle
    """
    if bundle_diameter < 1.0:
        reject(
            f"bundle_diameter {bundle_diameter} is under 1mm; raise it so a bundle can sit",
            param="bundle_diameter",
        )

    # Fit: 0.4mm across the seat so an 8.0 bundle sits in 8.4 of free space.
    clearance = 0.4
    inner = bundle_diameter + clearance
    wall = 2.6
    # M4 pan-head: 4.4 through-bore, 8.4 head-and-driver path, 2.4mm of material to the seat.
    hole_d = 4.4
    head_d = 8.4
    seat = 2.6
    length = 12.0
    head_gap = 0.8

    depth = seat + inner + wall
    channel_h = wall + inner
    screw_z = channel_h + head_d / 2 + head_gap
    height = screw_z + hole_d / 2 + wall
    screw_y = length / 2

    back = Box(seat, length, height, align=(Align.MIN, Align.MIN, Align.MIN))
    floor = Box(depth, length, wall, align=(Align.MIN, Align.MIN, Align.MIN))
    front = Pos(depth - wall, 0, 0) * Box(
        wall, length, channel_h, align=(Align.MIN, Align.MIN, Align.MIN)
    )
    body = back + floor + front

    bore = Pos(seat / 2, screw_y, screw_z) * Rot(Y=90) * Cylinder(hole_d / 2, seat + 4)
    body -= bore

    if draft:
        return body

    bed = body.bounding_box().min.Z
    back_x = body.bounding_box().min.X
    inside = {
        (round(edge.center().X, 4), round(edge.center().Z, 4))
        for edge in concave_edges(body)
    }
    keep = []
    for edge in body.edges():
        ebb = edge.bounding_box()
        if ebb.min.Z <= bed + 1e-3:
            continue
        if ebb.max.X <= back_x + 1e-3:
            continue
        if (ebb.max.Y - ebb.min.Y) < length * 0.8:
            continue
        if edge.geom_type == GeomType.CIRCLE:
            continue
        if (round(edge.center().X, 4), round(edge.center().Z, 4)) in inside:
            continue
        keep.append(edge)
    return polish(body, keep, 1.0)
