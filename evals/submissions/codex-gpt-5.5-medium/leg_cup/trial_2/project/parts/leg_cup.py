from nurb import *


@part
def leg_cup(draft=False):
    """
    lift: solid floor thickness that raises the short workbench leg.
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    pocket_width = leg_width + 0.4
    pocket_depth = leg_depth + 0.4
    wall_thickness = 2.0
    pocket_height = 8.0

    outside_width = pocket_width + wall_thickness * 2.0
    outside_depth = pocket_depth + wall_thickness * 2.0
    total_height = lift + pocket_height

    body = Box(
        outside_width,
        outside_depth,
        total_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    pocket_cut = Pos(0, 0, lift + pocket_height / 2.0) * Box(
        pocket_width,
        pocket_depth,
        pocket_height,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )

    return body - pocket_cut
