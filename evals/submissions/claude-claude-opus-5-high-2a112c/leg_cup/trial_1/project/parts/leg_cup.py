from nurb import *


@part
def leg_cup(wall=2.0, pocket_depth=8.0, leg_clearance=0.4, draft=False):
    """A slip-over cup that the short bench leg stands in, lifting it level.

    wall: how thick the sides of the cup are around the leg
    pocket_depth: how far down into the cup the leg's foot sits
    leg_clearance: extra room around the leg so the cup slips on by hand
    """
    # All three come off measurements.toml, so an edited number moves the part.
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    pocket_width = leg_width + leg_clearance
    pocket_length = leg_depth + leg_clearance
    outer_width = pocket_width + 2 * wall
    outer_length = pocket_length + 2 * wall
    height = lift + pocket_depth

    up = (Align.CENTER, Align.CENTER, Align.MIN)
    body = Box(outer_width, outer_length, height, align=up)
    # The pocket's ceiling is the body's own top face, so it opens straight up.
    pocket = Pos(0, 0, lift) * Box(pocket_width, pocket_length, pocket_depth, align=up)
    cup = body - pocket

    if draft:
        return cup

    # Only the four outside corners. The pocket mouth is a mating mouth and gets no
    # lead-in; the top rim would lose half the 2mm wall to a chamfer; the pocket's
    # inner corners are concave. Filter for those, then let `polish` do the rest.
    reach = pocket_width / 2 + wall / 2
    corners = cup.edges().filter_by(Axis.Z).filter_by(
        lambda e: abs(e.bounding_box().center().X) > reach
    )
    return polish(cup, corners, 1.0)
