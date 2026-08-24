from math import cos, radians, sin

from nurb import *

# The bench interface is fixed: the pole lies along Y with its axis exactly
# this far above the bed, centered over the footprint in X.
AXIS_HEIGHT = 18.0

# Seat radius over pole radius. Sized so a soft finish never touches an edge:
# the pole settles onto a matching arc, not onto rims.
SEAT_GAP = 0.25

# How far the seat wraps around the pole, each side of bottom dead center.
# The cradle needs a 120 degree arc of close support; 65 each side leaves
# margin so end chamfers and tolerance never eat into it.
WRAP_DEG = 65.0


@part
def pole_rest(pole_diameter=20.0, rest_length=22.0, side_wall=2.4, draft=False):
    """A bench rest that cradles a freshly finished pole while it dries.

    pole_diameter: how wide the pole is, measured across
    rest_length: how long the rest runs along the pole
    side_wall: how much material backs the seat at its rim
    """
    pole_r = pole_diameter / 2
    seat_r = pole_r + SEAT_GAP
    floor = AXIS_HEIGHT - seat_r
    if floor < 2.0:
        reject(
            f"pole_diameter {pole_diameter:g} leaves under 2mm of material "
            f"between the seat and the bed at the fixed {AXIS_HEIGHT:g}mm axis "
            "height: keep it below 31",
            param="pole_diameter",
        )
    if pole_diameter < 4.0:
        reject(
            f"pole_diameter {pole_diameter:g} is too small to cradle: "
            "keep it at 4 or more",
            param="pole_diameter",
        )
    if side_wall < 2.0:
        reject(
            f"side_wall {side_wall:g} is under the 2mm minimum printable wall",
            param="side_wall",
        )

    wrap = radians(WRAP_DEG)
    top = AXIS_HEIGHT - seat_r * cos(wrap)
    half_width = max(seat_r * sin(wrap) + side_wall, 5.0)

    block = Box(
        2 * half_width,
        rest_length,
        top,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    seat = Pos(0, 0, AXIS_HEIGHT) * Rot(90, 0, 0) * Cylinder(seat_r, rest_length + 2)
    body = block - seat

    if draft:
        return body

    # Polish everything except the seat (mating geometry stays untouched: no
    # lead-in chamfers, and the support arc keeps its full wrap) and edges
    # lying in the bed face. Vertical corners merely ending at the bed keep
    # their chamfers.
    def polishable(e):
        bb = e.bounding_box()
        cx = (bb.min.X + bb.max.X) / 2
        cz = (bb.min.Z + bb.max.Z) / 2
        near_seat = (cx**2 + (cz - AXIS_HEIGHT) ** 2) ** 0.5 < seat_r + 0.5
        in_bed = bb.max.Z < 1e-6
        return not near_seat and not in_bed

    # 1.1mm rather than the 1.0 default: the corner triangles where three
    # chamfers meet then land at ~1.05mm2, above the sliver threshold.
    keep = body.edges().filter_by(polishable)
    return polish(body, keep, 1.1)
