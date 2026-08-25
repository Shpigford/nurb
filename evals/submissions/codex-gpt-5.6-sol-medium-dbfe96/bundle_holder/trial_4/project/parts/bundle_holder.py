from nurb import *


@part
def bundle_holder(bundle_diameter: float = 8.0):
    """A wall-mounted, thread-through holder for a horizontal cable bundle.

    bundle_diameter: measured width of the cable bundle
    """
    clearance = 0.4
    cable_space = bundle_diameter + clearance
    cable_radius = cable_space / 2

    length = max(12.0, bundle_diameter + 4.0)
    wall_thickness = 3.0
    floor_thickness = 2.4
    retaining_wall = 2.4

    cable_center_z = floor_thickness + cable_radius
    retaining_x = wall_thickness + cable_space
    outer_x = retaining_x + retaining_wall

    screw_hole_radius = 2.2
    screw_head_radius = 4.2
    screw_center_y = length / 2
    screw_center_z = cable_center_z + cable_radius + screw_head_radius + 1.0
    plate_height = screw_center_z + screw_head_radius + 1.0

    back_plate = Box(
        wall_thickness,
        length,
        plate_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    floor = Box(
        outer_x,
        length,
        floor_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    lip_height = cable_center_z + 1.5
    outer_lip = Box(
        retaining_wall,
        length,
        lip_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    ).translate((retaining_x, 0, 0))

    body = back_plate + floor + outer_lip

    screw_bore = (
        Cylinder(
            screw_hole_radius,
            wall_thickness + 0.2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        .rotate(Axis.Y, 90)
        .translate((-0.1, screw_center_y, screw_center_z))
    )
    body = body - screw_bore

    return body
