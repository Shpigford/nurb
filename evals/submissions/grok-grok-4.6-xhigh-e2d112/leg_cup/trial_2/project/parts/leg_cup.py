from nurb import *


@part
def leg_cup(draft=False):
    """Slip-over cup that lifts a short workbench leg level.

    The pocket is the measured leg plus 0.4 mm of slip clearance, 8 mm deep,
    with 2 mm walls. Floor thickness is lift, still a guess until the bench
    can be measured.
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    slip = 0.4
    wall = 2.0
    pocket_depth = 8.0

    pocket_w = leg_width + slip
    pocket_d = leg_depth + slip
    outer_w = pocket_w + 2 * wall
    outer_d = pocket_d + 2 * wall
    height = lift + pocket_depth

    body = Box(outer_w, outer_d, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # Pocket cutter sticks 1 mm past the rim so the opening is not roofed over.
    pocket = Location((0, 0, lift)) * Box(
        pocket_w,
        pocket_d,
        pocket_depth + 1.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return body - pocket
