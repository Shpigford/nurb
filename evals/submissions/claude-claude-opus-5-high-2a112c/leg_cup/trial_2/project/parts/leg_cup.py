from nurb import *


@part
def leg_cup(
    lift=measured("lift"),
    pocket_depth=8.0,
    wall_thickness=2.0,
    leg_slack=0.4,
    corner_chamfer=1.0,
    draft=False,
):
    """A cup the short bench leg drops into, lifting it until the bench stops rocking.

    lift: how far the cup raises the leg off the floor, the solid floor under the foot
    pocket_depth: how deep the leg sits in the cup before it bottoms out
    wall_thickness: how thick the four walls around the leg are
    leg_slack: how much wider than the leg the pocket is, so the foot drops in
    corner_chamfer: how much is taken off the four outside corners
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")

    if lift <= 0:
        reject(
            f"lift {lift:g} leaves no floor under the foot, so the cup would be a "
            f"bottomless sleeve: raise it above 0",
            param="lift",
        )

    pocket_width = leg_width + leg_slack
    pocket_length = leg_depth + leg_slack
    outer_width = pocket_width + 2 * wall_thickness
    outer_length = pocket_length + 2 * wall_thickness

    up_from_bed = (Align.CENTER, Align.CENTER, Align.MIN)
    body = Box(outer_width, outer_length, lift + pocket_depth, align=up_from_bed)
    # The cut runs past the rim rather than stopping flush on it: a coincident face is
    # work the kernel does not need, and the pocket is still exactly `pocket_depth`
    # deep because its floor sits at `lift` and the rim is where the body ends.
    pocket = Pos(0, 0, lift) * Box(
        pocket_width, pocket_length, pocket_depth + 1.0, align=up_from_bed
    )
    cup = body - pocket

    if draft:
        return cup
    # Only the four outside corners. The rim stays square, because a chamfer there
    # eats the wall the leg leans on and a lead-in inside the pocket is polish laid
    # on mating geometry; a vertical corner's chamfer stands square to the plate and
    # costs the first layer nothing.
    inner_reach = max(pocket_width, pocket_length) / 2
    corners = cup.edges().filter_by(Axis.Z).filter_by(
        lambda e: abs(e.bounding_box().center().X) > inner_reach
        or abs(e.bounding_box().center().Y) > inner_reach
    )
    return polish(cup, corners, corner_chamfer)
