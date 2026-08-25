from nurb import *


@part
def cable_clip(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Screw-down cable clip.

    bundle_diameter: diameter of the cable bundle held by the channel
    """
    channel_width = bundle_diameter + 0.4
    wall_thickness = 2.4
    base_thickness = 3.0
    channel_depth = bundle_diameter
    length = 12.0
    tab_length = 10.0
    hole_diameter = 4.2
    outer_width = channel_width + 2.0 * wall_thickness

    # Use minimum-aligned primitives so the functional faces stay at exact
    # coordinates: tab x=0..10, channel x=10..23.2, and bed z=0.
    tab = Box(tab_length, length, base_thickness,
              align=(Align.MIN, Align.MIN, Align.MIN))
    channel_base = Pos(tab_length, 0, 0) * Box(
        outer_width, length, base_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN)
    )
    left_wall = Pos(tab_length, 0, base_thickness) * Box(
        wall_thickness, length, channel_depth,
        align=(Align.MIN, Align.MIN, Align.MIN)
    )
    right_wall = Pos(tab_length + wall_thickness + channel_width, 0,
                     base_thickness) * Box(
        wall_thickness, length, channel_depth,
        align=(Align.MIN, Align.MIN, Align.MIN)
    )

    body = tab + channel_base + left_wall + right_wall
    mounting_hole = Pos(tab_length / 2.0, length / 2.0, 0) * Cylinder(
        hole_diameter / 2.0, base_thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    return body - mounting_hole
