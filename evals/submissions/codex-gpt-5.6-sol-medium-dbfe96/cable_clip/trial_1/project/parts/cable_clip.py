from nurb import *


@part
def cable_clip(bundle_diameter=measured("bundle_diameter")):
    """A screw-down clip for a cable bundle running along Y.

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

    outside_width = channel_width + 2.0 * wall_thickness

    base = Box(
        outside_width,
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
    ).moved(Pos(outside_width - wall_thickness, 0.0, base_thickness))

    tab = Box(
        tab_length,
        part_length,
        base_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    ).moved(Pos(outside_width, 0.0, 0.0))
    screw_hole = Cylinder(
        screw_hole_width / 2.0,
        base_thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).moved(Pos(outside_width + tab_length / 2.0, part_length / 2.0, 0.0))

    return base + left_wall + right_wall + tab - screw_hole
