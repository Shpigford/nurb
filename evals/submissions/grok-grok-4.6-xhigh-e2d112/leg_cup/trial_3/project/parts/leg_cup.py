from nurb import *


@part
def leg_cup(draft=False):
    """Slip-over foot cup that levels a short workbench leg.

    The pocket is the measured leg plus 0.4 mm of drop-in clearance. Walls
    are 2 mm on all four sides. The solid floor is lift thick so the short
    leg comes up level with the others.

    The rim is left square: the pocket is a mating opening, the walls are
    exactly 2 mm, and a 1 mm chamfer would thin the rim and shrink the
    first-layer grip for no fit benefit.
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    clearance = 0.4
    wall = 2.0
    pocket_depth = 8.0

    pocket_w = leg_width + clearance
    pocket_d = leg_depth + clearance
    outer_w = pocket_w + 2 * wall
    outer_d = pocket_d + 2 * wall
    height = lift + pocket_depth

    body = Pos(0, 0, height / 2) * Box(outer_w, outer_d, height)
    # Cutter overshoots the rim so the pocket opens straight up, no roof.
    cavity = Pos(0, 0, lift + (pocket_depth + 1.0) / 2) * Box(
        pocket_w, pocket_d, pocket_depth + 1.0
    )
    return body - cavity
