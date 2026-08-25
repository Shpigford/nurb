from nurb import *
from math import sqrt


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Wall clip that traps a horizontal cable bundle on one M4 pan-head screw.

    bundle_diameter: caliper measurement across the taped bundle
    """
    if bundle_diameter < 4.0:
        reject(
            f"bundle_diameter {bundle_diameter} is under 4mm: raise it so the channel can print",
            param="bundle_diameter",
        )

    clearance = 0.5
    inner = bundle_diameter + clearance
    wall = 2.4
    back = 2.6
    length = 12.0
    screw_hole = 4.4
    head_clear = 8.4
    head_gap = 1.4

    floor_top = wall
    channel_top = floor_top + inner
    hole_z = channel_top + head_clear / 2.0 + head_gap
    hole_r = screw_hole / 2.0
    tear_tip = hole_r * sqrt(2.0)
    plate_top = hole_z + tear_tip + wall
    depth = back + inner + wall

    back_plate = Box(back, length, plate_top, align=(Align.MIN, Align.CENTER, Align.MIN))
    floor = Box(depth, length, wall, align=(Align.MIN, Align.CENTER, Align.MIN))
    lip = Box(wall, length, inner, align=(Align.MIN, Align.CENTER, Align.MIN))
    lip = lip.move(Location((back + inner, 0, floor_top)))
    body = back_plate + floor + lip

    bore = Cylinder(
        hole_r,
        back + 2.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    bore = bore.rotate(Axis.Y, 90.0).move(Location((-1.0, 0, hole_z)))
    tan = hole_r / sqrt(2.0)
    tear = Face(
        Wire.make_polygon(
            [
                Vector(-1.0, -tan, hole_z + tan),
                Vector(-1.0, tan, hole_z + tan),
                Vector(-1.0, 0.0, hole_z + tear_tip),
            ]
        )
    )
    tear = extrude(tear, amount=back + 2.0)
    body = body - (bore + tear)

    if draft:
        return body

    bed = body.bounding_box().min.Z
    concave = concave_edges(body)

    def polishable(e):
        if e.length <= 7.0:
            return False
        if e.bounding_box().min.Z <= bed + 0.05:
            return False
        c = e.bounding_box().center()
        if abs(c.Y) < hole_r + 0.6 and abs(c.Z - hole_z) < tear_tip + 0.6:
            return False
        if (
            back - 0.05 < c.X < back + inner + 0.05
            and floor_top - 0.05 < c.Z < channel_top + 0.05
        ):
            return False
        return True

    polish_edges = body.edges().filter_by(polishable)
    polish_edges = polish_edges - concave
    return polish(body, polish_edges, 1.0)
