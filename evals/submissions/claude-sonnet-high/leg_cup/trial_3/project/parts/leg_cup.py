from nurb import *


@part
def leg_cup(
    leg_width=measured("leg_width"),
    leg_depth=measured("leg_depth"),
    lift=measured("lift"),
    wall=2.0,
    pocket_height=8.0,
    draft=False,
):
    """
    leg_width: width of the bench leg's foot that has to drop into the pocket
    leg_depth: depth of the bench leg's foot that has to drop into the pocket
    lift: how much the cup raises the short leg to level the bench
    wall: thickness of the four walls around the pocket
    pocket_height: how deep the pocket is, top rim down to the floor
    """
    pocket_width = leg_width + 0.4
    pocket_depth = leg_depth + 0.4
    outer_width = pocket_width + 2 * wall
    outer_depth = pocket_depth + 2 * wall
    total_height = lift + pocket_height

    outer = Box(
        outer_width,
        outer_depth,
        total_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    pocket = Box(
        pocket_width,
        pocket_depth,
        pocket_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).translate((0, 0, lift))

    body = outer - pocket

    if draft:
        return body

    bed = body.bounding_box().min.Z
    concave = concave_edges(body)
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed and e not in concave
    )
    return polish(body, keep, 1.0)
