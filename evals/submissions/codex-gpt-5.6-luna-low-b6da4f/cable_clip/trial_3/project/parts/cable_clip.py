from nurb import *


@part
def cable_clip(bundle_diameter: float = 8.0):
    """Screw-down open cable clip.

    bundle_diameter: diameter of the cable bundle held by the channel
    """
    channel_width = bundle_diameter + 0.4
    wall = 2.4
    base_thickness = 3.0
    length = 12.0
    wall_height = bundle_diameter
    overall_width = channel_width + 2.0 * wall

    # X layout: mounting tab [-10, 0], left wall [0, 2.4],
    # channel [2.4, 10.8], right wall [10.8, 13.2].
    base = Pos(0, 0, 0) * Box(overall_width, length, base_thickness,
                              align=(Align.MIN, Align.MIN, Align.MIN))
    tab = Pos(-10.0, 0, 0) * Box(10.0, length, base_thickness,
                                  align=(Align.MIN, Align.MIN, Align.MIN))
    left_wall = Pos(0, 0, base_thickness) * Box(wall, length, wall_height,
                                                align=(Align.MIN, Align.MIN, Align.MIN))
    right_wall = Pos(wall + channel_width, 0, base_thickness) * Box(
        wall, length, wall_height, align=(Align.MIN, Align.MIN, Align.MIN)
    )
    clip = base + tab + left_wall + right_wall

    screw_hole = Pos(-5.0, length / 2.0, -1.0) * Cylinder(
        4.2 / 2.0, base_thickness + 2.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    return clip - screw_hole
