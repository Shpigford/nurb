from nurb import *


@part
def cable_clip(bundle_diameter=measured("bundle_diameter"), draft=False):
    """A screw-down, open-top cable-bundle clip.

    bundle_diameter: measured diameter of the cable bundle held in the channel.
    """
    channel_clearance = 0.4
    channel_wall_thickness = 2.4
    base_thickness = 3.0
    part_length = 12.0
    mounting_tab_length = 10.0
    screw_hole_diameter = 4.2

    channel_width = bundle_diameter + channel_clearance
    outer_width = channel_width + 2 * channel_wall_thickness
    clip_height = base_thickness + bundle_diameter

    channel_block = Box(
        outer_width,
        part_length,
        clip_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    mounting_tab = Pos(-mounting_tab_length, 0, 0) * Box(
        mounting_tab_length,
        part_length,
        base_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    channel = Pos(channel_wall_thickness, 0, base_thickness) * Box(
        channel_width,
        part_length,
        bundle_diameter,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    screw_hole = Pos(-mounting_tab_length / 2, part_length / 2, 0) * Cylinder(
        screw_hole_diameter / 2,
        base_thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    return (channel_block + mounting_tab) - channel - screw_hole
