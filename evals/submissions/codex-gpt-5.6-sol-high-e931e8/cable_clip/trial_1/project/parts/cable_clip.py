from nurb import *


@part
def cable_clip(bundle_diameter: float = 8.0):
    """Screw-down clip for a cable bundle running along Y.

    bundle_diameter: measured width of the cable bundle and channel depth
    """
    clearance = 0.4
    channel_width = bundle_diameter + clearance
    wall_thickness = 2.4
    base_thickness = 3.0
    part_length = 12.0
    tab_length = 10.0
    screw_hole_width = 4.2

    channel_outer_width = channel_width + 2 * wall_thickness

    # The base and mounting tab are one continuous slab. Center the channel
    # portion on X=0, with the tab extending from its positive-X wall.
    base = Pos(tab_length / 2, 0, base_thickness / 2) * Box(
        channel_outer_width + tab_length,
        part_length,
        base_thickness,
    )

    wall_offset = channel_width / 2 + wall_thickness / 2
    wall_center_z = base_thickness + bundle_diameter / 2
    left_wall = Pos(-wall_offset, 0, wall_center_z) * Box(
        wall_thickness,
        part_length,
        bundle_diameter,
    )
    right_wall = Pos(wall_offset, 0, wall_center_z) * Box(
        wall_thickness,
        part_length,
        bundle_diameter,
    )

    body = base + left_wall + right_wall

    tab_center_x = channel_outer_width / 2 + tab_length / 2
    screw_hole = Pos(tab_center_x, 0, base_thickness / 2) * Cylinder(
        screw_hole_width / 2,
        base_thickness,
    )

    return body - screw_hole
