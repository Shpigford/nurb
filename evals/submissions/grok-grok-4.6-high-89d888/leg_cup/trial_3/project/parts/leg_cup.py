from nurb import *


@part
def leg_cup(draft=False):
    """Slip-over cup that lifts a short workbench leg level.

    The leg drops into the pocket from above; the solid floor under the foot is the lift.
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    wall = 2.0
    pocket_depth = 8.0
    clearance = 0.4

    pocket_w = leg_width + clearance
    pocket_d = leg_depth + clearance
    outer_w = pocket_w + 2 * wall
    outer_d = pocket_d + 2 * wall
    outer_h = lift + pocket_depth

    body = Box(outer_w, outer_d, outer_h, align=(Align.MIN, Align.MIN, Align.MIN))
    # Overcut the pocket past the rim so the top is open, not a coplanar cap.
    pocket = Box(
        pocket_w,
        pocket_d,
        pocket_depth + 1.0,
        align=(Align.MIN, Align.MIN, Align.MIN),
    ).moved(Location((wall, wall, lift)))
    return body - pocket
