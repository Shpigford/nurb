from nurb import *


@part
def cable_clip(
    bundle_diameter=measured("bundle_diameter"),
    wall=2.4,
    base_thickness=3.0,
    tab_length=10.0,
    tab_hole_diameter=4.2,
    length=12.0,
    draft=False,
):
    """
    bundle_diameter: diameter of the cable bundle the channel cradles
    wall: thickness of each channel wall
    base_thickness: material under the channel floor and the tab
    tab_length: how far the mounting tab reaches out from the channel
    tab_hole_diameter: diameter of the screw clearance hole in the tab
    length: length of the clip along the cable
    """
    channel_width = bundle_diameter + 0.4
    channel_depth = bundle_diameter
    body_width = channel_width + 2 * wall
    total_width = tab_length + body_width

    channel_x_min = tab_length + wall
    channel_x_max = channel_x_min + channel_width

    base = Box(
        total_width, length, base_thickness, align=(Align.MIN, Align.MIN, Align.MIN)
    )
    left_wall = Box(
        wall, length, channel_depth, align=(Align.MIN, Align.MIN, Align.MIN)
    ).translate((tab_length, 0, base_thickness))
    right_wall = Box(
        wall, length, channel_depth, align=(Align.MIN, Align.MIN, Align.MIN)
    ).translate((channel_x_max, 0, base_thickness))

    hole = Cylinder(
        tab_hole_diameter / 2, base_thickness, align=(Align.CENTER, Align.CENTER, Align.MIN)
    ).translate((tab_length / 2, length / 2, 0))

    body = base + left_wall + right_wall - hole

    if draft:
        return body

    bed = body.bounding_box().min.Z
    body_height = base_thickness + channel_depth
    concave = concave_edges(body)

    def in_channel(e):
        bb = e.bounding_box()
        return bb.min.X >= channel_x_min - 1e-6 and bb.max.X <= channel_x_max + 1e-6

    def on_hole(e):
        return e.geom_type == GeomType.CIRCLE

    def wall_top_end_cap(e):
        bb = e.bounding_box()
        on_top = abs(bb.min.Z - body_height) < 1e-6 and abs(bb.max.Z - body_height) < 1e-6
        at_end = (abs(bb.min.Y) < 1e-6 and abs(bb.max.Y) < 1e-6) or (
            abs(bb.min.Y - length) < 1e-6 and abs(bb.max.Y - length) < 1e-6
        )
        return on_top and at_end and bb.min.Y == bb.max.Y

    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed + 1e-6
        and not in_channel(e)
        and not on_hole(e)
        and not wall_top_end_cap(e)
        and e not in concave
    )
    return polish(body, keep, 1.0)
