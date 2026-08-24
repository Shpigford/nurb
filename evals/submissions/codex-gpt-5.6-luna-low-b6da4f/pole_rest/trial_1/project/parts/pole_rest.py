from nurb import *


@part
def pole_rest(pole_diameter=20.0):
    """A soft-finish pole rest.

    pole_diameter: diameter of the pole being dried
    """
    pole_radius = pole_diameter / 2.0
    clearance = 0.1
    wall = 3.0
    outer_radius = pole_radius + clearance + wall
    axis_height = 18.0
    length = 24.0

    # The broad, flat foot seats the rest on the bed.  Its top is below the
    # pole axis, leaving the cradle itself to establish the fit.
    foot_height = 11.0
    foot_width = 2.0 * outer_radius + 1.0
    foot = Box(
        foot_width,
        length,
        foot_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    # A tube along Y, clipped at z=13: the remaining lower arc is open above
    # the seat, so the pole can drop straight down without striking a rim.
    outer = Cylinder(
        outer_radius,
        length,
        rotation=(90, 0, 0),
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).translate((0, length / 2.0, axis_height))
    inner = Cylinder(
        pole_radius + clearance,
        length + 0.4,
        rotation=(90, 0, 0),
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).translate((0, length / 2.0 + 0.2, axis_height))
    shell = outer - inner
    lower_half = Box(
        2.0 * outer_radius + 2.0,
        length + 2.0,
        axis_height - 5.5,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    cradle = shell & lower_half

    # Narrow side ribs give the clipped outer flanks a full-width print path.
    rib_x = outer_radius - 1.5
    ribs = (
        Box(3.0, length, 2.0, align=(Align.CENTER, Align.CENTER, Align.MIN)).translate((rib_x, 0, 11.0))
        + Box(3.0, length, 2.0, align=(Align.CENTER, Align.CENTER, Align.MIN)).translate((-rib_x, 0, 11.0))
    )

    return foot + cradle + ribs
