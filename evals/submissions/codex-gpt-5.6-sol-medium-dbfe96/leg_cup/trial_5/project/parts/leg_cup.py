from nurb import *


@part
def leg_cup():
    """A slip-over cup that raises the short workbench leg."""
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    fit_clearance = 0.4
    wall_thickness = 2.0
    pocket_height = 8.0

    pocket_width = leg_width + fit_clearance
    pocket_depth = leg_depth + fit_clearance
    outer_width = pocket_width + 2.0 * wall_thickness
    outer_depth = pocket_depth + 2.0 * wall_thickness
    outer_height = lift + pocket_height

    outer = Box(
        outer_width,
        outer_depth,
        outer_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    pocket = Pos(0, 0, lift) * Box(
        pocket_width,
        pocket_depth,
        pocket_height + 0.1,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return outer - pocket
