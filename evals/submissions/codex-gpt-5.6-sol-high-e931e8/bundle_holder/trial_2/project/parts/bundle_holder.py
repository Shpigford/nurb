from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Hold a horizontal cable bundle against a wall with one M4 screw.

    bundle_diameter: measured width across the cable bundle
    """
    if bundle_diameter < 4.0:
        reject(
            "bundle_diameter below 4 mm leaves the fixed M4 mount needlessly large",
            param="bundle_diameter",
        )
    if bundle_diameter > 14.0:
        reject(
            "bundle_diameter above 14 mm needs a taller wall plate around the M4 mount",
            param="bundle_diameter",
        )

    length = 14.0
    cable_clearance = 0.4
    channel_width = bundle_diameter + cable_clearance
    wall_thickness = 2.0
    screw_seat_x = 2.4
    back_thickness = screw_seat_x

    cable_center_x = back_thickness + channel_width / 2
    floor_top = wall_thickness
    cable_center_z = floor_top + channel_width / 2

    front_inside_x = cable_center_x + channel_width / 2
    front_outside_x = front_inside_x + wall_thickness
    front_height = cable_center_z + bundle_diameter / 2 + 0.2

    screw_center_z = front_height + 6.1
    plate_height = screw_center_z + 5.5

    min_corner = (Align.MIN, Align.MIN, Align.MIN)
    back = Box(back_thickness, length, plate_height, align=min_corner)
    floor = Pos(back_thickness, 0, 0) * Box(
        front_outside_x - back_thickness,
        length,
        wall_thickness,
        align=min_corner,
    )
    front = Pos(front_inside_x, 0, 0) * Box(
        wall_thickness,
        length,
        front_height,
        align=min_corner,
    )
    body = back + floor + front

    screw_y = length / 2
    shank = (
        Cylinder(
            2.25,
            screw_seat_x + 0.1,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        .rotate(Axis.Y, 90)
        .translate((0, screw_y, screw_center_z))
    )
    head_and_driver = (
        Cylinder(
            4.3,
            0.3,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        .rotate(Axis.Y, 90)
        .translate((screw_seat_x, screw_y, screw_center_z))
    )
    body = body - shank - head_and_driver

    if draft:
        return body

    exposed_front_rim = body.edges().filter_by(
        lambda edge: edge.bounding_box().min.X > front_outside_x - 0.01
        and edge.bounding_box().min.Z > front_height - 0.01
    )
    return polish(body, exposed_front_rim, 1.0)
