from nurb import *


@part
def pole_rest(pole_diameter: float = 20.0):
    """A broad, support-free drying rest for a freshly finished pole.

    pole_diameter: measured width of the pole this rest cradles
    """
    pole_radius = pole_diameter / 2.0
    clearance = 0.25
    seat_radius = pole_radius + clearance

    # The pole axis is fixed 18 mm above the bed. Ending the block 5 mm
    # below that axis exposes a little over 120 degrees of the circular seat.
    axis_height = 18.0
    top_height = axis_height - pole_radius / 2.0
    length = 24.0
    width = max(24.0, pole_diameter + 4.0)

    body = Box(width, length, top_height).translate((0, 0, top_height / 2.0))
    seat = Cylinder(seat_radius, length + 2.0).rotate(Axis.X, 90).translate(
        (0, 0, axis_height)
    )
    return body - seat
