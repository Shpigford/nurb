from nurb import *

# The row of rests is a fixed interface: the pole lies along Y with its axis
# exactly this far above the bench, so every rest cradles it at the same height.
AXIS_HEIGHT = 18.0


@part
def pole_rest(
    pole_diameter=measured("pole_diameter"),
    cradle_gap=0.2,
    cradle_wall=3.0,
    rest_length=24.0,
    chamfer_size=1.2,
    draft=False,
):
    """A drying rest: the finished pole lies in a half-round cradle, touching nothing sharp.

    pole_diameter: how thick the pole is across
    cradle_gap: air between the pole and the cradle, so the soft finish never rubs
    cradle_wall: how much material stands behind the cradle at its rim
    rest_length: how far the rest runs along the pole
    chamfer_size: how big the chamfers on the exposed edges are
    """
    cradle_radius = pole_diameter / 2.0 + cradle_gap
    floor = AXIS_HEIGHT - cradle_radius
    if floor < 3.0:
        reject(
            f"a {pole_diameter}mm pole leaves only {floor:.1f}mm of floor under the cradle "
            f"at the fixed {AXIS_HEIGHT}mm axis height: keep pole_diameter under "
            f"{2 * (AXIS_HEIGHT - 3.0 - cradle_gap):.1f}",
            param="pole_diameter",
        )

    width = 2.0 * (cradle_radius + cradle_wall)

    body = Box(width, rest_length, AXIS_HEIGHT,
               align=(Align.CENTER, Align.CENTER, Align.MIN))

    # The cradle is a half round opening upward: its widest point is the pole's own
    # axis, level with the top face, so the pole lowers straight down into it.
    seat = Pos(0, 0, AXIS_HEIGHT) * Rot(90, 0, 0) * Cylinder(
        cradle_radius, rest_length + 2.0
    )
    body = body - seat

    if draft:
        return body

    bed = body.bounding_box().min.Z
    concave = set(concave_edges(body))
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed + 1e-6 and e not in concave
    )
    return polish(body, keep, chamfer_size)
