from nurb import *


@part
def pole_rest(pole_diameter=measured("pole_diameter")):
    """A support-free drying rest for a finished pole.

    pole_diameter: diameter of the pole being dried
    """
    pole_radius = pole_diameter / 2.0
    axis_height = 18.0
    clearance = 0.15
    wall_thickness = 1.6
    cradle_length = 24.0

    inner_radius = pole_radius + clearance
    outer_radius = inner_radius + wall_thickness

    # The pole lies along Y.  A vertical-sided outer block keeps the cradle's
    # outside self-supporting while the cylindrical cut supplies the soft,
    # continuous lower cradle and its straight drop-in opening.
    outer = Pos(0, 0, axis_height - outer_radius) * Box(
        2.0 * outer_radius,
        cradle_length,
        outer_radius,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    inner = Pos(0, 0, axis_height) * Rot(90, 0, 0) * Cylinder(
        inner_radius,
        cradle_length + 0.4,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    cradle = outer - inner

    # Broad flat footprint: the cradle penetrates the base for a single solid.
    base = Box(
        28.0,
        26.0,
        7.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    body = base + cradle

    return body
