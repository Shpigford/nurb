from math import atan2, degrees, sqrt

from nurb import *

# Added to both stem diameter and across-flat: loose enough to drop on, tight enough to drive.
_BORE_CLEARANCE = 0.75

_KNOB_LENGTH = 40.0
_KNOB_WIDTH = 30.0
_KNOB_HEIGHT = 14.0


def _d_face(diameter, across_flat):
    """D-profile on XY, circle centered on the origin, flat facing +X."""
    radius = diameter / 2.0
    flat_x = across_flat - radius
    half = sqrt(radius * radius - flat_x * flat_x)
    start = degrees(atan2(half, flat_x))
    end = degrees(atan2(-half, flat_x))
    arc = Edge.make_circle(
        radius,
        Plane.XY,
        start_angle=start,
        end_angle=end + 360.0,
        angular_direction=AngularDirection.COUNTER_CLOCKWISE,
    )
    line = Edge.make_line(Vector(flat_x, -half, 0), Vector(flat_x, half, 0))
    return Face(Wire([arc, line]))


@part
def valve_knob(
    shaft_diameter: float = measured("shaft_diameter"),
    shaft_across_flat: float = measured("shaft_across_flat"),
    draft=False,
):
    """Replacement knob for a valve with a D-shaped stem. Prints bore-up.

    shaft_diameter: round-side width of the stem the knob drops onto
    shaft_across_flat: stem thickness from the flat to the opposite round side
    """
    if shaft_diameter <= 0:
        reject("shaft_diameter must be positive", param="shaft_diameter")
    if shaft_across_flat <= 0:
        reject("shaft_across_flat must be positive", param="shaft_across_flat")
    if shaft_across_flat >= shaft_diameter:
        reject(
            f"shaft_across_flat {shaft_across_flat}mm must be under "
            f"shaft_diameter {shaft_diameter}mm to leave a driving flat",
            param="shaft_across_flat",
        )

    bore_diameter = shaft_diameter + _BORE_CLEARANCE
    bore_across_flat = shaft_across_flat + _BORE_CLEARANCE
    if bore_across_flat >= bore_diameter:
        reject(
            "shaft_across_flat is too close to shaft_diameter for the bore clearance",
            param="shaft_across_flat",
        )
    if bore_diameter + 4.0 > _KNOB_WIDTH:
        reject(
            f"shaft_diameter {shaft_diameter}mm is too large for this knob body",
            param="shaft_diameter",
        )

    body = extrude(SlotOverall(_KNOB_LENGTH, _KNOB_WIDTH), amount=_KNOB_HEIGHT)
    bore = extrude(_d_face(bore_diameter, bore_across_flat), amount=_KNOB_HEIGHT + 2.0)
    body = body - bore.moved(Location((0, 0, -1.0)))

    if draft:
        return body

    bed = body.bounding_box().min.Z
    concave = set(concave_edges(body))
    bore_limit = (bore_diameter / 2.0) + 0.8

    def polishable(edge):
        if edge in concave:
            return False
        if edge.bounding_box().min.Z <= bed + 1e-4:
            return False
        center = edge.center()
        if center.X * center.X + center.Y * center.Y < bore_limit * bore_limit:
            return False
        return True

    keep = body.edges().filter_by(polishable)
    return polish(body, keep, 1.0)
