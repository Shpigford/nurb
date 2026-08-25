from nurb import *


@part
def cable_clip(bundle_diameter: float = measured("bundle_diameter"), draft=False):
    """Screw-down open cable-bundle clip.

    bundle_diameter: measured width of the cable bundle held in the channel.
    """
    channel_clearance = 0.4
    channel_width = bundle_diameter + channel_clearance
    wall_thickness = 2.4
    base_thickness = 3.0
    part_length = 12.0
    tab_length = 10.0
    screw_hole_diameter = 4.2

    # The U-shaped clip occupies x=0 through its outside right wall.  The tab
    # is grounded to the same bottom face and extends from the left wall.
    clip_width = wall_thickness + channel_width + wall_thickness
    outer = Box(clip_width, part_length, base_thickness + bundle_diameter,
                align=(Align.MIN, Align.MIN, Align.MIN))
    channel = Box(channel_width, part_length, bundle_diameter,
                  align=(Align.MIN, Align.MIN, Align.MIN)).translate(
                      (wall_thickness, 0, base_thickness)
                  )
    clip = outer - channel

    tab = Box(tab_length, part_length, base_thickness,
              align=(Align.MAX, Align.MIN, Align.MIN))
    mounting_hole = Cylinder(screw_hole_diameter / 2, base_thickness,
                             align=(Align.CENTER, Align.CENTER, Align.MIN)).translate(
                                 (-tab_length / 2, part_length / 2, 0)
                             )
    return (clip + tab) - mounting_hole
