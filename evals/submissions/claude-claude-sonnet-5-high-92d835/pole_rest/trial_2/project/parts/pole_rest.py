from nurb import *
from math import sin, cos, radians

AXIS_HEIGHT = 18.0


@part
def pole_rest(
    pole_diameter=20.0,
    length=22.0,
    clearance=0.3,
    wall=2.5,
    cradle_span=130.0,
    draft=False,
):
    """
    pole_diameter: diameter of the pole this rest cradles
    length: how long the rest runs along the pole
    clearance: gap left between the pole and the seat surface
    wall: material backing the seat, behind the pole's surface
    cradle_span: how much of the pole's circumference the cradle wraps, in degrees
    """
    if cradle_span < 120.0:
        reject(
            f"cradle_span {cradle_span} wraps under 120 degrees of the pole "
            "and will not hold it; raise it above 120",
            param="cradle_span",
        )
    if cradle_span > 175.0:
        reject(
            f"cradle_span {cradle_span} opens past 175 degrees, near the "
            "pole's own equator, and the pole can no longer drop straight "
            "down into the seat; keep it under 175",
            param="cradle_span",
        )

    pole_r = pole_diameter / 2.0
    seat_r = pole_r + clearance
    half_angle = radians(cradle_span / 2.0)

    top_z = AXIS_HEIGHT - seat_r * cos(half_angle)
    half_w = seat_r * sin(half_angle) + wall

    body = Box(
        2 * half_w, length, top_z,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    seat = Pos(0, 0, AXIS_HEIGHT) * Cylinder(
        seat_r, length + 20.0, rotation=(90, 0, 0),
    )
    body = body - seat

    if draft:
        return body

    def axis_dist(pt):
        return ((pt.X) ** 2 + (pt.Z - AXIS_HEIGHT) ** 2) ** 0.5

    concave = concave_edges(body)
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().max.Z > 1e-6
        and abs(axis_dist(e.center()) - seat_r) > 0.05
        and e not in concave
    )
    return polish(body, keep, 1.2)
