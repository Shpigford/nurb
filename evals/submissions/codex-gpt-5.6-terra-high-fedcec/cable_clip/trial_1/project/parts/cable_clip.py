from nurb import *


@part
def cable_clip(bundle_diameter: float = 8.0):
    """A screw-down, open-top clip for one cable bundle.

    bundle_diameter: measured width of the cable bundle held in the channel.
    """
    channel_clearance = 0.4
    channel_width = bundle_diameter + channel_clearance
    channel_depth = bundle_diameter
    wall_thickness = 2.4
    base_thickness = 3.0
    part_length = 12.0
    tab_length = 10.0
    screw_hole_diameter = 4.2

    # The channel and its two walls occupy the right-hand portion of the base;
    # the remaining 10 mm is the mounting tab. Nurb boxes are centered, so the
    # walls are raised by half their combined height to sit squarely on the base.
    channel_outer_width = channel_width + 2 * wall_thickness
    overall_width = tab_length + channel_outer_width
    base = Box(overall_width, part_length, base_thickness)
    wall_center_z = (base_thickness + channel_depth) / 2

    left_wall = Box(wall_thickness, part_length, channel_depth).translate(
        (-overall_width / 2 + tab_length + wall_thickness / 2, 0, wall_center_z)
    )
    right_wall = Box(wall_thickness, part_length, channel_depth).translate(
        (overall_width / 2 - wall_thickness / 2, 0, wall_center_z)
    )

    # The tab runs from the base's left end to the outside of the left wall.
    screw_hole = Cylinder(screw_hole_diameter / 2, base_thickness).translate(
        (-overall_width / 2 + tab_length / 2, 0, 0)
    )
    return base + left_wall + right_wall - screw_hole
