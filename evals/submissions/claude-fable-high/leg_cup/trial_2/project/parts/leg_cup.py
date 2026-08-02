from nurb import *


@part
def leg_cup(wall_thickness=2.0, pocket_depth=8.0, foot_clearance=0.4, draft=False):
    """A slip-over cup that lifts the workbench's short leg level.

    wall_thickness: how thick the cup wall is around the leg
    pocket_depth: how far the leg's foot drops into the cup
    foot_clearance: extra room around the foot so it slips on easily
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    pocket_width = leg_width + foot_clearance
    pocket_length = leg_depth + foot_clearance
    outer_width = pocket_width + 2 * wall_thickness
    outer_length = pocket_length + 2 * wall_thickness
    height = lift + pocket_depth

    body = Pos(0, 0, height / 2) * Box(outer_width, outer_length, height)
    pocket = Pos(0, 0, lift + pocket_depth / 2) * Box(
        pocket_width, pocket_length, pocket_depth
    )
    cup = body - pocket

    if draft:
        return cup

    # Only the four outer corners take a chamfer. The pocket mouth is mating
    # geometry and stays sharp, and the 2mm rim beside it cannot host a 1mm
    # chamfer: it would leave exactly the 1.0mm of face where the kernel fails.
    keep = cup.edges().filter_by(Axis.Z).filter_by(
        lambda e: abs(e.bounding_box().max.X) > pocket_width / 2
    )
    return polish(cup, keep, 1.0)
