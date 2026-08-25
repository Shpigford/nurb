from nurb import *


@part
def cable_clip(bundle_diameter=8.0, draft=False):
    """Screw-down open cable-bundle clip.

    bundle_diameter: measured diameter of the cable bundle held by the channel.
    """
    channel_width = bundle_diameter + 0.4
    channel_depth = bundle_diameter
    wall_thickness = 2.4
    base_thickness = 3.0
    part_length = 12.0
    tab_length = 10.0
    hole_diameter = 4.2

    # The X coordinate is intentionally laid out from the tab's outside edge so the
    # default dimensions are 23.2 x 12.0 x 11.0 mm.
    channel_outer_width = channel_width + 2 * wall_thickness
    total_width = tab_length + channel_outer_width

    base_and_tab = Box(
        total_width, part_length, base_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    left_wall = Box(
        wall_thickness, part_length, channel_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    ).translate((tab_length, 0, base_thickness))
    right_wall = Box(
        wall_thickness, part_length, channel_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    ).translate((tab_length + wall_thickness + channel_width, 0, base_thickness))

    # A through-hole in the flat 3 mm tab; its axis is vertical for printing.
    screw_hole = Cylinder(
        hole_diameter / 2, base_thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).translate((tab_length / 2, part_length / 2, 0))

    return (base_and_tab + left_wall + right_wall) - screw_hole
