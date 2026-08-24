from nurb import *


@part
def cable_clip(bundle_diameter=measured("bundle_diameter")):
    """A screw-down, open-top clip for a cable bundle.

    bundle_diameter: measured diameter of the cable bundle held in the channel.
    """
    channel_clearance = 0.4
    channel_wall_thickness = 2.4
    base_thickness = 3.0
    part_length = 12.0
    mounting_tab_length = 10.0
    screw_hole_diameter = 4.2

    if bundle_diameter <= 0.0:
        reject("bundle_diameter must be greater than 0 mm", param="bundle_diameter")

    channel_width = bundle_diameter + channel_clearance
    clip_width = channel_width + 2.0 * channel_wall_thickness
    wall_height = bundle_diameter

    # The base includes the mounting tab.  The two additions above it are the
    # channel walls, leaving an unmodified square-cornered channel floor.
    base = Box(
        mounting_tab_length + clip_width,
        part_length,
        base_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    ).translate((-mounting_tab_length, 0.0, 0.0))
    near_wall = Box(
        channel_wall_thickness,
        part_length,
        wall_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    ).translate((0.0, 0.0, base_thickness))
    far_wall = Box(
        channel_wall_thickness,
        part_length,
        wall_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    ).translate((channel_wall_thickness + channel_width, 0.0, base_thickness))

    screw_hole = Cylinder(
        screw_hole_diameter / 2.0,
        base_thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).translate((-mounting_tab_length / 2.0, part_length / 2.0, 0.0))

    return base + near_wall + far_wall - screw_hole
