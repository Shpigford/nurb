from nurb import *


@part
def cable_clip(bundle_diameter: float = 8.0):
    """Screw-down clip for a cable bundle running along Y.

    bundle_diameter: measured width and channel depth for the cable bundle
    """
    clearance = 0.4
    wall_thickness = 2.4
    base_thickness = 3.0
    part_length = 12.0
    tab_length = 10.0
    screw_hole_width = 4.2

    channel_width = bundle_diameter + clearance
    outside_width = channel_width + 2.0 * wall_thickness

    base_z = base_thickness / 2.0
    base = Box(outside_width, part_length, base_thickness).translate((0.0, 0.0, base_z))

    wall_x = channel_width / 2.0 + wall_thickness / 2.0
    wall_z = base_thickness + bundle_diameter / 2.0
    left_wall = Box(wall_thickness, part_length, bundle_diameter).translate(
        (-wall_x, 0.0, wall_z)
    )
    right_wall = Box(wall_thickness, part_length, bundle_diameter).translate(
        (wall_x, 0.0, wall_z)
    )

    tab_x = outside_width / 2.0 + tab_length / 2.0
    tab = Box(tab_length, part_length, base_thickness).translate((tab_x, 0.0, base_z))
    screw_hole = Cylinder(screw_hole_width / 2.0, base_thickness).translate(
        (tab_x, 0.0, base_z)
    )

    return base + left_wall + right_wall + tab - screw_hole
