from nurb import *


@part
def bundle_holder(bundle_diameter=8.0, draft=False):
    """Wall clip that traps a cable bundle with one M4 pan-head screw.

    bundle_diameter: calipered width of the taped cable bundle
    """
    if bundle_diameter < 3.0:
        reject(
            "bundle_diameter is under 3mm: raise it so the clip can close around the cables",
            param="bundle_diameter",
        )

    # 0.4 across the seat so an 8.0 bundle still drops into an 8.4 pocket.
    cavity = bundle_diameter + 0.4
    wall = 2.4
    back = 3.0
    length = 12.0
    screw_hole = 4.4
    head_clear = 8.4
    hole_r = screw_hole / 2.0
    head_r = head_clear / 2.0

    channel_top = wall + cavity
    screw_z = channel_top + 0.8 + head_r
    plate_top = screw_z + hole_r + 2.4
    y_c = length / 2.0

    back_plate = Box(back, length, plate_top, align=(Align.MIN, Align.MIN, Align.MIN))
    floor = Box(
        cavity + wall, length, wall, align=(Align.MIN, Align.MIN, Align.MIN)
    ).moved(Location((back, 0, 0)))
    front = Box(
        wall, length, channel_top, align=(Align.MIN, Align.MIN, Align.MIN)
    ).moved(Location((back + cavity, 0, 0)))
    body = back_plate + floor + front

    hole = Cylinder(hole_r, back + 4.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    hole = hole.rotate(Axis.Y, 90).moved(Location((-1.0, y_c, screw_z)))
    body = body - hole

    if draft:
        return body

    bed = body.bounding_box().min.Z
    conc = concave_edges(body)
    keep = []
    for e in body.edges():
        bb = e.bounding_box()
        if bb.min.Z <= bed + 0.05:
            continue
        # Floor-level inner junctions are concave; chamfering them leaves a
        # cosmetic strip in the channel.
        if bb.min.Z < wall + 0.3:
            continue
        if (bb.max.Y - bb.min.Y) < length - 0.2:
            continue
        if e in conc:
            continue
        mid_x = 0.5 * (bb.min.X + bb.max.X)
        # Leave the inner lip square; a 1mm chamfer on both sides of a 2.4mm
        # wall would meet in a knife edge.
        if mid_x < back + 0.2 or mid_x > back + cavity + wall - 0.2:
            keep.append(e)
    return polish(body, keep, 1.0)
