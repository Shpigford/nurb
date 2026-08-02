from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), draft=False):
    """
    bundle_diameter: measured width across the cable bundle this holder retains
    """
    length = 15.0
    wall_thickness = 2.6
    screw_bore_width = 4.4
    screw_head_clearance = 8.4
    cable_clearance = bundle_diameter + 0.4

    cable_radius = cable_clearance / 2
    cable_center_x = cable_radius
    cable_center_z = 12.2
    front_x = cable_center_x + cable_radius + 2.4
    lip_height = cable_center_z + cable_radius - 7.3
    seat_x = 2.6

    def block(size_x, size_y, size_z, x, y, z):
        return Pos(x + size_x / 2, y, z + size_z / 2) * Box(
            size_x, size_y, size_z
        )

    lower_body = block(front_x, length, 9.0, 0.0, 0.0, 0.0)
    back_plate = block(seat_x, length, 8.0, 0.0, 0.0, 0.0)
    front_lip = block(2.4, length, lip_height, front_x - 2.4, 0.0, 7.3)
    body = lower_body + back_plate + front_lip

    cable_space = block(
        cable_clearance,
        length + 1.0,
        cable_clearance,
        cable_center_x - cable_radius,
        0.0,
        cable_center_z - cable_radius,
    )
    screw_bore = Pos(front_x / 2, 0.0, 4.4) * Cylinder(
        screw_bore_width / 2, front_x + 2.0, rotation=(0, 90, 0)
    )
    head_space_depth = front_x - seat_x + 1.0
    head_space = block(
        head_space_depth,
        screw_head_clearance,
        cable_center_z + cable_radius,
        seat_x,
        0.0,
        0.0,
    )
    body = body - cable_space - screw_bore - head_space

    return body
