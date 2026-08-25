from nurb import *


@part
def leg_cup(
    wall_thickness=2.0,
    pocket_depth=8.0,
    foot_clearance=0.4,
    chamfer_size=1.0,
    draft=False,
):
    """A cup the wobbly bench's short leg drops into, lifting it level.

    wall_thickness: how thick the four side walls are around the leg's foot
    pocket_depth: how far down into the cup the foot sits
    foot_clearance: extra room across the pocket so the foot slides on by hand
    chamfer_size: the bevel taken off the outside edges
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    pocket_width = leg_width + foot_clearance
    pocket_depth_across = leg_depth + foot_clearance
    outer_width = pocket_width + 2 * wall_thickness
    outer_depth = pocket_depth_across + 2 * wall_thickness
    height = lift + pocket_depth

    body = Pos(0, 0, height / 2) * Box(outer_width, outer_depth, height)

    # Open the pocket straight up. The cutter runs past the rim so the two top
    # faces never land coincident, which is where OCCT leaves a skin behind.
    overshoot = 1.0
    pocket = Pos(0, 0, lift + (pocket_depth + overshoot) / 2) * Box(
        pocket_width, pocket_depth_across, pocket_depth + overshoot
    )
    body = body - pocket

    if draft:
        return body

    # Polish the four outside vertical corners and nothing else. The pocket is
    # what the leg slides into, so its rim and its inside corners stay exactly
    # as modelled; the bed face gets no bevel; and the rim stays square because
    # a 2mm wall has no width to spare for one.
    bed = body.bounding_box().min.Z
    rim = body.bounding_box().max.Z
    concave = set(concave_edges(body))
    half_width = outer_width / 2
    half_depth = outer_depth / 2
    tol = 1e-6

    def outside_corner(e):
        if e in concave:
            return False
        box = e.bounding_box()
        if box.max.Z <= bed + tol:  # lies in the bed face
            return False
        if box.min.Z >= rim - tol:  # lies in the rim face
            return False
        on_perimeter = (
            box.max.X >= half_width - tol
            or box.min.X <= -half_width + tol
            or box.max.Y >= half_depth - tol
            or box.min.Y <= -half_depth + tol
        )
        return on_perimeter

    keep = body.edges().filter_by(outside_corner)
    return polish(body, keep, chamfer_size)
