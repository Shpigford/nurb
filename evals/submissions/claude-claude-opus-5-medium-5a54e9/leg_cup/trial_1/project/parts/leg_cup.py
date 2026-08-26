from nurb import *


@part
def leg_cup(
    leg_width=measured("leg_width"),
    leg_depth=measured("leg_depth"),
    lift=measured("lift"),
    foot_clearance=0.4,
    wall_thickness=2.0,
    pocket_depth=8.0,
    draft=False,
):
    """A cup the bench's short leg drops into, lifting it level.

    leg_width: how wide the bench leg is, across the short side
    leg_depth: how deep the bench leg is, along the other side
    lift: how far the cup raises the leg off the floor
    foot_clearance: slack around the leg so the foot slides in
    wall_thickness: how thick the four walls around the leg are
    pocket_depth: how far the leg drops into the cup
    """
    pocket_width = leg_width + foot_clearance
    pocket_length = leg_depth + foot_clearance
    outer_width = pocket_width + 2 * wall_thickness
    outer_length = pocket_length + 2 * wall_thickness
    height = lift + pocket_depth

    if wall_thickness <= 0 or pocket_depth <= 0 or lift <= 0:
        reject("the cup needs walls, a pocket and a floor with real thickness")

    body = Box(outer_width, outer_length, height)
    # The pocket opens straight up: its roof is the rim, so nothing bridges it.
    pocket = Pos(0, 0, height / 2 - pocket_depth / 2) * Box(
        pocket_width, pocket_length, pocket_depth
    )
    body = body - pocket

    if draft:
        return body

    # Chamfer the outside only. A lead-in on the pocket rim would eat into the
    # 2mm wall and widen the mouth the leg is meant to sit snug in.
    box = body.bounding_box()
    bed = box.min.Z
    outer = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed + 1e-6
        and (
            e.bounding_box().max.X > outer_width / 2 - 1e-6
            or e.bounding_box().max.Y > outer_length / 2 - 1e-6
        )
    )
    return polish(body, outer, 1.0)
