from nurb import *


@part
def leg_cup(draft=False):
    """Slip-over foot cup that levels a short rectangular workbench leg.

    The pocket and floor sizes come from measurements.toml only:
    leg_width and leg_depth size the pocket, lift is the solid floor thickness.
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")
    wall = 2.0
    pocket_depth = 8.0
    pocket_w = leg_width + 0.4
    pocket_d = leg_depth + 0.4
    outer_w = pocket_w + 2.0 * wall
    outer_d = pocket_d + 2.0 * wall
    outer_h = lift + pocket_depth

    body = Box(outer_w, outer_d, outer_h)
    cavity = Box(pocket_w, pocket_d, pocket_depth).move(Location((0, 0, lift / 2.0)))
    return body - cavity
