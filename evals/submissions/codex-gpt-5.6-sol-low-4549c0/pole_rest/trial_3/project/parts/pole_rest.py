from build123d import Align, Axis, Box, Cylinder
from nurb import part


@part
def pole_rest(pole_diameter: float = 20.0):
    """A broad, support-free drying cradle for a freshly finished pole.

    pole_diameter: measured diameter of the pole the cradle supports
    """
    length = 24.0
    axis_height = 18.0
    pole_clearance = 0.20
    cradle_thickness = 2.8

    seat_radius = pole_diameter / 2.0 + pole_clearance
    outside_radius = seat_radius + cradle_thickness

    body = Box(
        2.0 * outside_radius,
        length,
        axis_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    inside = (
        Cylinder(seat_radius, length + 2.0, align=(Align.CENTER, Align.CENTER, Align.CENTER))
        .rotate(Axis.X, 90)
        .translate((0.0, 0.0, axis_height))
    )

    return body - inside
