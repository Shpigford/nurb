from nurb import *


@part
def cable_clip(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Screw-down clip for a cable bundle running along Y.

    bundle_diameter: diameter of the cable bundle held by the channel
    """
    channel_clear_width = bundle_diameter + 0.4
    wall_thickness = 2.4
    base_thickness = 3.0
    channel_depth = bundle_diameter
    part_length = 12.0
    tab_length = 10.0
    channel_outer_width = channel_clear_width + 2.0 * wall_thickness

    base = Box(
        channel_outer_width,
        part_length,
        base_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    left_wall = Pos(0, 0, base_thickness) * Box(
        wall_thickness,
        part_length,
        channel_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    right_wall = Pos(channel_outer_width - wall_thickness, 0, base_thickness) * Box(
        wall_thickness,
        part_length,
        channel_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    tab = Pos(-tab_length, 0, 0) * Box(
        tab_length,
        part_length,
        base_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )

    body = base + left_wall + right_wall + tab
    mounting_hole = Pos(-tab_length / 2.0, part_length / 2.0, 0) * Cylinder(
        2.1,
        base_thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return body - mounting_hole
