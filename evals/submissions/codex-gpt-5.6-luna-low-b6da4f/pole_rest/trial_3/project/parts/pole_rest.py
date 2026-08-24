from nurb import *


@part
def pole_rest(pole_diameter: float = measured("pole_diameter")):
    """A soft-finish pole rest with an open-top cradle.

    pole_diameter: diameter of the pole being dried
    """
    radius = pole_diameter / 2.0
    clearance = 0.1
    backing = 1.5
    length = 24.0
    base_width = 30.0
    base_height = 7.0
    axis_height = 18.0

    # Cylinders run along Y.  A square-backed cradle keeps the outside walls
    # vertical while the inside remains a true circular, soft-finish seat.
    inner = Cylinder(
        radius + clearance,
        length + 2.0,
        rotation=(90, 0, 0),
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    ).translate((0, length / 2.0, axis_height))
    cradle = Box(
        2.0 * (radius + clearance + backing), length,
        axis_height - (axis_height - radius - clearance - backing),
        align=(Align.CENTER, Align.MIN, Align.MIN),
    ).translate((0, 0, axis_height - radius - clearance - backing)).cut(inner)
    base = Box(
        base_width,
        length,
        base_height,
        align=(Align.CENTER, Align.MIN, Align.MIN),
    )
    return base.fuse(cradle)
