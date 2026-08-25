from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), draft=False):
    """A support-free J-clip for a horizontal cable bundle.

    bundle_diameter: measured diameter of the cable bundle held in the channel.
    """
    length = 12.5
    back_thickness = 3.5
    back_height = 20.5
    clearance = 0.4
    bundle_radius = bundle_diameter / 2.0 + clearance
    shelf_height = 3.5
    bundle_center_x = back_thickness + bundle_radius
    bundle_center_z = shelf_height + bundle_radius
    lip_thickness = 2.0
    lip_x = bundle_center_x + bundle_radius

    back = Box(back_thickness, length, back_height,
               align=(Align.MIN, Align.MIN, Align.MIN))
    # A small overlap turns the three rails into one watertight solid.
    shelf = Box(lip_x + 0.3, length, shelf_height,
                align=(Align.MIN, Align.MIN, Align.MIN))
    lip = Box(lip_thickness, length, shelf_height + bundle_radius + 2.0,
              align=(Align.MIN, Align.MIN, Align.MIN)).translate((lip_x, 0, 0))
    body = back + shelf + lip

    screw_y = length / 2.0
    screw_z = back_height - 5.5
    shank = Cylinder(2.2, back_thickness + 1.0, rotation=(0, 90, 0),
                     align=(Align.CENTER, Align.CENTER, Align.CENTER)).translate((1.75, screw_y, screw_z))
    head = Cylinder(4.3, 1.1, rotation=(0, 90, 0),
                    align=(Align.CENTER, Align.CENTER, Align.CENTER)).translate((2.95, screw_y, screw_z))
    return body - shank - head
