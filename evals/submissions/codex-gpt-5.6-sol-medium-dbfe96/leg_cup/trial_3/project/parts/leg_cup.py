from nurb import *


@part
def leg_cup(draft=False):
    """A slip-over cup that raises the short workbench leg.

    draft: runtime switch; this exact-fit part has no separate polish geometry.
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    clearance = 0.4
    wall = 2.0
    pocket_depth = 8.0

    pocket_width = leg_width + clearance
    pocket_depth_y = leg_depth + clearance
    outer_width = pocket_width + 2.0 * wall
    outer_depth = pocket_depth_y + 2.0 * wall

    bottom_aligned = (Align.CENTER, Align.CENTER, Align.MIN)
    body = Box(
        outer_width,
        outer_depth,
        lift + pocket_depth,
        align=bottom_aligned,
    )
    # Extend the cutter above the body so the pocket is unequivocally open while
    # its bottom remains exactly at z=lift.
    pocket = Pos(0, 0, lift) * Box(
        pocket_width,
        pocket_depth_y,
        pocket_depth + 1.0,
        align=bottom_aligned,
    )
    return body - pocket
