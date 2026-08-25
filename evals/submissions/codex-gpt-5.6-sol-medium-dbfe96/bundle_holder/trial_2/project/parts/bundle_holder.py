from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Hold a horizontal cable bundle against a wall with one M4 screw.

    bundle_diameter: measured width across the cable bundle
    """
    clearance = 0.6
    opening = bundle_diameter + clearance

    part_length = 14.0
    retained_length = 5.0
    back_thickness = 3.0
    back_height = 20.0
    floor_thickness = 2.0
    front_wall = 2.0

    inner_front = back_thickness + opening
    outer_front = inner_front + front_wall
    rail_height = floor_thickness + opening

    minimum = (Align.MIN, Align.MIN, Align.MIN)
    back = Box(back_thickness, part_length, back_height, align=minimum)
    floor = Box(outer_front, retained_length, floor_thickness, align=minimum)
    rail = Pos(inner_front, 0, 0) * Box(
        front_wall, retained_length, rail_height, align=minimum
    )

    body = back + floor + rail

    screw_y = 9.0
    screw_z = 15.0
    screw_bore = (
        Pos(0, screw_y, screw_z)
        * Rot(0, 90, 0)
        * Cylinder(
            2.2,
            back_thickness,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    )
    body = body - screw_bore

    return body
