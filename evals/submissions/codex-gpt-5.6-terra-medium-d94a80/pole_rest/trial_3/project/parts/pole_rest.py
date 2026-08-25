from nurb import *


@part
def pole_rest(pole_diameter=measured("pole_diameter"), draft=False):
    """A low, continuously lined cradle for drying a finished pole.

    pole_diameter: measured diameter of the pole the rest cradles
    """
    if pole_diameter <= 0.0:
        reject("pole_diameter must be positive", param="pole_diameter")

    # The pole center is deliberately fixed: every other radial dimension follows it.
    pole_axis_height = 18.0
    clearance = 0.15
    inner_radius = pole_diameter / 2.0 + clearance
    outer_radius = inner_radius + 1.9
    length = 24.0
    band_length = 1.5
    band_centers = tuple(-11.0 + 2.0 * index for index in range(12))
    base_height = pole_axis_height - outer_radius + 1.0

    base = Box(2.0 * outer_radius + 2.0, length, base_height,
               align=(Align.CENTER, Align.CENTER, Align.MIN))
    # Each short saddle band bridges between its open ends.  The twelve bands give the
    # pole a continuous curved bearing over 75% of the rest's length without asking
    # the printer to form a long unsupported circular overhang.
    body = base
    for center_y in band_centers:
        outer = Pos(0, center_y + band_length / 2.0, pole_axis_height) * Rot(90, 0, 0) * Cylinder(outer_radius, band_length)
        inner = Pos(0, center_y + band_length / 2.0, pole_axis_height) * Rot(90, 0, 0) * Cylinder(inner_radius, band_length)
        lower_half = Pos(0, center_y, 0) * Box(
            2.0 * outer_radius + 2.0, band_length, pole_axis_height,
            align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        body += (outer & lower_half) - inner
    return body
