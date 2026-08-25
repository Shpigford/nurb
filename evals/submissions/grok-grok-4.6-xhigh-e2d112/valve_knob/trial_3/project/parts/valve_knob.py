from math import hypot

from nurb import *

# Modelled slack on both D-shaft readings: enough that a 0.3mm-oversize stem
# drops in, tight enough that a 1mm-oversize stem jams and still takes torque.
_BORE_SLACK = 0.75


def _d_section(diameter, across_flat):
    """D-profile on XY, circle centred on the origin, flat facing +X."""
    radius = diameter / 2.0
    flat_x = across_flat - radius
    disk = Circle(radius)
    cutter = Pos(flat_x, 0) * Rectangle(
        diameter + 2.0, diameter + 2.0, align=(Align.MIN, Align.CENTER)
    )
    return disk - cutter


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    draft=False,
):
    """Replacement knob for a D-shaft valve stem, printed bore-up.

    shaft_diameter: caliper reading across the round of the stem
    shaft_across_flat: caliper reading from the stem's flat to the opposite round
    """
    if shaft_across_flat >= shaft_diameter:
        reject(
            f"shaft_across_flat {shaft_across_flat}mm must be smaller than "
            f"shaft_diameter {shaft_diameter}mm to form a D-shaft",
            param="shaft_across_flat",
        )

    knob_width = 32.0
    height = 16.0
    floor = 3.0

    bore_diameter = shaft_diameter + _BORE_SLACK
    bore_across_flat = shaft_across_flat + _BORE_SLACK
    if bore_diameter >= knob_width - 6.0:
        reject(
            f"shaft_diameter {shaft_diameter}mm leaves the bore too close to "
            f"the {knob_width}mm grip; use a smaller stem",
            param="shaft_diameter",
        )
    if bore_across_flat >= bore_diameter:
        reject(
            f"shaft_across_flat {shaft_across_flat}mm plus clearance is not a "
            f"flat on a {shaft_diameter}mm stem",
            param="shaft_across_flat",
        )

    body = extrude(RegularPolygon(knob_width / 2.0, 6, major_radius=False), height)

    bore_depth = height - floor + 1.0
    bore = Pos(0, 0, floor) * extrude(_d_section(bore_diameter, bore_across_flat), bore_depth)
    body = body - bore

    if draft:
        return body

    top = body.bounding_box().max.Z
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > top - 0.2
        and hypot(e.center().X, e.center().Y) > bore_diameter
    )
    return polish(body, keep, 1.0)
