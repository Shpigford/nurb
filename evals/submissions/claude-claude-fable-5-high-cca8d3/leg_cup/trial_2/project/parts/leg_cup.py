from nurb import *


@part
def leg_cup(leg_clearance=0.4, wall_thickness=2.0, pocket_depth=8.0, draft=False):
    """A slip-over foot cup for the workbench's short leg: the foot drops into
    the pocket from above and the solid floor lifts the bench level.

    leg_clearance: extra room in the pocket so the leg drops in by hand
    wall_thickness: how thick the cup's four walls are
    pocket_depth: how far down the leg's foot sits inside the cup
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    if lift <= 0:
        reject("lift must be positive: the solid floor under the foot is what levels the bench")

    pocket_width = leg_width + leg_clearance
    pocket_length = leg_depth + leg_clearance
    outer_width = pocket_width + 2 * wall_thickness
    outer_length = pocket_length + 2 * wall_thickness
    height = lift + pocket_depth

    body = Pos(0, 0, height / 2) * Box(outer_width, outer_length, height)
    # Cut past the rim so the pocket opens cleanly instead of a coplanar top face.
    pocket = Pos(0, 0, lift + (pocket_depth + 1) / 2) * Box(
        pocket_width, pocket_length, pocket_depth + 1
    )
    body = body - pocket

    if draft:
        return body

    # Polish only the four vertical outer corners. The pocket is fit-critical
    # mating geometry, so no lead-in chamfer at its mouth and nothing inside it;
    # the outer rim stays sharp too, because a rim chamfer meeting the corner
    # chamfers caps each corner with a sub-mm2 sliver face.
    def outer_vertical_corner(e):
        bb = e.bounding_box()
        x_reach = max(abs(bb.min.X), abs(bb.max.X))
        y_reach = max(abs(bb.min.Y), abs(bb.max.Y))
        return (
            x_reach >= outer_width / 2 - 1e-6
            and y_reach >= outer_length / 2 - 1e-6
            and bb.max.Z > bb.min.Z + 1e-6
        )

    keep = body.edges().filter_by(outer_vertical_corner)
    return polish(body, keep, 1.0)
