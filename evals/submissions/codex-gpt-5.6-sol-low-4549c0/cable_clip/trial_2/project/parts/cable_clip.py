from nurb import *


@part
def cable_clip(bundle_diameter=measured("bundle_diameter")):
    """A screw-down clip for a cable bundle running along Y.

    bundle_diameter: measured width of the cable bundle held by the channel
    """
    channel_clearance = 0.4
    wall_thickness = 2.4
    base_thickness = 3.0
    part_length = 12.0
    tab_length = 10.0
    screw_hole_width = 4.2

    channel_width = bundle_diameter + channel_clearance
    channel_depth = bundle_diameter
    clip_width = channel_width + 2.0 * wall_thickness
    total_height = base_thickness + channel_depth

    base = Box(
        clip_width,
        part_length,
        base_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    left_wall = Box(
        wall_thickness,
        part_length,
        channel_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    ).translate((0.0, 0.0, base_thickness))
    right_wall = Box(
        wall_thickness,
        part_length,
        channel_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    ).translate((clip_width - wall_thickness, 0.0, base_thickness))

    tab = Box(
        tab_length,
        part_length,
        base_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    ).translate((clip_width, 0.0, 0.0))
    screw_hole = Cylinder(
        screw_hole_width / 2.0,
        base_thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).translate((clip_width + tab_length / 2.0, part_length / 2.0, 0.0))

    clip = base + left_wall + right_wall + tab
    return clip - screw_hole
