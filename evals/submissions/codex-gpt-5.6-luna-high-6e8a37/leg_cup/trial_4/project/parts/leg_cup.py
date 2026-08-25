from nurb import *


@part
def leg_cup(draft=False):
    """Slip-over cup for a rectangular workbench leg.

    The pocket is sized from the measured leg with 0.2 mm clearance per side;
    lift is the solid floor thickness that raises the bench.
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    wall = 2.0
    pocket_depth = 8.0
    total_height = lift + pocket_depth
    outer = Pos(0, 0, total_height / 2.0) * Box(
        leg_width + 0.4 + 2.0 * wall,
        leg_depth + 0.4 + 2.0 * wall,
        total_height,
    )
    pocket = Pos(0, 0, lift + pocket_depth / 2.0) * Box(
        leg_width + 0.4,
        leg_depth + 0.4,
        pocket_depth,
    )
    return outer - pocket
