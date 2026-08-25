from nurb import *

WALL = 2.0
POCKET_DEPTH = 8.0
CLEARANCE = 0.4


@part
def leg_cup(draft=False):
    """Slip-over foot cup that levels a short workbench leg.

    The rectangular pocket takes the foot from above. The solid floor under it
    is the lift, read from measurements.toml.

    Geometry is derived only from measured leg_width, leg_depth, and lift.
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    pocket_w = leg_width + CLEARANCE
    pocket_d = leg_depth + CLEARANCE
    outer_w = pocket_w + 2 * WALL
    outer_d = pocket_d + 2 * WALL
    outer_h = lift + POCKET_DEPTH

    body = Box(outer_w, outer_d, outer_h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # Overcut the rim so the boolean cannot leave a film over the pocket.
    cutter = Box(
        pocket_w,
        pocket_d,
        POCKET_DEPTH + 1.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    cup = body - cutter.move(Location((0, 0, lift)))
    if draft:
        return cup
    return cup
