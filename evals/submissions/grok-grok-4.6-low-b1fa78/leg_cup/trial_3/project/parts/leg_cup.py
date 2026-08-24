from nurb import *


@part
def leg_cup(draft=False):
    """Slip-over cup that lifts a short workbench leg until the bench sits level.

    Geometry is driven only by measured leg_width, leg_depth, and lift.
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")
    clearance = 0.4
    wall = 2.0
    pocket_depth = 8.0
    pocket_w = leg_width + clearance
    pocket_d = leg_depth + clearance
    outer_w = pocket_w + 2.0 * wall
    outer_d = pocket_d + 2.0 * wall
    height = lift + pocket_depth
    body = Box(outer_w, outer_d, height).moved(Location((0, 0, height / 2.0)))
    cavity = Box(pocket_w, pocket_d, pocket_depth + 1.0).moved(
        Location((0, 0, lift + (pocket_depth + 1.0) / 2.0))
    )
    cup = body - cavity
    if draft:
        return cup
    return cup
