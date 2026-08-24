from nurb import *


@part
def cable_clip(bundle_diameter=measured("bundle_diameter")):
    """Screw-down cable clip.

    bundle_diameter: diameter of the cable bundle held by the channel
    """
    channel_clear_width = bundle_diameter + 0.4
    wall_thickness = 2.4
    base_thickness = 3.0
    length = 12.0
    channel_depth = bundle_diameter
    outer_width = channel_clear_width + 2.0 * wall_thickness
    tab_length = 10.0
    hole_diameter = 4.2

    base = Box(outer_width, length, base_thickness,
               align=(Align.MIN, Align.MIN, Align.MIN))
    left_wall = Pos(0, 0, base_thickness) * Box(
        wall_thickness, length, channel_depth,
        align=(Align.MIN, Align.MIN, Align.MIN))
    right_wall = Pos(outer_width - wall_thickness, 0, base_thickness) * Box(
        wall_thickness, length, channel_depth,
        align=(Align.MIN, Align.MIN, Align.MIN))
    tab = Pos(outer_width, 0, 0) * Box(
        tab_length, length, base_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN))

    body = base + left_wall + right_wall + tab
    screw_hole = Pos(outer_width + tab_length / 2.0, length / 2.0, 0) * Cylinder(
        hole_diameter / 2.0, base_thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN))
    return body - screw_hole
