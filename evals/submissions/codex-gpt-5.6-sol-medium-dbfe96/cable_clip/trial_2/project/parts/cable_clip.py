from nurb import *


@part
def cable_clip(bundle_diameter=8.0):
    """Screw-down clip for a cable bundle running along Y.

    bundle_diameter: measured width of the cable bundle held by the channel
    """
    channel_width = bundle_diameter + 0.4
    channel_depth = bundle_diameter
    wall_thickness = 2.4
    base_thickness = 3.0
    part_length = 12.0
    tab_length = 10.0
    screw_hole_width = 4.2
    outside_width = channel_width + 2 * wall_thickness

    floor = Box(outside_width, part_length, base_thickness,
                align=(Align.MIN, Align.MIN, Align.MIN))
    left_wall = Box(wall_thickness, part_length, channel_depth,
                    align=(Align.MIN, Align.MIN, Align.MIN)).translate(
                        (0, 0, base_thickness))
    right_wall = Box(wall_thickness, part_length, channel_depth,
                     align=(Align.MIN, Align.MIN, Align.MIN)).translate(
                         (wall_thickness + channel_width, 0, base_thickness))
    tab = Box(tab_length, part_length, base_thickness,
              align=(Align.MIN, Align.MIN, Align.MIN)).translate(
                  (-tab_length, 0, 0))
    screw_hole = Cylinder(screw_hole_width / 2, base_thickness,
                          align=(Align.CENTER, Align.CENTER, Align.MIN)).translate(
                              (-tab_length / 2, part_length / 2, 0))

    return floor + left_wall + right_wall + tab - screw_hole
