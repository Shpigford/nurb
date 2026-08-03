from nurb import *


@part
def leg_cup(draft=False):
    """Slip-over workbench foot cup.

    leg_width: measured width of the rectangular bench leg
    leg_depth: measured depth of the rectangular bench leg
    lift: solid floor thickness that levels the short leg
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    pocket_clearance = 0.4
    wall_thickness = 2.0
    pocket_depth = 8.0

    pocket_width = leg_width + pocket_clearance
    pocket_depth_width = leg_depth + pocket_clearance
    outer_width = pocket_width + wall_thickness * 2.0
    outer_depth = pocket_depth_width + wall_thickness * 2.0
    total_height = lift + pocket_depth

    body = Box(
        outer_width,
        outer_depth,
        total_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    pocket = Pos(0, 0, lift) * Box(
        pocket_width,
        pocket_depth_width,
        pocket_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    return body - pocket
