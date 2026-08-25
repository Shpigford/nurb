from nurb import *


@part
def cable_clip(bundle_diameter=measured("bundle_diameter")):
    """Screw-down clip for a cable bundle running along the Y axis.

    bundle_diameter: measured width of the cable bundle and channel depth
    """
    channel_clearance = 0.4
    channel_width = bundle_diameter + channel_clearance
    channel_depth = bundle_diameter
    wall_thickness = 2.4
    base_thickness = 3.0
    part_length = 12.0
    tab_length = 10.0
    screw_hole_width = 4.2

    channel_outer_width = channel_width + 2.0 * wall_thickness
    overall_width = channel_outer_width + tab_length

    base = Box(
        overall_width,
        part_length,
        base_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )

    left_wall = Box(
        wall_thickness,
        part_length,
        channel_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    ).moved(Pos(0.0, 0.0, base_thickness))

    right_wall = Box(
        wall_thickness,
        part_length,
        channel_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    ).moved(Pos(wall_thickness + channel_width, 0.0, base_thickness))

    screw_hole = Cylinder(
        screw_hole_width / 2.0,
        base_thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).moved(
        Pos(
            channel_outer_width + tab_length / 2.0,
            part_length / 2.0,
            0.0,
        )
    )

    return base + left_wall + right_wall - screw_hole
