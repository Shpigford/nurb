from nurb import *


@part
def cable_clip(bundle_diameter=measured("bundle_diameter"), draft=False):
    """A screw-down, open-top clip for a cable bundle.

    bundle_diameter: measured width of the cable bundle held in the channel
    """
    channel_width = bundle_diameter + 0.4
    wall_thickness = 2.4
    base_thickness = 3.0
    part_length = 12.0
    tab_length = 10.0
    hole_diameter = 4.2

    # The base and two walls form a square-cornered, full-length U channel.
    clip_width = channel_width + 2.0 * wall_thickness
    base = Box(clip_width, part_length, base_thickness,
               align=(Align.MIN, Align.MIN, Align.MIN))
    left_wall = Box(wall_thickness, part_length, bundle_diameter,
                    align=(Align.MIN, Align.MIN, Align.MIN))
    left_wall = left_wall.moved(Location((0, 0, base_thickness)))
    right_wall = Box(wall_thickness, part_length, bundle_diameter,
                     align=(Align.MIN, Align.MIN, Align.MIN))
    right_wall = right_wall.moved(Location((wall_thickness + channel_width, 0, base_thickness)))

    # The mounting tab is flush to the bed and spans the same length as the clip.
    tab = Box(tab_length, part_length, base_thickness,
              align=(Align.MIN, Align.MIN, Align.MIN))
    tab = tab.moved(Location((clip_width, 0, 0)))
    body = base + left_wall + right_wall + tab

    hole = Cylinder(hole_diameter / 2.0, base_thickness,
                    align=(Align.CENTER, Align.CENTER, Align.MIN))
    hole = hole.moved(Location((clip_width + tab_length / 2.0, part_length / 2.0, 0)))
    return body - hole
