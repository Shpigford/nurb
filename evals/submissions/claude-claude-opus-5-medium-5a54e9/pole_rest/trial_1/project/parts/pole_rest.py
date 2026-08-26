import math

from nurb import *

# Fixed by the bench setup: several identical rests stand in a row and the pole
# lies across all of them, so the axis height is an interface, not a choice.
POLE_AXIS_HEIGHT = 18.0


@part
def pole_rest(
    pole_diameter=measured("pole_diameter"),
    pole_clearance=0.25,
    wall_thickness=3.0,
    rest_length=22.0,
    rim_height=3.0,
    chamfer_size=1.2,
    draft=False,
):
    """A cradle that holds a freshly finished pole while the finish dries.

    pole_diameter: how thick the pole is, measured across
    pole_clearance: gap between the pole and the cradle, so wet finish never touches
    wall_thickness: how much material sits outside the cradle
    rest_length: how far the rest runs along the pole
    rim_height: how far the cradle walls rise above the pole's centre
    chamfer_size: the facet taken off every exposed edge
    """
    cradle_radius = pole_diameter / 2.0 + pole_clearance
    floor = POLE_AXIS_HEIGHT - cradle_radius
    if floor < 2.0:
        reject(
            f"a {pole_diameter}mm pole seated at {POLE_AXIS_HEIGHT}mm leaves only "
            f"{floor:.2f}mm of floor under the cradle; keep pole_diameter under "
            f"{2 * (POLE_AXIS_HEIGHT - 2.0 - pole_clearance):.1f}",
            param="pole_diameter",
        )

    width = 2.0 * (cradle_radius + wall_thickness)
    height = POLE_AXIS_HEIGHT + rim_height

    body = Box(width, rest_length, height, align=(Align.CENTER, Align.CENTER, Align.MIN))

    # The seat is a half-round the size of the pole plus its clearance, capped by
    # straight walls above the pole's centre so the pole lowers in from directly
    # above without touching anything on the way down.
    over = rest_length + 2.0
    seat = Pos(0, 0, POLE_AXIS_HEIGHT) * Rot(90, 0, 0) * Cylinder(cradle_radius, over)
    mouth = Pos(0, 0, POLE_AXIS_HEIGHT) * Box(
        2.0 * cradle_radius, over, rim_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    body = body - seat - mouth

    if draft:
        return body

    def key(edge):
        bb = edge.bounding_box()
        return tuple(round(v, 4) for v in (bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y, bb.max.Z))

    concave = {key(e) for e in concave_edges(body)}

    def keep(edge):
        bb = edge.bounding_box()
        if key(edge) in concave:
            return False
        # Nothing lying in the bed-contact face.
        if bb.max.Z <= 1e-3:
            return False
        # Nothing on the seat: the cradle and its mouth are what the pole meets,
        # and a lead-in chamfer there is exactly the polish the doctrine forbids.
        if max(abs(bb.min.X), abs(bb.max.X)) <= cradle_radius + 0.05:
            return False
        return True

    return polish(body, body.edges().filter_by(keep), chamfer_size)
