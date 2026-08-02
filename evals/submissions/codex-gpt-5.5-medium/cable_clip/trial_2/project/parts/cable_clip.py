from nurb import *


@part
def cable_clip(bundle_diameter=measured("bundle_diameter"), draft=False):
    """
    bundle_diameter: measured width across the cable bundle the channel holds
    """
    channel_clearance = 0.4
    channel_inner_width = bundle_diameter + channel_clearance
    channel_depth = bundle_diameter
    wall_thickness = 2.4
    base_thickness = 3.0
    part_length = 12.0
    tab_length = 10.0
    tab_thickness = 3.0
    screw_hole_diameter = 4.2

    channel_outer_width = channel_inner_width + 2 * wall_thickness
    total_height = base_thickness + channel_depth

    clip = Pos(channel_outer_width / 2, part_length / 2, total_height / 2) * Box(
        channel_outer_width, part_length, total_height
    )
    tab = Pos(
        channel_outer_width + tab_length / 2,
        part_length / 2,
        tab_thickness / 2,
    ) * Box(tab_length, part_length, tab_thickness)

    channel_void = Pos(
        wall_thickness + channel_inner_width / 2,
        part_length / 2,
        base_thickness + channel_depth / 2,
    ) * Box(channel_inner_width, part_length + 0.2, channel_depth)
    screw_hole = Pos(
        channel_outer_width + tab_length / 2,
        part_length / 2,
        tab_thickness / 2,
    ) * Cylinder(screw_hole_diameter / 2, tab_thickness + 0.4)

    return clip + tab - channel_void - screw_hole
