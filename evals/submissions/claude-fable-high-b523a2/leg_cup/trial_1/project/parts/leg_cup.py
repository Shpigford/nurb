from nurb import *


@part
def leg_cup(wall_thickness=2.0, pocket_depth=8.0, leg_clearance=0.4, draft=False):
    """A slip-over cup for the workbench's short leg: the foot drops into the
    pocket from above and the solid floor lifts the bench level.

    wall_thickness: how thick the cup's four walls are
    pocket_depth: how deep the leg sits inside the cup
    leg_clearance: extra room in the pocket so the leg drops in without forcing
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    pocket_width = leg_width + leg_clearance
    pocket_length = leg_depth + leg_clearance
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

    # The pocket is the fit and the bottom is the bed, so only the four outer
    # vertical corners get the chamfer; adding the rim's outer edge would leave
    # sliver corner faces where three chamfers meet.
    eps = 1e-6

    def outer_vertical_corner(e):
        bb = e.bounding_box()
        on_x = bb.max.X > outer_width / 2 - eps or bb.min.X < -outer_width / 2 + eps
        on_y = bb.max.Y > outer_length / 2 - eps or bb.min.Y < -outer_length / 2 + eps
        return on_x and on_y and bb.max.Z - bb.min.Z > eps

    keep = cup.edges().filter_by(outer_vertical_corner)
    return polish(cup, keep, 1.0)
