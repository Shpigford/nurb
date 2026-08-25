from nurb import *


@part
def leg_cup(draft=False):
    """Slip-over cup that lifts a short rectangular workbench leg level.

    The pocket is a straight drop-in for the measured leg plus 0.4 mm of slip.
    Floor thickness is the unmeasured lift from measurements.toml.
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    wall = 2.0
    slip = 0.4
    pocket_depth = 8.0

    pocket_w = leg_width + slip
    pocket_d = leg_depth + slip
    outer_w = pocket_w + 2 * wall
    outer_d = pocket_d + 2 * wall
    height = lift + pocket_depth

    body = Box(outer_w, outer_d, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # Overcut the open top so the kernel cannot leave a film roofing the pocket.
    cutter = Box(
        pocket_w,
        pocket_d,
        pocket_depth + 1.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    cutter = cutter.move(Location((0, 0, lift)))
    cup = body - cutter
    if draft:
        return cup
    # Mating socket: no polish. A rim chamfer would change the pocket mouth and
    # the 2 mm walls; a bed chamfer would cut first-layer grip.
    return cup
