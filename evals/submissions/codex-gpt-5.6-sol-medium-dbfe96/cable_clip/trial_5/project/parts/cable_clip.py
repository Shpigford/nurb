from nurb import *


@part
def cable_clip(bundle_diameter=measured("bundle_diameter")):
    """Screw-down clip for a cable bundle running along Y.

    bundle_diameter: measured width of the cable bundle held by the channel
    """
    clearance = 0.4
    wall_thickness = 2.4
    base_thickness = 3.0
    part_length = 12.0
    tab_length = 10.0
    screw_hole_width = 4.2

    channel_width = bundle_diameter + clearance
    channel_depth = bundle_diameter
    body_width = channel_width + 2.0 * wall_thickness
    total_height = base_thickness + channel_depth

    box_align = (Align.MIN, Align.CENTER, Align.MIN)
    base = Box(body_width, part_length, base_thickness, align=box_align)
    left_wall = Pos(0, 0, base_thickness) * Box(
        wall_thickness, part_length, channel_depth, align=box_align
    )
    right_wall = Pos(wall_thickness + channel_width, 0, base_thickness) * Box(
        wall_thickness, part_length, channel_depth, align=box_align
    )
    tab = Pos(body_width, 0, 0) * Box(
        tab_length, part_length, base_thickness, align=box_align
    )

    clip = base + left_wall + right_wall + tab
    hole = Pos(body_width + tab_length / 2.0, 0, 0) * Cylinder(
        screw_hole_width / 2.0,
        base_thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    return clip - hole
