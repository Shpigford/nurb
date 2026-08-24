from nurb import *


@part
def bundle_holder(bundle_diameter: float = 8.0, length: float = 14.0):
    """A low-material wall clip for a horizontal cable bundle.

    bundle_diameter: measured diameter of the cable bundle.
    length: contact length along the cable's run.
    """
    # The 0.4 mm diametral allowance is deliberate: this is a printed clip,
    # not a nominal-size bore.  X is wall-to-room, Y is cable length, Z is up.
    clearance = 0.4
    bundle_space = bundle_diameter + clearance
    radius = bundle_space / 2
    back_thickness = 3.0
    shelf_thickness = 2.8
    rail_thickness = 2.6
    rail_height = radius + shelf_thickness + 0.5

    # A generous wall plate gives the M4 head a solid, isolated seat above the
    # cable path.  The open C channel lets the bundle be threaded along Y.
    plate_height = bundle_space + shelf_thickness + 12.8
    body = Box(back_thickness, length, plate_height)
    bed_z = -plate_height / 2
    shelf_z = bed_z + shelf_thickness / 2
    body = body + Box(bundle_space, length, shelf_thickness).translate((back_thickness / 2 + bundle_space / 2, 0, shelf_z))
    body = body + Box(rail_thickness, length, rail_height).translate((back_thickness / 2 + bundle_space + rail_thickness / 2, 0, bed_z + rail_height / 2))

    # M4 clearance bore from the wall, followed by an 8.4 mm square head/driver
    # clearance pocket.  The pocket starts after 3 mm of shank guide material.
    screw_z = plate_height / 2 - 5.0
    bore = Box(back_thickness, 4.4, 4.4).translate((0, 0, screw_z))
    head_clearance = Box(6.0, 8.4, 8.4).translate((back_thickness / 2 + 3.0, 0, screw_z))
    return body - bore - head_clearance
