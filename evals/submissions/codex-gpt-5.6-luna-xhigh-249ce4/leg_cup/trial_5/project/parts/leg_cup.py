from nurb import *


@part
def leg_cup(draft=False):
    """Slip-over foot cup for the short workbench leg.

    leg_width: measured width of the rectangular leg
    leg_depth: measured depth of the rectangular leg
    lift: estimated floor thickness that raises the bench
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    wall = 2.0
    clearance = 0.4
    pocket_depth = 8.0
    pocket_width = leg_width + clearance
    pocket_depth_xy = leg_depth + clearance
    outside_width = pocket_width + 2.0 * wall
    outside_depth = pocket_depth_xy + 2.0 * wall

    outside = Box(
        outside_width,
        outside_depth,
        lift + pocket_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    pocket = Pos(wall, wall, lift) * Box(
        pocket_width,
        pocket_depth_xy,
        pocket_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    return outside - pocket
