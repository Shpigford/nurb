from nurb import *
from math import radians, sin


@part
def pole_rest(pole_diameter=measured("pole_diameter"), length=28.0, draft=False):
    """A low, open-top drying cradle for a finished pole.

    pole_diameter: measured diameter of the pole held by the cradle
    length: how far the rest runs along the pole
    """
    # The pole's axis is fixed at Z=18. The small horizontal terraces trace the
    # lower 120 degrees of its clearance circle; unlike a smooth trough they
    # present only upward-facing and vertical printable surfaces.
    axis_height = 18.0
    clearance_radius = pole_diameter / 2.0 + 0.10
    arc_half_width = clearance_radius * 0.8660254  # sin(60°): 120° total arc
    base_height = 5.0
    width = 2.0 * arc_half_width + 2.0
    base = Box(width, length, base_height, align=(Align.CENTER, Align.CENTER, Align.MIN))

    body = base
    # One wide central terrace avoids a row of microscopic faces at the bottom;
    # 2-degree terraces take over where the circle rises more quickly.
    central_x = clearance_radius * 0.1736482  # sin(10°)
    central_top = axis_height - clearance_radius
    body = body + Box(2.0 * central_x, length, central_top, align=(Align.CENTER, Align.CENTER, Align.MIN))
    for side in (-1.0, 1.0):
        for degrees in range(10, 60, 2):
            inner_x = clearance_radius * sin(radians(degrees))
            outer_x = clearance_radius * sin(radians(degrees + 2))
            top = axis_height - (clearance_radius ** 2 - inner_x ** 2) ** 0.5
            # The end terrace continues outward as a buttress, eliminating a
            # thin free-standing lip while staying below the pole surface.
            extra = 1.5 if degrees == 58 else 0.02
            column = Box(outer_x - inner_x + extra, length, top, align=(Align.CENTER, Align.CENTER, Align.MIN))
            center_x = side * ((inner_x + outer_x) / 2.0 + extra / 2.0)
            body = body + column.translate((center_x, 0, 0))
    return body
