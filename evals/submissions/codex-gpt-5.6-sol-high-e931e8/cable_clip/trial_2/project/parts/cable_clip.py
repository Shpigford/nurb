from nurb import *


@part
def cable_clip(bundle_diameter=measured("bundle_diameter")):
    """A screw-down, open-top clip for a cable bundle running along Y.

    bundle_diameter: measured width of the cable bundle held by the channel
    """
    channel_clearance = 0.4
    channel_width = bundle_diameter + channel_clearance
    channel_depth = bundle_diameter
    wall_thickness = 2.4
    base_thickness = 3.0
    part_length = 12.0
    tab_length = 10.0
    screw_hole_width = 4.2

    outer_width = channel_width + 2.0 * wall_thickness

    base = Box(
        outer_width,
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
    right_wall = Pos(wall_thickness + channel_width, 0, base_thickness) * Box(
        wall_thickness,
        part_length,
        channel_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    mounting_tab = Pos(outer_width, 0, 0) * Box(
        tab_length,
        part_length,
        base_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )

    body = base + left_wall + right_wall + mounting_tab

    screw_hole = Pos(
        outer_width + tab_length / 2.0,
        part_length / 2.0,
        0,
    ) * Cylinder(
        screw_hole_width / 2.0,
        base_thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    return body - screw_hole
