from nurb import *


@part
def bundle_holder(bundle_diameter=8.0, length=16.0, wall_thickness=3.0):
    """A compact wall clip for a horizontal cable bundle.

    bundle_diameter: outside diameter of the cable bundle being retained
    length: length of the clip along the cable run
    wall_thickness: thickness of the wall-mounting back plate
    """
    # The free channel is nominal bundle size plus 0.4 mm diametral clearance.
    clear_diameter = bundle_diameter + 0.4
    radius = clear_diameter / 2
    base_thickness = wall_thickness
    back_height = clear_diameter + 8.6
    channel_center_x = wall_thickness + radius + 0.2

    # X is away from the wall, Y follows the cable, and Z is up from the bed.
    back = Box(wall_thickness, length, back_height,
               align=(Align.MIN, Align.MIN, Align.MIN))
    floor = Box(channel_center_x + radius - wall_thickness, length, base_thickness,
                align=(Align.MIN, Align.MIN, Align.MIN)).translate((wall_thickness, 0, 0))

    # A low outer toe catches both downward and outward cable motion while
    # keeping the channel open along Y for threading the bundle through.
    toe_x = channel_center_x + radius - 0.2
    toe = Box(2.4, length, base_thickness + 2.0,
              align=(Align.MIN, Align.MIN, Align.MIN)).translate((toe_x, 0, 0))
    holder = back + floor + toe

    # M4 clearance bore: its outer face is a solid 3 mm seat for the pan head.
    screw_z = back_height - 4.0
    screw = Cylinder(2.2, wall_thickness + 0.4,
                     align=(Align.CENTER, Align.CENTER, Align.MIN)) \
        .rotate(Axis.Y, 90).translate((0, length / 2, screw_z))
    return holder - screw
