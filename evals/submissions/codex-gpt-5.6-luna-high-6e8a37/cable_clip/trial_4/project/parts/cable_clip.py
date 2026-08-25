from nurb import *


@part
def cable_clip(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Screw-down clip for one cable bundle.

    bundle_diameter: diameter of the cable bundle held by the channel
    """
    channel_width = bundle_diameter + 0.4
    wall_thickness = 2.4
    channel_outer_width = channel_width + 2.0 * wall_thickness
    base_thickness = 3.0
    channel_depth = bundle_diameter
    length = 12.0
    tab_length = 10.0
    overall_width = channel_outer_width + tab_length
    hole_diameter = 4.2

    # The channel occupies the left side of the overall footprint.  Keeping the
    # whole base in one box gives the cable a single, uninterrupted flat floor.
    base = Pos(0, 0, base_thickness / 2.0) * Box(
        overall_width, length, base_thickness
    )
    wall_z = base_thickness + channel_depth / 2.0
    left_wall_x = -overall_width / 2.0 + wall_thickness / 2.0
    right_wall_x = -overall_width / 2.0 + channel_outer_width - wall_thickness / 2.0
    left_wall = Pos(left_wall_x, 0, wall_z) * Box(
        wall_thickness, length, channel_depth
    )
    right_wall = Pos(right_wall_x, 0, wall_z) * Box(
        wall_thickness, length, channel_depth
    )
    body = base + left_wall + right_wall

    tab_center_x = -overall_width / 2.0 + channel_outer_width + tab_length / 2.0
    mounting_hole = Pos(tab_center_x, 0, base_thickness / 2.0) * Cylinder(
        hole_diameter / 2.0, base_thickness
    )
    return body - mounting_hole
