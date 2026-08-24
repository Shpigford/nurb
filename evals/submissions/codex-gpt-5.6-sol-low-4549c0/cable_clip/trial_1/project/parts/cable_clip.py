from build123d import Align, Box, Cylinder, Pos
from nurb import part


@part
def cable_clip(bundle_diameter: float = 8.0):
    """Screw-down clip for a cable bundle running along Y.

    bundle_diameter: measured diameter of the cable bundle
    """
    clearance = 0.4
    channel_width = bundle_diameter + clearance
    channel_depth = bundle_diameter
    wall_thickness = 2.4
    base_thickness = 3.0
    part_length = 12.0
    tab_length = 10.0
    screw_hole_width = 4.2

    channel_outer_width = channel_width + 2.0 * wall_thickness
    overall_width = channel_outer_width + tab_length

    min_corner = (Align.MIN, Align.MIN, Align.MIN)
    base_and_tab = Box(
        overall_width, part_length, base_thickness, align=min_corner
    )
    left_wall = Pos(0, 0, base_thickness) * Box(
        wall_thickness, part_length, channel_depth, align=min_corner
    )
    right_wall = Pos(
        wall_thickness + channel_width, 0, base_thickness
    ) * Box(wall_thickness, part_length, channel_depth, align=min_corner)

    body = base_and_tab + left_wall + right_wall

    hole = Pos(
        channel_outer_width + tab_length / 2.0,
        part_length / 2.0,
        0,
    ) * Cylinder(
        screw_hole_width / 2.0,
        base_thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    return body - hole
