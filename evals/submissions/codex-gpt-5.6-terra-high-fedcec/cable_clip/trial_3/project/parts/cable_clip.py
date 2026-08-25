from nurb import *


@part
def cable_clip(bundle_diameter=measured("bundle_diameter"), draft=False):
    """A screw-down, open-top cable-bundle clip.

    bundle_diameter: measured diameter of the cable bundle held in the channel.
    """
    channel_width = bundle_diameter + 0.4
    channel_depth = bundle_diameter
    wall_thickness = 2.4
    base_thickness = 3.0
    tab_length = 10.0
    part_length = 12.0

    # The base is also the mounting tab. Explicit coordinates preserve the full,
    # square-cornered channel for every permitted bundle size.
    outer_width = tab_length + channel_width + 2.0 * wall_thickness
    base = Box(
        outer_width,
        part_length,
        base_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    near_wall = Box(
        wall_thickness,
        part_length,
        channel_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    ).translate((tab_length, 0.0, base_thickness))
    far_wall = Box(
        wall_thickness,
        part_length,
        channel_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    ).translate((tab_length + wall_thickness + channel_width, 0.0, base_thickness))

    body = base.fuse(near_wall).fuse(far_wall)
    mounting_hole = Cylinder(
        2.1,
        base_thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).translate((tab_length / 2.0, part_length / 2.0, 0.0))
    return body.cut(mounting_hole)
