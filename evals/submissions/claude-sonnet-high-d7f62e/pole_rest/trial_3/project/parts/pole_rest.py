from nurb import *

# The bench fixes this: every rest in the row holds the pole's axis at this
# height above the bed, centered in X over the rest's own footprint.
AXIS_Z = 18.0


@part
def pole_rest(
    pole_diameter=measured("pole_diameter"),
    rest_length=22.0,
    fit_clearance=0.2,
    cradle_wall=2.5,
    draft=False,
):
    """
    pole_diameter: diameter of the pole the rest cradles
    rest_length: how far the cradle runs along the pole
    fit_clearance: gap left between the cradle surface and the pole
    cradle_wall: material thickness behind the cradle, holding it up
    """
    if rest_length < 20.0:
        reject(
            f"rest_length {rest_length} is under the 20mm minimum span along the pole",
            param="rest_length",
        )
    if fit_clearance < 0.1:
        reject(
            f"fit_clearance {fit_clearance} is under the 0.1mm minimum fit clearance",
            param="fit_clearance",
        )
    if cradle_wall < 1.2:
        reject(
            f"cradle_wall {cradle_wall} is under the 1.2mm minimum backing behind the cradle",
            param="cradle_wall",
        )

    pole_radius = pole_diameter / 2.0
    groove_radius = pole_radius + fit_clearance
    outer_radius = groove_radius + cradle_wall
    width = 2 * outer_radius
    height = AXIS_Z

    block = Box(
        width,
        rest_length,
        height,
        align=(Align.CENTER, Align.MIN, Align.MIN),
    )
    groove = Pos(0, rest_length / 2, AXIS_Z) * Cylinder(
        groove_radius,
        rest_length + 4,
        rotation=(90, 0, 0),
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    body = block - groove

    if draft:
        return body

    bed = body.bounding_box().min.Z
    avoid = concave_edges(body)

    def three_way_corner(e):
        # The short shoulder-top edges (along X, at the top corners) meet a
        # vertical edge and a top-side edge at the same convex vertex; chamfering
        # all three leaves a sub-1mm2 corner triangle. Leave these bare instead.
        bb = e.bounding_box()
        return (bb.max.Y - bb.min.Y) < 1e-6 and (bb.max.Z - bb.min.Z) < 1e-6

    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed
        and e not in avoid
        and not three_way_corner(e)
    )
    return polish(body, keep, 1.0)
