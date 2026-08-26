from nurb import *


@part
def leg_cup(
    leg_width=measured("leg_width"),
    leg_depth=measured("leg_depth"),
    lift=measured("lift"),
    pocket_slack=0.4,
    wall_thickness=2.0,
    pocket_depth=8.0,
    chamfer_size=1.2,
    draft=False,
):
    """A slip-over foot cup: the bench leg drops in from above and the solid floor lifts it.

    leg_width: the wide side of the bench leg's rectangular section
    leg_depth: the narrow side of the bench leg's rectangular section
    lift: how much the solid floor raises the short leg to kill the wobble
    pocket_slack: total slack across the pocket, so the leg drops in without forcing
    wall_thickness: how thick the four walls around the leg are
    pocket_depth: how far the leg sinks into the cup
    chamfer_size: the size of the chamfer on the outside edges and the rim
    """
    pocket_w = leg_width + pocket_slack
    pocket_d = leg_depth + pocket_slack
    outer_w = pocket_w + 2 * wall_thickness
    outer_d = pocket_d + 2 * wall_thickness
    height = lift + pocket_depth

    body = Box(outer_w, outer_d, height)
    top = body.bounding_box().max.Z

    # The pocket opens straight up. The cutter runs past the rim so the mouth is open,
    # and its floor sits exactly pocket_depth below the rim, leaving `lift` of solid.
    overshoot = 1.0
    cutter = Pos(0, 0, top + overshoot - (pocket_depth + overshoot) / 2) * Box(
        pocket_w, pocket_d, pocket_depth + overshoot
    )
    cup = body - cutter

    if draft:
        return cup

    bed = cup.bounding_box().min.Z
    tol = 1e-6

    def outside(edge):
        box = edge.bounding_box()
        # Nothing inside the pocket: it is mating geometry, and a lead-in chamfer at a
        # socket mouth is exactly what rule 3 forbids.
        if (
            -pocket_w / 2 - tol <= box.min.X
            and box.max.X <= pocket_w / 2 + tol
            and -pocket_d / 2 - tol <= box.min.Y
            and box.max.Y <= pocket_d / 2 + tol
        ):
            return False
        # An edge lying in the bed-contact face buys nothing; one that merely ends there
        # (the vertical corners) keeps its chamfer.
        return box.max.Z > bed + tol

    keep = cup.edges().filter_by(outside)
    return polish(cup, keep, chamfer_size)
