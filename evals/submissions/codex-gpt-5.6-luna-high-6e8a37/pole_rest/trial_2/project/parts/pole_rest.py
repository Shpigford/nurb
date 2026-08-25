from nurb import *


@part
def pole_rest(pole_diameter=measured("pole_diameter"), draft=False):
    """A support-free cradle for a freshly finished pole.

    pole_diameter: diameter of the pole being held
    """
    axis_height = 18.0
    pole_radius = pole_diameter / 2.0
    clearance = 0.2
    cradle_radius = pole_radius + clearance

    # A 130-degree lower arc gives the pole a real cradle rather than two
    # edge contacts.  Keeping the opening below the pole centre also lets the
    # pole drop vertically into the seat.
    opening_height = axis_height - cradle_radius * 0.42
    block_width = 2.0 * (cradle_radius + 2.0)
    block_length = 24.0

    body = Box(
        block_width,
        block_length,
        opening_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    bore = Pos(0, 0, axis_height) * Cylinder(
        cradle_radius,
        block_length + 2.0,
        rotation=(90, 0, 0),
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    return body - bore
