from nurb import *


@part
def cable_clip(bundle_diameter=8.0):
    """Screw-down, open-top clip for a round cable bundle.

    bundle_diameter: measured diameter of the cable bundle held in the channel
    """
    channel_width = bundle_diameter + 0.4
    wall_thickness = 2.4
    base_thickness = 3.0
    part_length = 12.0
    channel_depth = bundle_diameter
    tab_length = 10.0
    hole_diameter = 4.2

    channel_outer_width = channel_width + 2 * wall_thickness
    body = Box(channel_outer_width, part_length, base_thickness + channel_depth)
    tab = Box(tab_length, part_length, base_thickness).translate(
        (-0.5 * (channel_outer_width + tab_length), 0, -0.5 * channel_depth)
    )
    channel = Box(channel_width, part_length, channel_depth).translate(
        (0, 0, 0.5 * base_thickness)
    )
    hole = Cylinder(hole_diameter / 2, base_thickness).translate(
        (-0.5 * (channel_outer_width + tab_length) + tab_length / 2, 0, -0.5 * channel_depth)
    )
    return (body + tab - channel - hole).clean()
