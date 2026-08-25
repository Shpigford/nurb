from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Low-profile, wall-mounted cable-bundle saddle.

    bundle_diameter: measured diameter of the cable bundle held in the saddle.
    """
    # X is wall-to-room, Y is the cable direction, and Z is print-up.
    length = 12.0
    back_thickness = 3.2
    back_height = max(bundle_diameter + 15.0, 23.0)
    clearance = 0.5
    bundle_radius = bundle_diameter / 2.0 + clearance
    shelf_thickness = 3.0
    bundle_center_z = shelf_thickness + bundle_radius + 0.5
    bundle_center_x = back_thickness + bundle_radius + 0.5
    lip_inner_x = bundle_center_x + bundle_radius + 0.5
    lip_thickness = 2.4
    # The lip need only cross the bundle's middle; keeping it low leaves a full
    # head-and-driver corridor above the cable.
    lip_height = bundle_center_z + 2.0

    if bundle_diameter <= 0.0:
        reject("bundle_diameter must be positive", param="bundle_diameter")

    back = Box(back_thickness, length, back_height,
               align=(Align.MIN, Align.MIN, Align.MIN))
    shelf = Box(lip_inner_x + lip_thickness, length, shelf_thickness,
                align=(Align.MIN, Align.MIN, Align.MIN))
    lip = Box(lip_thickness, length, lip_height,
              align=(Align.MIN, Align.MIN, Align.MIN)).translate((lip_inner_x, 0, 0))
    body = back + shelf + lip

    # M4 clearance bore normal to the wall. Its 3.2 mm wall thickness is the
    # bearing land for the pan head; the open space ahead clears head and driver.
    screw_y = length / 2.0
    screw_z = back_height - 6.0
    bore = Cylinder(2.2, back_thickness + 0.4).rotate(Axis.Y, 90).translate(
        (back_thickness / 2.0, screw_y, screw_z)
    )
    return body - bore
