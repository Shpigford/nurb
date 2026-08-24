from nurb import *


@part
def cable_clip(bundle_diameter: float = measured("bundle_diameter")):
    """A screw-down, open-top clip for a cable bundle.

    bundle_diameter: diameter of the cable bundle held by the channel
    """
    channel_width = bundle_diameter + 0.4
    wall_thickness = 2.4
    base_thickness = 3.0
    part_length = 12.0
    tab_length = 10.0
    hole_diameter = 4.2

    # The floor, walls, and mounting tab are deliberately separate simple
    # solids: this leaves the channel's floor and inside corners perfectly
    # square, while the overall X extent derives from the cable size.
    base_width = wall_thickness + channel_width + wall_thickness
    base = Box(base_width, part_length, base_thickness,
               align=(Align.MIN, Align.MIN, Align.MIN))
    left_wall = Box(wall_thickness, part_length, bundle_diameter,
                    align=(Align.MIN, Align.MIN, Align.MIN)).moved(Location((0, 0, base_thickness)))
    right_wall = Box(wall_thickness, part_length, bundle_diameter,
                     align=(Align.MIN, Align.MIN, Align.MIN)).moved(Location((wall_thickness + channel_width, 0, base_thickness)))
    tab = Box(tab_length, part_length, base_thickness,
              align=(Align.MIN, Align.MIN, Align.MIN)).moved(Location((-tab_length, 0, 0)))

    clip = base.fuse(left_wall).fuse(right_wall).fuse(tab)
    screw_hole = Cylinder(hole_diameter / 2, base_thickness,
                          align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((-tab_length / 2, part_length / 2, 0)))
    return clip.cut(screw_hole)
