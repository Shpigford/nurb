from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), length=12.0, draft=False):
    """A compact, one-screw wall clip for a horizontal cable bundle.

    bundle_diameter: measured diameter across the cable bundle.
    length: how far the retaining channel runs along the bundle.
    """
    # The 0.4 mm fit allowance is deliberately derived from the measured bundle.
    clearance_diameter = bundle_diameter + 0.4
    back_thickness = 2.8
    floor_thickness = 3.0
    lip_thickness = 1.4
    channel_depth = clearance_diameter + 0.2
    bundle_center_x = back_thickness + channel_depth / 2
    # A small seating gap keeps the retained bundle in free space while the floor
    # still stops a 1 mm downward movement.
    bundle_center_z = floor_thickness + clearance_diameter / 2 + 0.2
    lip_height = clearance_diameter + 1.0
    # Keep the M4 head/driver envelope above the cable as the parameter grows.
    back_height = max(22.0, bundle_center_z + clearance_diameter / 2 + 10.0)

    # The broad vertical web is the wall interface; the floor and front rail make a
    # support-free U-channel that blocks both downward and outward cable motion.
    back = Box(back_thickness, length, back_height, align=(Align.MIN, Align.MIN, Align.MIN))
    floor = Pos(back_thickness, 0, 0) * Box(
        channel_depth, length, floor_thickness, align=(Align.MIN, Align.MIN, Align.MIN)
    )
    lip = Pos(back_thickness + channel_depth, 0, 0) * Box(
        lip_thickness, length, lip_height, align=(Align.MIN, Align.MIN, Align.MIN)
    )
    body = back.fuse(floor).fuse(lip)

    # M4 clearance bore, entered from the wall side.  The shallow 8.4 mm access
    # pocket lets a pan-head screw and driver leave in +X without crossing the cable.
    screw_y = length / 2
    screw_z = back_height - 5.3
    shank = Pos(-0.1, screw_y, screw_z) * Rot(0, 90, 0) * Cylinder(2.2, back_thickness + 0.2)
    head_access = Pos(back_thickness - 0.01, screw_y, screw_z) * Rot(0, 90, 0) * Cylinder(4.2, 20.0)
    body = body.cut(shank).cut(head_access)

    return body
