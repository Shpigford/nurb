from nurb import *


@part
def bundle_holder(bundle_diameter: float = measured("bundle_diameter")):
    """Wall holder for a horizontal cable bundle.

    bundle_diameter: diameter of the cable bundle that sits in the channel
    """
    clearance = 0.4
    channel_diameter = bundle_diameter + 2.0 * clearance

    # The wall is the minimum-X face.  All three members start on the bed,
    # keeping this a support-free, single-solid print.
    length = 30.0
    plate_thickness = 2.4
    plate_height = max(15.0, channel_diameter + 6.0)
    floor_thickness = 2.0
    floor_depth = channel_diameter + 2.0

    back = Box(plate_thickness, length, plate_height,
               align=(Align.MIN, Align.MIN, Align.MIN))
    floor = Pos(0, 0, 0) * Box(plate_thickness + floor_depth, length,
                                floor_thickness,
                                align=(Align.MIN, Align.MIN, Align.MIN))

    # A short front post blocks +X motion for 12 mm of the 30 mm run.
    post_length = 12.0
    post_y = (length - post_length) / 2.0
    post_x = plate_thickness + floor_depth - 2.0
    post = Pos(post_x, post_y, 0) * Box(
        2.0, post_length, plate_height - 1.0,
        align=(Align.MIN, Align.MIN, Align.MIN))

    body = back + floor + post

    # M4 medium clearance, axis along X, through the wall plate.  The seat
    # is the +X face of the 2.4 mm plate; it is below the cable channel.
    screw_y = length / 2.0
    screw_z = 4.6
    bore = Pos(-0.1, screw_y, screw_z) * Rot(0, 90, 0) * Cylinder(
        2.2, plate_thickness + 0.2,
        align=(Align.CENTER, Align.CENTER, Align.MIN))
    return body - bore
