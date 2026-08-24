from nurb import *


@part
def leg_cup(leg_clearance=0.4, wall_thickness=2.0, pocket_depth=8.0, draft=False):
    """A slip-over foot cup for the workbench's short leg: the cup sits on the
    floor, the leg's foot drops into the pocket from above, and the solid floor
    under the foot lifts the bench level.

    leg_clearance: total extra pocket width so the leg drops in without forcing
    wall_thickness: how thick the cup's four walls are
    pocket_depth: how far the leg's foot sits down inside the cup
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    if lift < 1.0:
        reject(
            "lift %.1f leaves the floor under the leg too thin to print sound: "
            "raise it to at least 1.0" % lift
        )

    inner_x = leg_width + leg_clearance
    inner_y = leg_depth + leg_clearance
    outer_x = inner_x + 2 * wall_thickness
    outer_y = inner_y + 2 * wall_thickness
    height = lift + pocket_depth

    body = Box(outer_x, outer_y, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    pocket = Pos(0, 0, lift) * Box(
        inner_x, inner_y, pocket_depth, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    cup = body - pocket

    if draft:
        return cup

    # Polish only the outer rim: the pocket is fit-critical mating geometry and
    # stays sharp, bed-touching edges stay sharp, and stopping the chamfer set
    # at the rim leaves no three-chamfer corner triangles to sliver.
    def outer_exposed(e):
        bb = e.bounding_box()
        on_outer = (
            max(abs(bb.min.X), abs(bb.max.X)) > outer_x / 2 - 0.1
            or max(abs(bb.min.Y), abs(bb.max.Y)) > outer_y / 2 - 0.1
        )
        return on_outer and bb.min.Z > 0.1

    keep = cup.edges().filter_by(outer_exposed)
    return polish(cup, keep, 1.0)
