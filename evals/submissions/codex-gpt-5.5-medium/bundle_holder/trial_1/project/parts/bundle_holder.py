from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), length=12.0, draft=False):
    """Wall-mounted cable bundle holder.

    bundle_diameter: diameter of the cable bundle the channel clears
    length: length of holder along the cable run
    """
    clearance = 0.4
    bundle_clearance = bundle_diameter + 2 * clearance

    back_thickness = 2.6
    floor_thickness = 2.4
    lip_thickness = 2.4
    side_clearance = 0.4
    top_of_channel = floor_thickness + bundle_clearance + 1.2
    height = top_of_channel + 9.0
    inside_depth = bundle_clearance + side_clearance
    depth = back_thickness + inside_depth + lip_thickness

    back = Pos(back_thickness / 2, 0, height / 2) * Box(back_thickness, length, height)
    floor = Pos(depth / 2, 0, floor_thickness / 2) * Box(depth, length, floor_thickness)
    lip_height = floor_thickness + bundle_clearance + 1.0
    lip = Pos(depth - lip_thickness / 2, 0, lip_height / 2) * Box(
        lip_thickness, length, lip_height
    )
    body = back + floor + lip

    screw_bore_width = 4.4
    screw_head_clearance = 8.4
    screw_z = floor_thickness + bundle_clearance + 5.3
    screw_axis_length = depth + 1.0
    shaft = Pos(depth / 2, 0, screw_z) * Rot(0, 90, 0) * Cylinder(
        screw_bore_width / 2, screw_axis_length
    )
    head_exit = depth + 0.5
    head_pocket = Pos((back_thickness + head_exit) / 2, 0, screw_z) * Rot(
        0, 90, 0
    ) * Cylinder(screw_head_clearance / 2, head_exit - back_thickness)
    body = body - shaft - head_pocket

    return body
