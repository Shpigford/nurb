from nurb import *


@part
def leg_cup(clearance=0.4, wall=2.0, pocket_depth=8.0, draft=False):
    """
    clearance: extra room in the pocket around the leg's cross-section
    wall: how thick the cup's sides are around the pocket
    pocket_depth: how far the leg's foot sinks into the pocket
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    inner_width = leg_width + clearance
    inner_depth = leg_depth + clearance
    outer_width = inner_width + 2 * wall
    outer_depth = inner_depth + 2 * wall
    height = lift + pocket_depth

    body = Box(outer_width, outer_depth, height)
    pocket = Pos(0, 0, height / 2 - pocket_depth / 2) * Box(
        inner_width, inner_depth, pocket_depth
    )
    body = body - pocket

    if draft:
        return body

    bed = body.bounding_box().min.Z
    concave = concave_edges(body)
    keep = body.edges().filter_by(lambda e: e.bounding_box().min.Z > bed)
    keep = keep.filter_by(lambda e: e not in concave)
    return polish(body, keep, 1.0)
