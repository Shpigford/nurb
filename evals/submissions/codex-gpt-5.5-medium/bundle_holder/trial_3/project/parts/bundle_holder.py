from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), draft=False):
    """
    bundle_diameter: measured width of the cable bundle that runs through the holder
    """
    length = max(10.8, bundle_diameter + 2.8)
    cable_clearance = bundle_diameter + 0.4
    wall = 2.0
    screw_hole_width = 4.4
    screw_head_clearance = 8.4
    screw_seat_depth = 2.6

    depth = cable_clearance + 2 * wall
    cable_center_x = wall + cable_clearance / 2
    cable_center_z = wall + cable_clearance / 2
    screw_center_z = cable_center_z + cable_clearance / 2 + screw_head_clearance / 2 + 1.0
    height = screw_center_z + screw_head_clearance / 2

    body = Box(
        depth,
        length,
        height,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )

    cable_tunnel = Pos(cable_center_x, 0, cable_center_z) * Cylinder(
        cable_clearance / 2,
        length + 1.0,
        rotation=(90, 0, 0),
    )
    screw_bore = Pos(depth / 2, 0, screw_center_z) * Cylinder(
        screw_hole_width / 2,
        depth + 1.0,
        rotation=(0, 90, 0),
    )
    head_clearance = Pos(
        screw_seat_depth + (depth - screw_seat_depth + 0.5) / 2,
        0,
        screw_center_z,
    ) * Box(
        depth - screw_seat_depth + 0.5,
        screw_head_clearance,
        screw_head_clearance,
    )

    body = body - cable_tunnel - screw_bore - head_clearance
    return body
