from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), draft=False):
    """A wall-mounted tunnel that retains a horizontal cable bundle.

    bundle_diameter: measured width of the cable bundle the tunnel holds
    """
    clearance = 0.4
    opening = bundle_diameter + clearance
    wall = 2.4
    length = 12.0

    # The channel begins at the wall plate and retains the bundle below and away
    # from the wall. Its open top avoids bridges and makes installation easy.
    plate_thickness = 3.0
    tunnel_height = opening + 2.0 * wall
    tunnel_depth = opening + wall
    plate_height = tunnel_height + 10.0

    box_align = (Align.MIN, Align.MIN, Align.MIN)
    back = Box(plate_thickness, length, plate_height, align=box_align)
    floor = Pos(plate_thickness - 0.01, 0, 0) * Box(
        opening + 0.02, length, wall, align=box_align
    )
    front = Pos(plate_thickness + opening, 0, 0) * Box(
        wall, length, tunnel_height, align=box_align
    )
    body = back + floor + front

    # Three millimetres of shank-bearing wall precedes an unobstructed pan-head recess.
    screw_z = tunnel_height + 5.0
    shank = Pos(0, length / 2.0, screw_z) * Cylinder(
        2.2,
        plate_thickness,
        rotation=(0, 90, 0),
        align=(Align.MIN, Align.CENTER, Align.CENTER),
    )
    head_clearance = Pos(plate_thickness, length / 2.0, screw_z) * Cylinder(
        4.2,
        tunnel_depth,
        rotation=(0, 90, 0),
        align=(Align.MIN, Align.CENTER, Align.CENTER),
    )
    # Open the upper half of the head recess to the top. The pan head still seats
    # against the 3 mm plate, while the recess prints without a circular ceiling.
    driver_slot = Pos(plate_thickness, length / 2.0 - 4.2, screw_z) * Box(
        tunnel_depth,
        8.4,
        plate_height - screw_z + 0.01,
        align=box_align,
    )
    body = body - shank - head_clearance - driver_slot

    return body
