from nurb import *


@part
def leg_cup():
    """Slip-over rectangular foot cup with an exact rectangular pocket."""
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    pocket_width = leg_width + 0.4
    pocket_depth = leg_depth + 0.4
    outer_width = pocket_width + 4.0
    outer_depth = pocket_depth + 4.0
    pocket_height = 8.0

    body = Box(
        outer_width,
        outer_depth,
        lift + pocket_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    pocket = Pos(0, 0, lift) * Box(
        pocket_width,
        pocket_depth,
        pocket_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return body - pocket
