from nurb import *

# Specified fit, not measured: clearance around the leg, wall thickness, pocket depth.
_CLEARANCE = 0.4
_WALL = 2.0
_POCKET = 8.0


@part
def leg_cup():
    """Slip-over foot cup that levels a wobbly workbench.

    The short leg drops into a rectangular pocket from above. A solid floor under
    the foot lifts the bench by `lift` from measurements.toml, which is still a
    guess until someone measures the wobble.

    Pocket inner size is the measured leg plus 0.4 mm clearance, 8 mm deep, with
    2 mm walls on all four sides. Prints pocket-up, flat on the bed.
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    inner_x = leg_width + _CLEARANCE
    inner_y = leg_depth + _CLEARANCE
    outer_x = inner_x + 2 * _WALL
    outer_y = inner_y + 2 * _WALL
    height = lift + _POCKET

    body = Box(outer_x, outer_y, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # Overshoot the top so the boolean cannot leave a film roofing the pocket.
    cutter = Box(
        inner_x,
        inner_y,
        _POCKET + 1.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).moved(Location((0, 0, lift)))
    return body - cutter

