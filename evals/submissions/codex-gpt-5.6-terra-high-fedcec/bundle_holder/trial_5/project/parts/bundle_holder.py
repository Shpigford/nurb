from nurb import *
from math import sqrt


@part
def bundle_holder(bundle_diameter: float = measured("bundle_diameter"), draft=False):
    """A compact wall clip for one horizontal cable bundle.

    bundle_diameter: measured diameter of the cable bundle held in the channel.
    """
    if bundle_diameter <= 0.0:
        reject("bundle_diameter must be greater than zero", param="bundle_diameter")

    # The channel is sized from the measured bundle with 0.4 mm total clearance.
    channel_diameter = bundle_diameter + 0.4
    back_thickness = 2.6
    shelf_thickness = 1.8
    length = 16.0
    lip_thickness = 2.0
    cable_center_x = back_thickness + channel_diameter / 2.0
    cable_center_z = shelf_thickness + channel_diameter / 2.0

    # Keep the M4 head completely above the cable envelope.  This is deliberately
    # derived too, so a nearby bundle size retains the same installation clearance.
    screw_z = cable_center_z + bundle_diameter / 2.0 + 4.5
    back_height = screw_z + 4.5

    # A back plate, grounded shelf, and short front rail make a continuous, printable
    # U-channel.  The rail begins at the clearance envelope, so it retains an inserted
    # bundle without reducing the stated channel size.
    back = Box(back_thickness, length, back_height,
               align=(Align.MIN, Align.CENTER, Align.MIN))
    shelf = Pos(back_thickness, 0, 0) * Box(
        channel_diameter + lip_thickness, length, shelf_thickness,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    # At the rail, a bundle moved 1 mm outward still has this much vertical extent.
    shifted_half_width = channel_diameter / 2.0 - 1.0
    retained_top = cable_center_z + sqrt(
        (bundle_diameter / 2.0) ** 2 - shifted_half_width ** 2
    )
    lip_height = retained_top + 0.3
    lip = Pos(back_thickness + channel_diameter, 0, 0) * Box(
        lip_thickness, length, lip_height,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )

    # M4 clearance bore through the wall plate.  Its seat is the front of the 2.6 mm
    # plate; the open channel in front gives an 8.4 mm pan-head/driver a clear exit.
    bore = Pos(0, 0, screw_z) * Cylinder(
        2.2, back_thickness + 0.02, rotation=(0, 90, 0),
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    return (back + shelf + lip) - bore
