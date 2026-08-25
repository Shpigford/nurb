from math import sqrt

from nurb import *


@part
def pole_rest(pole_diameter=20.0):
    """A low, stable cradle for a freshly finished pole.

    pole_diameter: measured diameter of the pole the rest cradles
    """
    length = 24.0
    axis_height = 18.0
    clearance = 0.2
    cradle_thickness = 2.4
    base_width = pole_diameter + 8.0
    base_height = axis_height - pole_diameter / 2.0 - cradle_thickness + 0.2

    inner_radius = pole_diameter / 2.0 + clearance
    outer_radius = inner_radius + cradle_thickness

    base = Box(base_width, length, base_height).translate(
        (0, 0, base_height / 2.0)
    )

    outer = Cylinder(outer_radius, length).rotate(
        Axis((0, 0, 0), (1, 0, 0)), -90
    ).translate((0, 0, axis_height))
    inner = Cylinder(inner_radius, length).rotate(
        Axis((0, 0, 0), (1, 0, 0)), -90
    ).translate((0, 0, axis_height))
    lower_half = Box(
        2.0 * outer_radius + 2.0,
        length,
        outer_radius,
    ).translate(
        (0, 0, axis_height - outer_radius / 2.0)
    )
    lower_outer = outer & lower_half

    # This central mass follows the seat after the pole clearance is cut from it.
    # Its sides begin just beyond the 45-degree points of the outer cylinder, so
    # every remaining exposed underside is printable without support.
    support_width = 2.0 * outer_radius / sqrt(2.0) + 0.4
    support = Box(support_width, length, axis_height).translate(
        (0, 0, axis_height / 2.0)
    )
    body = (base + lower_outer + support) - inner

    return body
