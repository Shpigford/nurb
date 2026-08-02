from nurb import *


@part
def cable_clip(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Screw-down open cable clip.

    bundle_diameter: measured width of the cable bundle the channel holds
    """
    channel_clearance = 0.4
    channel_width = bundle_diameter + channel_clearance
    channel_depth = bundle_diameter
    wall_thickness = 2.4
    base_thickness = 3.0
    tab_length = 10.0
    part_length = 12.0
    screw_hole_width = 4.2

    channel_outer_width = channel_width + 2.0 * wall_thickness
    total_width = tab_length + channel_outer_width
    total_height = base_thickness + channel_depth

    base = Pos(0, 0, base_thickness / 2.0) * Box(
        total_width,
        part_length,
        base_thickness,
    )

    channel_center_x = -total_width / 2.0 + tab_length + channel_outer_width / 2.0
    walls = Pos(channel_center_x, 0, total_height / 2.0) * Box(
        channel_outer_width,
        part_length,
        total_height,
    )

    channel_void = Pos(
        channel_center_x,
        0,
        base_thickness + (channel_depth + 0.2) / 2.0,
    ) * Box(
        channel_width,
        part_length + 0.2,
        channel_depth + 0.2,
    )

    tab_hole_x = -total_width / 2.0 + tab_length / 2.0
    screw_hole = Pos(tab_hole_x, 0, base_thickness / 2.0) * Cylinder(
        screw_hole_width / 2.0,
        base_thickness + 0.4,
    )

    return (base + walls) - channel_void - screw_hole
