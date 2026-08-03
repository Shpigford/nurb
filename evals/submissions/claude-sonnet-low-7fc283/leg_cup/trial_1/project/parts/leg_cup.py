from nurb import *


@part
def leg_cup(clearance=0.4, wall=2.0, pocket_depth=8.0, draft=False):
    """
    clearance: how much bigger the pocket is than the leg, all around
    wall: how thick the cup's walls and rim are
    pocket_depth: how far down the leg's foot drops into the pocket
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    pocket_width = leg_width + clearance
    pocket_length = leg_depth + clearance

    outer_width = pocket_width + 2 * wall
    outer_length = pocket_length + 2 * wall
    outer_height = lift + pocket_depth

    body = Box(outer_width, outer_length, outer_height)
    pocket = Box(pocket_width, pocket_length, pocket_depth)
    pocket = Pos(0, 0, outer_height / 2 - pocket_depth / 2) * pocket
    body = body - pocket

    if draft:
        return body

    concave = concave_edges(body)
    bed = body.bounding_box().min.Z
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed and e not in concave
    )
    return polish(body, keep, 1.0)
