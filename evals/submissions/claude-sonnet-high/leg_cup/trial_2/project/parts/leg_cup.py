from nurb import *


@part
def leg_cup(wall=2.0, clearance=0.4, pocket_depth=8.0, draft=False):
    """A slip-over cup that drops under a short bench leg to level the bench.

    wall: how thick the pocket walls are on all four sides.
    clearance: how loose the pocket is so the leg slips in and out.
    pocket_depth: how far the leg's foot drops down into the pocket.
    """
    pocket_x = measured("leg_width") + clearance
    pocket_y = measured("leg_depth") + clearance
    lift = measured("lift")
    height = lift + pocket_depth

    outer = Pos(0, 0, height / 2) * Box(pocket_x + 2 * wall, pocket_y + 2 * wall, height)
    pocket = Pos(0, 0, lift + pocket_depth / 2) * Box(pocket_x, pocket_y, pocket_depth)
    cup = outer - pocket

    if draft:
        return cup

    # Chamfer only the outer top rim: edges that lie in the top plane and reach the
    # outer wall. Leaving the vertical outer corners alone keeps each rim corner a
    # plain two-edge miter instead of the three-edge convex corner that leaves a
    # sliver triangle. The pocket's own rim is a mating mouth (doctrine: never
    # lead-in-chamfer a socket) and is left untouched, along with the bed face and
    # the concave floor-to-wall and pocket-corner junctions.
    bb = cup.bounding_box()
    concave = concave_edges(cup)

    def on_top(e):
        eb = e.bounding_box()
        return abs(eb.min.Z - bb.max.Z) < 1e-6 and abs(eb.max.Z - bb.max.Z) < 1e-6

    def reaches_outer(e):
        eb = e.bounding_box()
        return (
            abs(eb.min.X - bb.min.X) < 1e-6
            or abs(eb.max.X - bb.max.X) < 1e-6
            or abs(eb.min.Y - bb.min.Y) < 1e-6
            or abs(eb.max.Y - bb.max.Y) < 1e-6
        )

    keep = cup.edges().filter_by(on_top)
    keep = keep.filter_by(reaches_outer)
    keep = keep.filter_by(lambda e: e not in concave)
    return polish(cup, keep, 1.0)
