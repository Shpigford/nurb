from nurb import *


@part
def cable_clip(bundle_diameter: float = measured("bundle_diameter"), draft=False):
    """Screw-down clip for an 8 mm cable bundle.

    bundle_diameter: diameter of the cable bundle held in the open channel
    """
    clearance = 0.4
    channel_width = bundle_diameter + clearance
    channel_depth = bundle_diameter
    wall_thickness = 2.4
    base_thickness = 3.0
    tab_length = 10.0
    part_length = 12.0
    screw_hole_width = 4.2

    outside_channel_width = channel_width + 2 * wall_thickness
    total_width = tab_length + outside_channel_width
    total_height = base_thickness + channel_depth

    tab = Box(
        tab_length,
        part_length,
        base_thickness,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    floor = Pos(tab_length + wall_thickness, 0, 0) * Box(
        channel_width,
        part_length,
        base_thickness,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    left_wall = Pos(tab_length, 0, 0) * Box(
        wall_thickness,
        part_length,
        total_height,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    right_wall = Pos(tab_length + wall_thickness + channel_width, 0, 0) * Box(
        wall_thickness,
        part_length,
        total_height,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )

    body = tab + floor + left_wall + right_wall
    screw_hole = Pos(tab_length / 2, 0, base_thickness / 2) * Cylinder(
        radius=screw_hole_width / 2,
        height=base_thickness + 0.2,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    body = body - screw_hole

    if draft:
        return body
    return body
