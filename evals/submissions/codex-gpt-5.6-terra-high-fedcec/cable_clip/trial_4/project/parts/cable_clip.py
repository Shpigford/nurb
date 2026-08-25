from nurb import *


@part
def cable_clip(bundle_diameter=measured("bundle_diameter"), draft=False):
    """A screw-down, open-top clip for one cable bundle.

    bundle_diameter: measured width of the cable bundle held in the channel.
    """
    channel_clearance = 0.4
    channel_wall_thickness = 2.4
    channel_depth = bundle_diameter
    base_thickness = 3.0
    part_length = 12.0
    mounting_tab_length = 10.0
    mounting_hole_diameter = 4.2

    if bundle_diameter <= 0.0:
        reject("bundle_diameter must be greater than 0 mm", param="bundle_diameter")

    channel_width = bundle_diameter + channel_clearance
    clip_width = channel_width + 2.0 * channel_wall_thickness
    total_height = base_thickness + channel_depth

    # The base continues under the tab; its upper face is the channel's flat floor.
    base = Pos((-mounting_tab_length, 0, 0)) * Box(
        mounting_tab_length + clip_width,
        part_length,
        base_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    left_wall = Pos((0, 0, base_thickness)) * Box(
        channel_wall_thickness,
        part_length,
        channel_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    right_wall = Pos((channel_wall_thickness + channel_width, 0, base_thickness)) * Box(
        channel_wall_thickness,
        part_length,
        channel_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )

    hole = Pos((-mounting_tab_length / 2.0, part_length / 2.0, 0)) * Cylinder(
        mounting_hole_diameter / 2.0,
        base_thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    clip = base + left_wall + right_wall - hole

    # Preserve every channel edge: the mating cavity stays square and dimensionally exact.
    return clip
