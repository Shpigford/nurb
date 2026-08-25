from nurb import *


@part
def bundle_holder(bundle_diameter=float(measured("bundle_diameter")), draft=False):
    """Wall-mounted clip that traps a cable bundle on one M4 pan-head screw.

    bundle_diameter: calipered width of the taped cable bundle
    """
    if bundle_diameter < 4.0:
        reject(
            f"bundle_diameter {bundle_diameter} is under 4mm; raise it so the seat can print",
            param="bundle_diameter",
        )

    # 0.4 extra across so an 8.0 bundle sits in 8.4 of free space.
    inner = bundle_diameter + 0.4
    wall = 2.6
    back = 2.6  # >= 2.4 of bore before the pan head seats
    y_len = 12.0
    screw_hole = 4.4
    head_clear = 8.4
    # 8.4 driver path is in +X of the plate, so the hole sits above the cradle.
    screw_z = wall + inner + head_clear / 2 + 1.0
    # Extra millimetre above the hole so the 1mm top chamfer still leaves a ring.
    pad_above = screw_hole / 2 + wall + 1.0
    total_z = screw_z + pad_above
    screw_y = y_len / 2
    align = (Align.MIN, Align.MIN, Align.MIN)

    plate = Box(back, y_len, total_z, align=align)
    floor = Box(back + inner + wall, y_len, wall, align=align)
    lip = Pos(back + inner, 0, 0) * Box(wall, y_len, wall + inner, align=align)
    body = plate + floor + lip

    bore = Pos(back / 2, screw_y, screw_z) * Cylinder(
        screw_hole / 2,
        back + 4,
        rotation=(0, 90, 0),
    )
    body = body - bore

    if draft:
        return body

    bed = body.bounding_box().min.Z
    concave = {_edge_id(e) for e in concave_edges(body)}

    def keep_edge(edge):
        if _edge_id(edge) in concave:
            return False
        if edge.bounding_box().min.Z <= bed + 1e-3:
            return False
        if edge.geom_type == GeomType.CIRCLE:
            return False
        # End-face edges along X would complete a 3-chamfer corner sliver.
        if abs(edge.tangent_at(0.5).X) > 0.9:
            return False
        c = edge.center()
        on_end = min(abs(c.Y), abs(c.Y - y_len)) < 0.25
        in_seat = (back - 0.3 <= c.X <= back + inner + 0.3) and (
            wall - 0.3 <= c.Z <= wall + inner + 0.3
        )
        if on_end and in_seat:
            return False
        return True

    return polish(body, [e for e in body.edges() if keep_edge(e)], 1.0)


def _edge_id(edge):
    c = edge.center()
    return (round(c.X, 3), round(c.Y, 3), round(c.Z, 3), round(edge.length, 3))
