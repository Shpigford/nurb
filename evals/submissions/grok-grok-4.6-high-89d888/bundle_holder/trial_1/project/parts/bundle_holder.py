from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Wall clip for a cable bundle that runs horizontally along the wall.

    bundle_diameter: calipered width of the taped cable bundle
    """
    if bundle_diameter < 2.0:
        reject(
            f"bundle_diameter {bundle_diameter} is under 2mm: raise it so the "
            "trough and screw pad still have room to print",
            param="bundle_diameter",
        )

    # 0.4 across so an 8mm bundle sits in an 8.4mm channel.
    inner = bundle_diameter + 0.4
    back = 3.0  # wall plate; 2.4mm is the minimum along the screw bore
    wall = 2.2
    length = 14.0  # along the bundle (Y); 10mm is the minimum
    screw_hole = 4.4
    driver = 8.4

    floor = wall
    front = wall
    front_top = floor + inner
    bundle_cz = floor + inner / 2
    bundle_top = bundle_cz + bundle_diameter / 2

    # Screw above the trough: the 8.4 driver and the 3.2 pan head stay clear of
    # both the bundle and the front wall that blocks it from leaving +X.
    screw_z = max(front_top, bundle_top) + driver / 2 + 1.2
    pad_top = screw_z + screw_hole / 2 + wall
    outer_x = back + inner + front

    back_plate = Box(back, length, pad_top, align=(Align.MIN, Align.CENTER, Align.MIN))
    base = Box(outer_x, length, floor, align=(Align.MIN, Align.CENTER, Align.MIN))
    front_wall = Pos(back + inner, 0, 0) * Box(
        front, length, front_top, align=(Align.MIN, Align.CENTER, Align.MIN)
    )
    body = back_plate + base + front_wall

    hole = Pos(back / 2, 0, screw_z) * Rot(Y=90) * Cylinder(screw_hole / 2, outer_x + 4)
    body -= hole

    if draft:
        return body

    def edge_key(e):
        c = e.bounding_box().center()
        return (round(c.X, 2), round(c.Y, 2), round(c.Z, 2), round(e.length, 2))

    concave = {edge_key(e) for e in concave_edges(body)}
    keep = []
    for e in body.edges():
        if edge_key(e) in concave or e.geom_type == GeomType.CIRCLE:
            continue
        bb = e.bounding_box()
        # Long profile edges only: chamfering the Y-ends too makes slivers
        # where three 1mm chamfers meet on the 2.2mm front wall.
        along_y = (bb.max.Y - bb.min.Y) > length * 0.5
        if not along_y or (bb.max.X - bb.min.X) > 0.3 or (bb.max.Z - bb.min.Z) > 0.3:
            continue
        if bb.min.Z <= 0.05 or bb.min.X <= 0.05:
            continue
        # Both tops of the front wall are only `front` apart; one 1mm polish
        # is enough, the inner lip stays sharp so the wall is not a sliver.
        if abs(bb.min.X - (back + inner)) < 0.2 and abs(bb.min.Z - front_top) < 0.2:
            continue
        keep.append(e)
    return polish(body, keep, 1.0) if keep else body
