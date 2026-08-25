from nurb import *


@part
def cable_clip(bundle_diameter: float = measured("bundle_diameter"), draft=False):
    """Screw-down clip for a cable bundle.

    bundle_diameter: diameter of the cable bundle held in the channel
    """
    channel_clearance = 0.4
    channel_width = bundle_diameter + channel_clearance
    wall_thickness = 2.4
    base_thickness = 3.0
    length = 12.0
    wall_height = bundle_diameter
    channel_outer_width = channel_width + 2.0 * wall_thickness
    tab_length = 10.0
    hole_diameter = 4.2

    # The channel occupies X=tab_length..23.2, Y=0..12, Z=0..11.
    base = Pos(tab_length, 0, 0) * Box(
        channel_outer_width, length, base_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    left_wall = Pos(tab_length, 0, base_thickness) * Box(
        wall_thickness, length, wall_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    right_wall = Pos(tab_length + wall_thickness + channel_width, 0, base_thickness) * Box(
        wall_thickness, length, wall_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )

    tab = Pos(0, 0, 0) * Box(
        tab_length, length, base_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    screw_hole = Pos(tab_length / 2.0, length / 2.0, 0) * Cylinder(
        hole_diameter / 2.0, base_thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    tab = tab - screw_hole

    return base + left_wall + right_wall + tab
