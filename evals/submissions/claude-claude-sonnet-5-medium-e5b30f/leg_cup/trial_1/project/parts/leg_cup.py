from nurb import *


@part
def leg_cup(leg_width=measured("leg_width"), leg_depth=measured("leg_depth"),
            lift=measured("lift"), wall=2.0, pocket_depth=8.0, draft=False):
    """
    leg_width: width of the bench leg's foot that drops into the pocket
    leg_depth: depth of the bench leg's foot that drops into the pocket
    lift: how much solid floor raises this leg to stop the wobble
    wall: thickness of the four walls around the pocket
    pocket_depth: how far down the pocket drops to swallow the leg's foot
    """
    pocket_w = leg_width + 0.4
    pocket_d = leg_depth + 0.4
    outer_w = pocket_w + 2 * wall
    outer_d = pocket_d + 2 * wall
    total_h = lift + pocket_depth

    body = Box(outer_w, outer_d, total_h)
    if draft:
        return body

    pocket = Box(pocket_w, pocket_d, pocket_depth)
    pocket = pocket.translate((0, 0, (total_h - pocket_depth) / 2))
    cup = body - pocket

    bed = cup.bounding_box().min.Z
    concave = concave_edges(cup)
    keep = cup.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed + 1e-6 and e not in concave
    )
    return polish(cup, keep, 1.0)
