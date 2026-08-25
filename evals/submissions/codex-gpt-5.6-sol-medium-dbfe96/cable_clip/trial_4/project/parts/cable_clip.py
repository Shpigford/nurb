from nurb import *


@part
def cable_clip(bundle_diameter: float = 8.0):
    """A screw-down clip for a cable bundle running along Y.

    bundle_diameter: measured width of the cable bundle
    """
    clearance = 0.4
    wall_thickness = 2.4
    base_thickness = 3.0
    part_length = 12.0
    tab_length = 10.0
    screw_hole_width = 4.2

    channel_width = bundle_diameter + clearance
    channel_depth = bundle_diameter
    channel_outer_width = channel_width + 2.0 * wall_thickness
    overall_height = base_thickness + channel_depth

    base = Box(channel_outer_width, part_length, base_thickness).translate(
        (0, 0, base_thickness / 2.0)
    )
    wall_center = channel_width / 2.0 + wall_thickness / 2.0
    left_wall = Box(wall_thickness, part_length, overall_height).translate(
        (-wall_center, 0, overall_height / 2.0)
    )
    right_wall = Box(wall_thickness, part_length, overall_height).translate(
        (wall_center, 0, overall_height / 2.0)
    )

    tab = Box(tab_length, part_length, base_thickness).translate(
        (
            channel_outer_width / 2.0 + tab_length / 2.0,
            0,
            base_thickness / 2.0,
        )
    )
    screw_hole = Cylinder(screw_hole_width / 2.0, base_thickness).translate(
        (
            channel_outer_width / 2.0 + tab_length / 2.0,
            0,
            base_thickness / 2.0,
        )
    )

    return base + left_wall + right_wall + tab - screw_hole
