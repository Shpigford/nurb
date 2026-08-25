from nurb import *


@part
def leg_cup():
    """A solid-floor slip-over cup for the measured rectangular workbench leg."""
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    wall = 2.0
    pocket_width = leg_width + 0.4
    pocket_depth = leg_depth + 0.4
    pocket_height = 8.0
    outer_width = pocket_width + 2.0 * wall
    outer_depth = pocket_depth + 2.0 * wall
    total_height = lift + pocket_height

    body = Box(
        outer_width,
        outer_depth,
        total_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    pocket = Pos(0, 0, lift) * Box(
        pocket_width,
        pocket_depth,
        pocket_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return body - pocket
