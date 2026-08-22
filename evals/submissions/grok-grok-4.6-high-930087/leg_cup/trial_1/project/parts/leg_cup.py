from nurb import *


@part
def leg_cup(draft=False):
    """Slip-over foot cup that levels a short workbench leg.

    The cup sits on the floor. The leg drops into the pocket from above,
    and the solid floor under the foot is the lift.

    lift: how far the cup raises the short leg; read from measurements
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
    height = lift + pocket_depth

    body = Box(outer_w, outer_d, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # Overcut the open top so the pocket has no roof; floor stays at z=lift.
    pocket = Box(
        pocket_w,
        pocket_d,
        pocket_depth + 1.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).moved(Location((0, 0, lift)))

    if draft:
        return body - pocket
    # Outer top rim only: polish the blank before the pocket is cut so the
    # 2 mm walls keep a flat 1 mm land and the pocket stays a rectangle.
    bed = body.bounding_box().min.Z
    keep = body.edges().filter_by(lambda e: e.bounding_box().min.Z > bed)
    return polish(body, keep, 1.0) - pocket
