from nurb import *


@part
def leg_cup():
    """Slip-over foot cup: the short bench leg drops into the pocket; the solid
    floor under it lifts the bench level.

    Pocket, walls, and height come from measured leg_width, leg_depth, and lift.
    """
    clearance = 0.4
    wall = 2.0
    pocket_depth = 8.0
    pocket_x = measured("leg_width") + clearance
    pocket_y = measured("leg_depth") + clearance
    lift = measured("lift")
    height = lift + pocket_depth
    outer = Pos(0, 0, height / 2) * Box(
        pocket_x + 2 * wall, pocket_y + 2 * wall, height
    )
    pocket = Pos(0, 0, lift + pocket_depth / 2) * Box(pocket_x, pocket_y, pocket_depth)
    return outer - pocket
