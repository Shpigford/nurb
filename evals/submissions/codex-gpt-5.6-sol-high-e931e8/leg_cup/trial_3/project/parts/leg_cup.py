from nurb import *


@part
def leg_cup(draft=False):
    """A slip-over cup that raises the short workbench leg.

    lift: the solid thickness below the leg that levels the bench
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    clearance = 0.4
    wall = 2.0
    pocket_depth = 8.0

    pocket_width = leg_width + clearance
    pocket_depth_width = leg_depth + clearance
    outer_width = pocket_width + 2.0 * wall
    outer_depth = pocket_depth_width + 2.0 * wall

    on_bed = (Align.CENTER, Align.CENTER, Align.MIN)
    body = Box(
        outer_width,
        outer_depth,
        lift + pocket_depth,
        align=on_bed,
    )
    pocket = Pos(0, 0, lift) * Box(
        pocket_width,
        pocket_depth_width,
        pocket_depth,
        align=on_bed,
    )
    return body - pocket
