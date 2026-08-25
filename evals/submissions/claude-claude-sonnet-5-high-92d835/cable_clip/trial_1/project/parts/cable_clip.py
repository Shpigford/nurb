from nurb import *


@part
def cable_clip(
    bundle_diameter=8.0,
    wall_thickness=2.4,
    base_thickness=3.0,
    part_length=12.0,
    tab_length=10.0,
    tab_thickness=3.0,
    hole_diameter=4.2,
    draft=False,
):
    """
    bundle_diameter: the cable bundle's measured diameter, sets the channel's inner size
    wall_thickness: thickness of the two walls either side of the channel
    base_thickness: solid material under the channel floor
    part_length: length of the clip along the cable
    tab_length: how far the mounting tab reaches out past the wall
    tab_thickness: thickness of the mounting tab
    hole_diameter: diameter of the tab's screw through-hole
    """
    channel_width = bundle_diameter + 0.4
    channel_depth = bundle_diameter
    block_width = channel_width + 2 * wall_thickness
    block_height = base_thickness + channel_depth

    body = Box(
        block_width, part_length, block_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    channel_cut = Box(
        channel_width, part_length, channel_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    channel_cut = Pos(wall_thickness, 0, base_thickness) * channel_cut
    body = body - channel_cut

    tab = Box(
        tab_length, part_length, tab_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    tab = Pos(block_width, 0, 0) * tab
    hole = Cylinder(
        hole_diameter / 2, tab_thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    hole = Pos(block_width + tab_length / 2, part_length / 2, 0) * hole
    tab = tab - hole

    body = body + tab

    if draft:
        return body

    bed = body.bounding_box().min.Z
    concave = concave_edges(body)
    channel_x_min = wall_thickness
    channel_x_max = wall_thickness + channel_width

    def in_channel(e):
        bb = e.bounding_box()
        return (
            bb.min.X >= channel_x_min - 1e-6
            and bb.max.X <= channel_x_max + 1e-6
            and bb.max.Z >= base_thickness - 1e-6
        )

    def is_hole_rim(e):
        try:
            r = e.radius
        except Exception:
            return False
        return abs(r - hole_diameter / 2) < 1e-3

    def is_wall_top_end_cap(e):
        bb = e.bounding_box()
        on_top = abs(bb.min.Z - block_height) < 1e-6 and abs(bb.max.Z - block_height) < 1e-6
        at_y_end = abs(bb.min.Y - bb.max.Y) < 1e-6
        in_wall = (bb.max.X <= wall_thickness + 1e-6) or (bb.min.X >= channel_x_max - 1e-6)
        return on_top and at_y_end and in_wall

    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed
        and e not in concave
        and not in_channel(e)
        and not is_hole_rim(e)
        and not is_wall_top_end_cap(e)
    )
    return polish(body, keep, 1.0)
