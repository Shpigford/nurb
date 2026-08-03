from nurb import *


@part
def leg_cup(pocket_gap=0.4, pocket_depth=8.0, wall_thickness=2.0, draft=False):
    """A slip-over foot cup: the bench leg drops in from above and the solid floor lifts it level.

    pocket_gap: how much wider than the leg the pocket is, so the foot slides in
    pocket_depth: how far the leg drops into the cup
    wall_thickness: how thick the four walls around the leg are
    """
    floor_thickness = measured("lift")
    pocket_width = measured("leg_width") + pocket_gap
    pocket_depth_across = measured("leg_depth") + pocket_gap

    outer_width = pocket_width + 2 * wall_thickness
    outer_depth = pocket_depth_across + 2 * wall_thickness
    total_height = floor_thickness + pocket_depth

    body = Pos(0, 0, total_height / 2) * Box(outer_width, outer_depth, total_height)

    # Cut from the floor clear through the rim, so the pocket depth is the floor's
    # doing and no coplanar top faces meet in the boolean.
    overshoot = 1.0
    cutter = Pos(0, 0, floor_thickness + (pocket_depth + overshoot) / 2) * Box(
        pocket_width, pocket_depth_across, pocket_depth + overshoot
    )
    cup = body - cutter

    if draft:
        return cup

    # The four outer corners only. The bottom edges lie in the bed face, and the rim's
    # outer edge would leave 1mm of rim between the chamfer and the mouth the leg has to
    # slide through: below what a 1mm chamfer needs to land, and a lead-in at a mating
    # mouth besides.
    bed = cup.bounding_box().min.Z
    corners = (
        cup.edges()
        .filter_by(Axis.Z)
        .filter_by(lambda e: e.bounding_box().min.Z < bed + 1e-6)
    )
    return polish(cup, corners, 1.0)
