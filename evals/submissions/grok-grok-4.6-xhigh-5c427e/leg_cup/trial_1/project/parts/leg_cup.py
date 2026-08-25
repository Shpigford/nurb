from nurb import *


@part
def leg_cup(draft=False):
    """Slip-over foot cup that lifts a short workbench leg level.

    The leg drops into the pocket from above. The solid floor under the foot is
    the unmeasured lift that kills the wobble.

    Pocket inner size is the measured leg plus 0.4 mm of slip clearance. Walls
    are 2 mm and rise 8 mm to the rim. The floor is solid, lift thick, with
    no openings. Fit faces stay unchamfered: a lead-in would change the pocket.
    """
    wall = 2.0
    clearance = 0.4
    pocket_depth = 8.0

    pocket_width = measured("leg_width") + clearance
    pocket_depth_xy = measured("leg_depth") + clearance
    lift = measured("lift")

    outer_width = pocket_width + 2 * wall
    outer_depth = pocket_depth_xy + 2 * wall
    height = lift + pocket_depth

    seated = (Align.CENTER, Align.CENTER, Align.MIN)
    body = Box(outer_width, outer_depth, height, align=seated)
    # Overcut the open top so the pocket is a straight rectangular well.
    cutter = Pos(0, 0, lift) * Box(
        pocket_width, pocket_depth_xy, pocket_depth + 1.0, align=seated
    )
    return body - cutter
