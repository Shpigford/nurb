from nurb import *
import math

AXIS_HEIGHT = 18.0  # the bench row is fixed: every rest puts the pole axis here


@part
def pole_rest(
    pole_diameter: float = 20.0,
    rest_length: float = 22.0,
    wall_thickness: float = 3.0,
    pole_clearance: float = 0.3,
    rim_rise: float = 1.5,
    chamfer_size: float = 1.0,
    draft: bool = False,
):
    """A cradle that holds a freshly finished pole off the bench while it dries.

    pole_diameter: how thick the pole is across
    rest_length: how far the rest runs along the pole
    wall_thickness: how much material sits behind the cradle surface
    pole_clearance: the gap between the cradle and the wet finish
    rim_rise: how far the cradle lips stand above the pole's centreline
    chamfer_size: the chamfer taken off the exposed edges
    """
    seat_radius = pole_diameter / 2.0 + pole_clearance
    seat_bottom = AXIS_HEIGHT - seat_radius
    if seat_bottom < wall_thickness:
        reject(
            f"pole_diameter {pole_diameter} leaves only {seat_bottom:.1f}mm under the "
            f"seat at the fixed {AXIS_HEIGHT}mm axis height: keep it under "
            f"{2 * (AXIS_HEIGHT - wall_thickness - pole_clearance):.1f}",
            param="pole_diameter",
        )
    if rim_rise < 0.0:
        reject("rim_rise cannot be negative", param="rim_rise")

    # the seat is a half round below the pole's centreline, so it wraps the full 180
    # degrees; above the centreline the lips run straight up and the pole drops in
    body_height = AXIS_HEIGHT + rim_rise
    body_width = 2.0 * (seat_radius + wall_thickness)

    body = Pos(0, 0, body_height / 2) * Box(body_width, rest_length, body_height)

    # seat: the pole's own arc, plus a straight-walled mouth above it so the pole
    # drops in from directly overhead without touching anything on the way down
    trough = Pos(0, 0, AXIS_HEIGHT) * Rot(90, 0, 0) * Cylinder(
        seat_radius, rest_length + 2.0
    )
    mouth = Pos(0, 0, AXIS_HEIGHT + body_height / 2) * Box(
        2 * seat_radius, rest_length + 2.0, body_height
    )
    body = body - trough - mouth

    if draft:
        return body

    bed = body.bounding_box().min.Z
    concave = set(concave_edges(body))

    def on_seat(e):
        # the cradle surface is what the wet finish touches: leave its edges alone
        for u in (0.0, 0.5, 1.0):
            pt = e.position_at(u)
            r = math.hypot(pt.X, pt.Z - AXIS_HEIGHT)
            if abs(r - seat_radius) > 0.05:
                return False
        return True

    keep = [
        e
        for e in body.edges()
        if e.bounding_box().min.Z > bed + 1e-6
        and e not in concave
        and not on_seat(e)
    ]
    return polish(body, keep, chamfer_size)
