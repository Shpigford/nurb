from nurb import *


@part
def cable_clip(bundle_diameter=measured("bundle_diameter"), draft=False):
    """A screw-down, open-top clip for a cable bundle.

    bundle_diameter: measured diameter of the cable bundle held in the channel.
    """
    channel_clearance = 0.4
    channel_width = bundle_diameter + channel_clearance
    channel_depth = bundle_diameter
    wall_thickness = 2.4
    base_thickness = 3.0
    part_length = 12.0
    tab_length = 10.0
    screw_hole_diameter = 4.2

    if bundle_diameter <= 0.0:
        reject("bundle_diameter must be greater than 0 mm", param="bundle_diameter")

    clip_width = wall_thickness + channel_width + wall_thickness
    overall_width = tab_length + clip_width

    # The base is continuous with the tab.  The two walls leave the channel fully
    # open above its flat floor; no channel faces are polished or rounded.
    base = Box(overall_width, part_length, base_thickness,
               align=(Align.MIN, Align.MIN, Align.MIN))
    left_wall = Box(wall_thickness, part_length, channel_depth,
                    align=(Align.MIN, Align.MIN, Align.MIN)).translate((tab_length, 0, base_thickness))
    right_wall = Box(wall_thickness, part_length, channel_depth,
                     align=(Align.MIN, Align.MIN, Align.MIN)).translate(
                         (tab_length + wall_thickness + channel_width, 0, base_thickness)
                     )
    body = base.fuse(left_wall).fuse(right_wall)

    screw_hole = Cylinder(screw_hole_diameter / 2.0, base_thickness,
                         align=(Align.CENTER, Align.CENTER, Align.MIN)).translate(
                             (tab_length / 2.0, part_length / 2.0, 0)
                         )
    return body.cut(screw_hole)
