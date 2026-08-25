from nurb import *


@part
def cable_clip(bundle_diameter: float = 8.0):
    """Screw-down open cable clip.

    bundle_diameter: measured diameter of the cable bundle the channel holds
    """
    channel_width = bundle_diameter + 0.4
    channel_depth = bundle_diameter
    wall_thickness = 2.4
    base_thickness = 3.0
    part_length = 12.0
    tab_length = 10.0
    hole_diameter = 4.2

    outer_width = channel_width + 2 * wall_thickness

    # Separate rectangular solids preserve a square-cornered, open channel.
    base = Box(outer_width, part_length, base_thickness)
    left_wall = Box(wall_thickness, part_length, channel_depth).move(
        Location((-(outer_width - wall_thickness) / 2, 0, (base_thickness + channel_depth) / 2))
    )
    right_wall = Box(wall_thickness, part_length, channel_depth).move(
        Location(((outer_width - wall_thickness) / 2, 0, (base_thickness + channel_depth) / 2))
    )
    tab = Box(tab_length, part_length, base_thickness).move(
        Location((-(outer_width + tab_length) / 2, 0, 0))
    )

    body = base.fuse(left_wall).fuse(right_wall).fuse(tab)
    screw_hole = Cylinder(hole_diameter / 2, base_thickness).move(
        Location((-(outer_width + tab_length) / 2, 0, 0))
    )
    return body.cut(screw_hole)
