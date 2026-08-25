from nurb import *


@part
def cable_clip(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Screw-down, open-top cable-bundle clip.

    bundle_diameter: measured cable bundle diameter; sets the channel depth and width.
    """
    channel_clearance = 0.4
    channel_wall_thickness = 2.4
    base_thickness = 3.0
    part_length = 12.0
    mounting_tab_length = 10.0
    mounting_hole_diameter = 4.2

    if bundle_diameter <= 0.0:
        reject("bundle_diameter must be greater than 0 mm", param="bundle_diameter")

    channel_width = bundle_diameter + channel_clearance
    channel_depth = bundle_diameter
    clip_width = 2.0 * channel_wall_thickness + channel_width

    # The walls meet the base at sharp inside corners, leaving one uninterrupted,
    # flat channel floor across the complete fit-critical width.
    tab = Box(
        mounting_tab_length, part_length, base_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    base = Pos(mounting_tab_length, 0, 0) * Box(
        clip_width, part_length, base_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    near_wall = Pos(mounting_tab_length, 0, base_thickness) * Box(
        channel_wall_thickness, part_length, channel_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    far_wall = Pos(mounting_tab_length + channel_wall_thickness + channel_width, 0, base_thickness) * Box(
        channel_wall_thickness, part_length, channel_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )

    body = tab + base + near_wall + far_wall
    mounting_hole = Pos(mounting_tab_length / 2.0, part_length / 2.0, 0) * Cylinder(
        mounting_hole_diameter / 2.0, base_thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return body - mounting_hole
