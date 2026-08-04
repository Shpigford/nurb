from nurb import *


@part
def cable_clip(
    bundle_diameter=measured("bundle_diameter"),
    wall_thickness=2.4,
    base_thickness=3.0,
    part_length=12.0,
    tab_length=10.0,
    hole_diameter=4.2,
    draft=False,
):
    """
    bundle_diameter: diameter of the cable bundle the channel clamps around
    wall_thickness: thickness of the two channel walls
    base_thickness: thickness of solid material under the channel floor
    part_length: length of the clip along the cable (Y axis)
    tab_length: how far the mounting tab sticks out from the wall
    hole_diameter: diameter of the screw hole through the mounting tab
    """
    channel_width = bundle_diameter + 0.4
    channel_depth = bundle_diameter
    outer_width = channel_width + 2 * wall_thickness
    total_height = base_thickness + channel_depth

    outer = Box(
        outer_width, part_length, total_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    channel_void = Box(
        channel_width, part_length, channel_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    channel_void = Pos(wall_thickness, 0, base_thickness) * channel_void
    body = outer - channel_void

    tab = Box(
        tab_length, part_length, base_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    tab = Pos(-tab_length, 0, 0) * tab
    body = body + tab

    hole = Cylinder(
        hole_diameter / 2, base_thickness + 2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    hole = Pos(-tab_length / 2, part_length / 2, -1) * hole
    body = body - hole

    if draft:
        return body

    bed = body.bounding_box().min.Z
    concave = concave_edges(body)
    channel_x_lo = wall_thickness
    channel_x_hi = wall_thickness + channel_width
    hole_center_x = -tab_length / 2
    hole_center_y = part_length / 2
    hole_margin = hole_diameter / 2 + 3.0
    junction_x = 0.0

    def in_channel(e):
        bb = e.bounding_box()
        return bb.min.X >= channel_x_lo - 1e-6 and bb.max.X <= channel_x_hi + 1e-6 and bb.min.Z >= base_thickness - 1e-6

    def near_hole(e):
        bb = e.bounding_box()
        cx = (bb.min.X + bb.max.X) / 2
        cy = (bb.min.Y + bb.max.Y) / 2
        return abs(cx - hole_center_x) < hole_margin and abs(cy - hole_center_y) < hole_margin

    def on_junction(e):
        bb = e.bounding_box()
        return abs(bb.min.X - junction_x) < 1e-6 and abs(bb.max.X - junction_x) < 1e-6

    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed + 1e-6
        and e not in concave
        and not in_channel(e)
        and not near_hole(e)
        and not on_junction(e)
    )
    return polish(body, keep, 1.0)
