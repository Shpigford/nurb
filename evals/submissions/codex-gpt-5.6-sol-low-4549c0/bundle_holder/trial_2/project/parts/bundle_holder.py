from nurb import *
from build123d import Align, Axis, Box, Cylinder, Pos


@part
def bundle_holder(bundle_diameter: float = 8.0):
    """Wall-mounted channel for a horizontal cable bundle.

    bundle_diameter: measured diameter of the cable bundle
    """
    clearance = 0.4
    bundle_space = bundle_diameter + clearance

    length = 12.0
    back_thickness = 3.0
    floor_thickness = 2.4
    retaining_wall = 1.8
    channel_top = floor_thickness + bundle_space
    screw_z = channel_top + 5.7
    holder_height = screw_z + 6.5

    channel_depth = bundle_space
    outer_x = back_thickness + channel_depth

    at_min = (Align.MIN, Align.MIN, Align.MIN)
    back = Box(back_thickness, length, holder_height, align=at_min)
    floor = Box(outer_x + retaining_wall, length, floor_thickness, align=at_min)
    lip = Pos(outer_x, 0, floor_thickness) * Box(
        retaining_wall, length, bundle_space, align=at_min
    )

    body = back + floor + lip

    screw_bore = Pos(0, length / 2, screw_z) * Cylinder(
        2.2,
        back_thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).rotate(Axis.Y, 90)

    return body - screw_bore
