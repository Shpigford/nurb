from math import cos, radians, sin

from nurb import *

# The bench row fixes the interface: the pole lies along Y with its axis
# exactly this high above the bed, centered over the footprint in X.
AXIS_HEIGHT = 18.0


@part
def pole_rest(
    pole_diameter=float(measured("pole_diameter")),
    rest_length=22.0,
    cradle_angle=150.0,
    pole_clearance=0.25,
    draft=False,
):
    """A drying rest the freshly finished pole lies across.

    pole_diameter: how thick the pole is, straight from the calipers
    rest_length: how long the rest runs along the pole
    cradle_angle: how far around the pole the seat wraps, in degrees
    pole_clearance: the gap between the seat and the pole's finish
    """
    if not 0.15 <= pole_clearance <= 0.35:
        reject(
            f"pole_clearance {pole_clearance} leaves the pole either binding on the "
            "wet finish or rattling on edges: keep it between 0.15 and 0.35",
            param="pole_clearance",
        )
    if not 130.0 <= cradle_angle <= 165.0:
        reject(
            f"cradle_angle {cradle_angle} either drops below a real cradle once the "
            "rim chamfers run, or wraps far enough to fight a straight drop-in: "
            "keep it between 130 and 165",
            param="cradle_angle",
        )
    if rest_length < 20.0:
        reject(
            f"rest_length {rest_length} is under the 20mm the bench row calls for",
            param="rest_length",
        )

    seat_r = pole_diameter / 2.0 + pole_clearance
    if AXIS_HEIGHT - seat_r < 2.0:
        reject(
            f"pole_diameter {pole_diameter} puts the seat within 2mm of the bed at "
            "the fixed 18mm axis height: this rest tops out near 31mm poles",
            param="pole_diameter",
        )

    half = radians(cradle_angle / 2.0)
    rim_x = seat_r * sin(half)
    top = AXIS_HEIGHT - seat_r * cos(half)
    # 1.2mm of backing behind the seat everywhere, and enough top-face strip
    # beside the rim for two 1mm chamfers to land without colliding.
    half_width = max((seat_r + 1.2) * sin(half) + 0.6, rim_x + 2.5)

    body = Pos(0, 0, top / 2.0) * Box(2.0 * half_width, rest_length, top)
    seat = (
        Pos(0, 0, AXIS_HEIGHT)
        * Rot(90, 0, 0)
        * Cylinder(seat_r, rest_length + 2.0)
    )
    body -= seat

    if draft:
        return body
    bed = body.bounding_box().min.Z
    # Straight edges only: chamfering the seat's end arcs as well would leave
    # sliver corner triangles where three chamfers meet at each rim corner.
    keep = body.edges().filter_by(GeomType.LINE).filter_by(
        lambda e: e.bounding_box().min.Z > bed + 0.1
    )
    return polish(body, keep, 1.0)
