from nurb import *


@part
def cable_clip(bundle_diameter=8.0):
    """Screw-down clip for a cable bundle.

    bundle_diameter: diameter of the cable bundle held by the channel
    """
    channel_clearance = 0.4
    channel_width = bundle_diameter + channel_clearance
    wall_thickness = 2.4
    base_thickness = 3.0
    clip_length = 12.0
    tab_length = 10.0
    mounting_hole_diameter = 4.2

    channel_outer_width = channel_width + 2.0 * wall_thickness
    overall_height = base_thickness + bundle_diameter

    base = Pos(0, 0, base_thickness / 2.0) * Box(
        channel_outer_width, clip_length, base_thickness
    )
    left_wall = Pos(
        -channel_outer_width / 2.0 + wall_thickness / 2.0,
        0,
        base_thickness + bundle_diameter / 2.0,
    ) * Box(
        wall_thickness, clip_length, bundle_diameter
    )
    right_wall = Pos(
        channel_outer_width / 2.0 - wall_thickness / 2.0,
        0,
        base_thickness + bundle_diameter / 2.0,
    ) * Box(
        wall_thickness, clip_length, bundle_diameter
    )
    tab = Pos(channel_outer_width / 2.0 + tab_length / 2.0, 0, base_thickness / 2.0) * Box(
        tab_length, clip_length, base_thickness
    )
    body = base + left_wall + right_wall + tab

    hole = Pos(channel_outer_width / 2.0 + tab_length / 2.0, 0, base_thickness / 2.0) * Cylinder(
        mounting_hole_diameter / 2.0, base_thickness
    )
    return body - hole
