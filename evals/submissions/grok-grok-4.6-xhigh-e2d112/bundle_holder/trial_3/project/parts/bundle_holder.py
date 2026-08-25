from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Wall clip for a taped cable bundle, held with one M4 pan-head screw.

    bundle_diameter: how wide the taped cable bundle is
    """
    if bundle_diameter < 4.0:
        reject(
            f"bundle_diameter {bundle_diameter} is under 4mm; raise it so the "
            "channel can close around a real bundle",
            param="bundle_diameter",
        )

    # Walls stay at the M4 seat depth so the back is thick enough to clamp against.
    wall = 2.6
    seat_depth = 2.6
    fit_gap = 0.4
    bore = 4.4
    head_clear = 8.4
    around_bore = 3.2
    length = 12.0

    inner = bundle_diameter + fit_gap
    back_t = max(wall, seat_depth)
    overall_x = back_t + inner + wall
    lip_top = wall + inner

    # Screw sits above the channel: the 8.4mm driver must miss the front wall, the
    # 3.2mm pan head must miss the bundle, and the pad must wrap the bore.
    screw_z = max(
        lip_top + head_clear / 2.0 + 0.6,
        wall + inner / 2.0 + bundle_diameter / 2.0 + head_clear / 2.0 + 0.8,
        lip_top + around_bore + bore / 2.0,
    )
    pad_top = screw_z + bore / 2.0 + around_bore

    back_plate = Box(back_t, length, pad_top, align=(Align.MIN, Align.CENTER, Align.MIN))
    floor = Box(overall_x, length, wall, align=(Align.MIN, Align.CENTER, Align.MIN))
    lip = Pos(back_t + inner, 0, 0) * Box(
        wall, length, lip_top, align=(Align.MIN, Align.CENTER, Align.MIN)
    )
    body = back_plate + floor + lip

    hole = Pos(back_t / 2.0, 0, screw_z) * Cylinder(
        bore / 2.0, back_t + 4.0, rotation=(0, 90, 0)
    )
    body = body - hole

    if draft:
        return body

    box = body.bounding_box()
    bed = box.min.Z
    back = box.min.X
    inside = concave_edges(body)
    # Chamfer only the extruded rails. End-face edges would meet those at a
    # corner and leave the 0.9mm2 triangles the sliver rule rejects.
    keep = [
        edge
        for edge in body.edges()
        if edge.bounding_box().min.Z > bed + 1e-3
        and edge.bounding_box().min.X > back + 1e-3
        and abs(edge.tangent_at(0.5).Y) > 0.9
        and edge.geom_type != GeomType.CIRCLE
        and edge not in inside
    ]
    return polish(body, keep, 1.0)
