from nurb import *

SEATED = (Align.CENTER, Align.CENTER, Align.MIN)


@part
def leg_cup(clearance=0.4, wall=2.0, pocket_depth=8.0, draft=False):
    """clearance: extra room around the leg so it drops into the pocket
    wall: thickness of the cup's walls and rim
    pocket_depth: how far the leg's foot sinks into the pocket
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    pocket_w = leg_width + clearance
    pocket_d = leg_depth + clearance
    outer_w = pocket_w + 2 * wall
    outer_d = pocket_d + 2 * wall
    total_h = lift + pocket_depth

    body = Box(outer_w, outer_d, total_h, align=SEATED)
    if draft:
        return body

    pocket = Pos(0, 0, lift) * Box(pocket_w, pocket_d, pocket_depth, align=SEATED)
    cup = body - pocket

    bed = cup.bounding_box().min.Z
    top = cup.bounding_box().max.Z
    concave = set(concave_edges(cup))

    def flat_in(e, z):
        box = e.bounding_box()
        return box.min.Z == z and box.max.Z == z

    # Only the four outer vertical corners are chamfered: leaving the top and
    # bottom perimeters sharp keeps three convex edges from ever meeting at one
    # vertex, which is what mints the corner-triangle sliver.
    keep = cup.edges().filter_by(
        lambda e: e not in concave and not flat_in(e, bed) and not flat_in(e, top)
    )
    return polish(cup, keep, 1.0)
