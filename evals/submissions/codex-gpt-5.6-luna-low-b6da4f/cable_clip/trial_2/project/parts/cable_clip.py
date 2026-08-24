from nurb import *


@part
def cable_clip(bundle_diameter: float = measured("bundle_diameter")):
    """Screw-down open cable clip.

    bundle_diameter: diameter of the cable bundle held by the channel
    """
    channel_width = bundle_diameter + 0.4
    wall_thickness = 2.4
    base_thickness = 3.0
    length = 12.0
    tab_length = 10.0
    hole_diameter = 4.2

    outer_width = tab_length + wall_thickness + channel_width + wall_thickness
    base = Pos(0, 0, base_thickness / 2) * Box(outer_width, length, base_thickness)
    x_min = -outer_width / 2
    left_wall = Pos(x_min + tab_length + wall_thickness / 2, 0, base_thickness + bundle_diameter / 2) * Box(
        wall_thickness, length, bundle_diameter
    )
    right_wall = Pos(x_min + tab_length + wall_thickness + channel_width + wall_thickness / 2, 0, base_thickness + bundle_diameter / 2) * Box(
        wall_thickness, length, bundle_diameter
    )
    body = base + left_wall + right_wall
    mounting_hole = Pos(x_min + tab_length / 2, 0, 0) * Cylinder(
        hole_diameter / 2, base_thickness
    )
    return body - mounting_hole
