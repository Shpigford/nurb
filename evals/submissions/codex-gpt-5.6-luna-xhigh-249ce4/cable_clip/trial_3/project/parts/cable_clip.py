from nurb import *


@part
def cable_clip(bundle_diameter: float = measured("bundle_diameter")):
    """Screw-down clip for a cable bundle.

    bundle_diameter: diameter of the cable bundle held by the channel
    """
    channel_width = bundle_diameter + 0.4
    wall_thickness = 2.4
    base_thickness = 3.0
    part_length = 12.0
    outer_width = channel_width + 2.0 * wall_thickness
    channel_height = bundle_diameter
    tab_length = 10.0

    base = Box(
        outer_width,
        part_length,
        base_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    left_wall = Pos(0, 0, base_thickness) * Box(
        wall_thickness,
        part_length,
        channel_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    right_wall = Pos(outer_width - wall_thickness, 0, base_thickness) * Box(
        wall_thickness,
        part_length,
        channel_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    mounting_tab = Box(
        tab_length,
        part_length,
        base_thickness,
        align=(Align.MAX, Align.MIN, Align.MIN),
    )
    mounting_hole = Pos(-tab_length / 2.0, part_length / 2.0, -1.0) * Cylinder(
        4.2 / 2.0,
        base_thickness + 2.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    return base.fuse(left_wall, right_wall, mounting_tab).cut(mounting_hole)
