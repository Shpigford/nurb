"""A support-free drying rest for a finished pole."""

import math

from nurb import *


@part
def pole_rest(
    pole_diameter=measured("pole_diameter"),
    length=24.0,
    cradle_clearance=0.1,
    shell_thickness=1.6,
    draft=False,
):
    """Rest a pole in a continuous, open-top cradle.

    pole_diameter: diameter of the freshly finished pole
    length: length of the rest along the pole
    cradle_clearance: radial air gap between pole and cradle
    shell_thickness: radial material behind the cradle surface
    """
    if pole_diameter <= 0:
        reject("pole_diameter must be positive", param="pole_diameter")
    if length < 20.0:
        reject("length must be at least 20.0 mm", param="length")
    if cradle_clearance < 0.1:
        reject("cradle_clearance must be at least 0.1 mm", param="cradle_clearance")
    if shell_thickness < 1.2:
        reject("shell_thickness must be at least 1.2 mm", param="shell_thickness")

    pole_radius = pole_diameter / 2.0
    inner_radius = pole_radius + cradle_clearance
    outer_radius = inner_radius + shell_thickness
    axis_height = 18.0
    base_width = 30.0
    base_height = min(
        7.8,
        axis_height - pole_radius - cradle_clearance - 0.1,
    )
    corbel_bottom = base_height - 1.0
    corbel_top = axis_height - 5.0
    corbel_gap = 1.0
    corbel_inner_bottom = max(
        4.5,
        math.sqrt(max(inner_radius**2 - (corbel_bottom - axis_height) ** 2, 0.0))
        + corbel_gap,
    )
    corbel_inner_top = (
        math.sqrt(max(inner_radius**2 - (corbel_top - axis_height) ** 2, 0.0))
        + corbel_gap
    )

    # The two coaxial cylinders make a 180-degree lower cradle.  The box clips
    # away the upper half, leaving the complete vertical drop-in path open.
    outer = Pos(0, 0, axis_height) * Cylinder(
        outer_radius, length, rotation=(90, 0, 0)
    )
    inner = Pos(0, 0, axis_height) * Cylinder(
        inner_radius, length, rotation=(90, 0, 0)
    )
    annulus = outer - inner
    lower_half = annulus & Pos(0, 0, axis_height - outer_radius) * Box(
        2.0 * outer_radius + 4.0,
        length + 2.0,
        outer_radius,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    base = Pos(0, 0, base_height / 2.0) * Box(
        base_width,
        length,
        base_height,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    # Low 45-degree side corbels carry the outside of the curved shell from
    # the base without putting support material into the pole's clearance.
    def side_corbels(points):
        profile = make_face(Polygon(*points, align=None))
        prism = extrude(profile, amount=length)
        return Pos(0, length / 2.0, 0) * Rot(90, 0, 0) * prism

    right_corbel = side_corbels(
        [(corbel_inner_bottom, corbel_bottom),
         (outer_radius + 1.3, corbel_bottom),
         (outer_radius + 1.3, corbel_top), (corbel_inner_top, corbel_top)]
    )
    left_corbel = side_corbels(
        [(-corbel_inner_bottom, corbel_bottom),
         (-outer_radius - 1.3, corbel_bottom),
         (-outer_radius - 1.3, corbel_top), (-corbel_inner_top, corbel_top)]
    )
    body = (base + lower_half + right_corbel + left_corbel).clean()

    # The cradle/corbel junctions are structural concave edges; leaving those
    # edges square avoids cosmetic chamfer strips that become thin print walls.
    return body
