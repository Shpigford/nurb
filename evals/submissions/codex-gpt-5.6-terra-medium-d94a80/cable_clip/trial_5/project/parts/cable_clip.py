from nurb import *


@part
def cable_clip(bundle_diameter: float = 8.0):
    """A screw-down, open-top cable-bundle clip.

    bundle_diameter: diameter of the cable bundle held in the channel
    """
    channel_width = bundle_diameter + 0.4
    wall_thickness = 2.4
    base_thickness = 3.0
    channel_depth = bundle_diameter
    length = 12.0
    tab_length = 10.0
    clip_width = channel_width + 2 * wall_thickness

    base = Box(clip_width + tab_length, length, base_thickness, align=(Align.MIN, Align.MIN, Align.MIN))
    left_wall = Box(wall_thickness, length, channel_depth, align=(Align.MIN, Align.MIN, Align.MIN)).translate((0, 0, base_thickness))
    right_wall = Box(wall_thickness, length, channel_depth, align=(Align.MIN, Align.MIN, Align.MIN)).translate(
        (wall_thickness + channel_width, 0, base_thickness)
    )
    screw_hole = Cylinder(2.1, base_thickness, align=(Align.CENTER, Align.CENTER, Align.MIN)).translate(
        (clip_width + tab_length / 2, length / 2, 0)
    )
    return (base + left_wall + right_wall) - screw_hole
