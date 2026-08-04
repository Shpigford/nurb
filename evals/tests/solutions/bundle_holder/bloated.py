"""A brick with a bundle tunnel and a counterbored screw hole. Everything works, so
only the material ladder separates it from the reference: the function checks must
pass and the volume steps must all fail."""

from nurb import *


@part
def bundle_holder(bundle_diameter=8.0):
    length = 12.0
    height = bundle_diameter + 16.0
    body = Pos(14.0, 0, height / 2) * Box(28.0, length, height)
    tunnel = (
        Pos(9.0, 0, 2.4 + bundle_diameter / 2 + 0.2)
        * Rot(90, 0, 0)
        * Cylinder(bundle_diameter / 2 + 0.2, length)
    )
    hole_z = height - 6.0
    bore = Pos(3.0, 0, hole_z) * Rot(0, 90, 0) * Cylinder(2.2, 6.0)
    pocket = Pos(17.0, 0, hole_z) * Rot(0, 90, 0) * Cylinder(4.3, 22.0)
    return body - tunnel - bore - pocket
