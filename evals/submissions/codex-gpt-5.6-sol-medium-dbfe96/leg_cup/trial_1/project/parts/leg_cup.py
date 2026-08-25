from nurb import *


@part
def leg_cup(
    leg_width=measured("leg_width"),
    leg_depth=measured("leg_depth"),
    lift=measured("lift"),
):
    """A slip-over cup that raises the short workbench leg.

    leg_width: measured width of the rectangular bench leg
    leg_depth: measured depth of the rectangular bench leg
    lift: solid floor thickness that raises the short leg
    """
    clearance = 0.4
    wall_thickness = 2.0
    pocket_depth = 8.0

    pocket_width = leg_width + clearance
    pocket_depth_size = leg_depth + clearance
    outer_width = pocket_width + 2.0 * wall_thickness
    outer_depth = pocket_depth_size + 2.0 * wall_thickness

    build_up = (Align.CENTER, Align.CENTER, Align.MIN)
    body = Box(
        outer_width,
        outer_depth,
        lift + pocket_depth,
        align=build_up,
    )
    pocket = Pos(0, 0, lift) * Box(
        pocket_width,
        pocket_depth_size,
        pocket_depth + 0.1,
        align=build_up,
    )
    return body - pocket
