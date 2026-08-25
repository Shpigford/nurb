from nurb import *


@part
def cable_clip(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Screw-down clip for a cable bundle running along Y.

    bundle_diameter: diameter of the cable bundle held in the channel
    """
    channel_width = bundle_diameter + 0.4
    wall_thickness = 2.4
    base_thickness = 3.0
    part_length = 12.0
    wall_height = base_thickness + bundle_diameter
    channel_outer_width = channel_width + 2.0 * wall_thickness
    tab_length = 10.0
    hole_diameter = 4.2

    # The channel occupies X=0..channel_outer_width and Y=0..part_length.
    # Keeping these boxes square preserves the full-width, flat channel floor.
    base = Pos(channel_outer_width / 2.0, part_length / 2.0, base_thickness / 2.0) * Box(
        channel_outer_width, part_length, base_thickness
    )
    left_wall = Pos(
        wall_thickness / 2.0, part_length / 2.0,
        (base_thickness + wall_height) / 2.0,
    ) * Box(wall_thickness, part_length, wall_height - base_thickness)
    right_wall = Pos(
        channel_outer_width - wall_thickness / 2.0, part_length / 2.0,
        (base_thickness + wall_height) / 2.0,
    ) * Box(wall_thickness, part_length, wall_height - base_thickness)
    tab = Pos(-tab_length / 2.0, part_length / 2.0, base_thickness / 2.0) * Box(
        tab_length, part_length, base_thickness
    )

    body = base + left_wall + right_wall + tab
    mounting_hole = Pos(-tab_length / 2.0, part_length / 2.0, base_thickness / 2.0) * Cylinder(
        hole_diameter / 2.0, base_thickness
    )
    return body - mounting_hole
