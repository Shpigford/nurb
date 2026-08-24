from nurb import *


@part
def leg_cup():
    """Slip-over cup that lifts a short workbench leg level.

    lift: how much the solid floor under the pocket raises the foot
    """
    wall = 2.0
    clearance = 0.4
    pocket_depth = 8.0

    inner_w = measured("leg_width") + clearance
    inner_d = measured("leg_depth") + clearance
    lift = measured("lift")

    outer_w = inner_w + 2.0 * wall
    outer_d = inner_d + 2.0 * wall
    height = lift + pocket_depth

    body = Box(outer_w, outer_d, height)
    body = Location((0, 0, height / 2.0)) * body
    pocket = Box(inner_w, inner_d, pocket_depth)
    pocket = Location((0, 0, lift + pocket_depth / 2.0)) * pocket
    return body - pocket
