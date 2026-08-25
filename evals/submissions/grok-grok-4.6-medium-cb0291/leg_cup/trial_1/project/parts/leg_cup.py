from nurb import *


@part
def leg_cup(draft=False):
    """Slip-over foot cup that lifts a short workbench leg level.

    The leg drops into an open rectangular pocket from above. A solid floor
    under the foot is `lift` thick; walls are 2 mm and the pocket is 8 mm
    deep, with 0.4 mm of slip clearance around the measured leg.

    lift: thickness of the solid floor that raises the short leg
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    clearance = 0.4
    pocket_depth = 8.0
    wall = 2.0

    pocket_w = leg_width + clearance
    pocket_d = leg_depth + clearance
    outer_w = pocket_w + 2.0 * wall
    outer_d = pocket_d + 2.0 * wall
    height = lift + pocket_depth

    body = Box(outer_w, outer_d, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # Cut slightly through the rim so the pocket opens straight up.
    pocket = Box(
        pocket_w,
        pocket_d,
        pocket_depth + 0.2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).moved(Location((0, 0, lift)))
    cup = body - pocket
    # Pocket size, wall thickness and floor thickness are fit-critical.
    # Chamfering the 2 mm rim leaves sliver faces, so leave the cup square.
    return cup
