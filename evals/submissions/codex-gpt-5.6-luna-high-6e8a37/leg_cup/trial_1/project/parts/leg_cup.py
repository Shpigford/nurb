from nurb import *


@part
def leg_cup():
    """Slip-over foot cup for levelling a rectangular workbench leg.

    The pocket is sized from the measured leg with 0.4 mm total clearance.
    The floor lift remains provisional until the bench can be measured.
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    wall = 2.0
    pocket_depth = 8.0
    pocket_width = leg_width + 0.4
    pocket_depth_xy = leg_depth + 0.4

    outside = Box(
        pocket_width + 2.0 * wall,
        pocket_depth_xy + 2.0 * wall,
        lift + pocket_depth,
    )
    # Box is centered on its local origin.  Center the pocket in X/Y and place
    # its 8 mm cutter so its bottom is exactly lift above the outer bottom.
    pocket = Pos(0, 0, lift / 2.0) * Box(
        pocket_width,
        pocket_depth_xy,
        pocket_depth,
    )
    return outside - pocket
