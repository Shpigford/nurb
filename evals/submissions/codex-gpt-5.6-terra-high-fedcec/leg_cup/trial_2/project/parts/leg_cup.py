from nurb import *


@part
def leg_cup(draft=False):
    """A slip-over leveling cup for a rectangular workbench leg.

    draft: retained for the standard part interface; this dimension-critical cup has no polish pass.
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    wall_thickness = 2.0
    fit_clearance = 0.4
    pocket_depth = 8.0

    pocket_width = leg_width + fit_clearance
    pocket_length = leg_depth + fit_clearance
    outer_width = pocket_width + 2.0 * wall_thickness
    outer_length = pocket_length + 2.0 * wall_thickness

    outer = Box(
        outer_width,
        outer_length,
        lift + pocket_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    pocket = Pos(wall_thickness, wall_thickness, lift) * Box(
        pocket_width,
        pocket_length,
        pocket_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    return outer - pocket
