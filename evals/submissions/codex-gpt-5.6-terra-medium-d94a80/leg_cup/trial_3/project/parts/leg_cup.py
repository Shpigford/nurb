from nurb import *


@part
def leg_cup(draft=False):
    """A support-free, slip-over leveling cup for a rectangular workbench leg."""
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    wall_thickness = 2.0
    fit_clearance = 0.4
    pocket_depth = 8.0

    pocket_width = leg_width + fit_clearance
    pocket_depth_y = leg_depth + fit_clearance
    overall_width = pocket_width + 2 * wall_thickness
    overall_depth = pocket_depth_y + 2 * wall_thickness

    # Both boxes are located from the same outside corner.  The pocket begins at
    # the top of the solid lifting floor, leaving four full-height 2 mm walls.
    outer = Box(overall_width, overall_depth, lift + pocket_depth,
                align=(Align.MIN, Align.MIN, Align.MIN))
    pocket = Pos(wall_thickness, wall_thickness, lift) * Box(
        pocket_width, pocket_depth_y, pocket_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    return outer - pocket
