from nurb import *


@part
def pole_rest(pole_diameter=measured("pole_diameter"), rest_length=30.0):
    """A support-free drying rest with a semicircular padded cradle.

    pole_diameter: diameter of the finished pole held by the rest
    rest_length: length of the rest in the direction the pole runs
    """
    if pole_diameter <= 0.0:
        reject("pole_diameter must be positive", param="pole_diameter")
    if rest_length < 20.0:
        reject("rest_length must be at least 20mm for stable pole support", param="rest_length")

    # The axis is deliberately fixed at z=18.  The 0.2mm radial gap protects
    # a soft finish while the remaining lower semicircle supplies a 180-degree
    # continuous, backed support arc.
    seat_radius = pole_diameter / 2.0 + 0.2
    body_width = pole_diameter + 4.0
    body = Box(body_width, rest_length, 18.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    cutter = Pos(0, 0, 18.0) * Cylinder(
        seat_radius,
        rest_length + 2.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
        rotation=(90, 0, 0),
    )
    return body - cutter
