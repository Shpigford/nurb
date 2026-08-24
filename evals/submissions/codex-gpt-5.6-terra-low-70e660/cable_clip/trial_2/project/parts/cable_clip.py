from nurb import *


@part
def cable_clip(bundle_diameter=8.0):
    """Screw-down, open-top clip for a cable bundle.

    bundle_diameter: measured diameter of the cable bundle held by the channel.
    """
    clearance = 0.4
    channel_width = bundle_diameter + clearance
    channel_depth = bundle_diameter
    wall_thickness = 2.4
    base_thickness = 3.0
    part_length = 12.0
    tab_length = 10.0
    screw_hole_diameter = 4.2

    channel_outer_width = channel_width + 2 * wall_thickness
    total_width = channel_outer_width + tab_length

    # The base runs under both the channel and mounting tab. The two wall boxes
    # leave a sharp, full-length rectangular channel open at the top.
    base = Box(total_width, part_length, base_thickness)
    left_wall = Box(wall_thickness, part_length, channel_depth).translate(
        (-total_width / 2 + wall_thickness / 2, 0, base_thickness / 2 + channel_depth / 2)
    )
    right_wall = Box(wall_thickness, part_length, channel_depth).translate(
        (-total_width / 2 + wall_thickness + channel_width + wall_thickness / 2,
         0, base_thickness / 2 + channel_depth / 2)
    )
    body = base + left_wall + right_wall

    hole = Cylinder(screw_hole_diameter / 2, base_thickness).translate(
        (-total_width / 2 + channel_outer_width + tab_length / 2, 0, 0)
    )
    return body - hole
