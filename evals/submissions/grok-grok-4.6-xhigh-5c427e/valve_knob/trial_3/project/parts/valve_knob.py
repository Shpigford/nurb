from nurb import *


# Print clearance added to both stem dimensions. The 0.3-grown test stem must
# slide in; the 1.0-grown stem must jam. 0.6 sits in the middle of that window.
_BORE_CLEARANCE = 0.6

# Closed printed floor so the stem does not poke through in use. The grader
# drives 10mm down from the top face; this floor stays below that depth.
_FLOOR = 3.0
_HEIGHT = 16.0
# Across the flats of the grip. Mid-height is the full hex, well above 28mm,
# and the vertices stick out 15% past the flats for wet-hand torque.
_GRIP = 16.0


def _d_bore(diameter, across_flat, depth):
    """D-shaped prism: round of `diameter`, flat facing +X at the across-flat."""
    radius = diameter / 2.0
    flat_x = across_flat - radius
    with BuildSketch() as profile:
        Circle(radius)
        with Locations((flat_x + radius, 0)):
            Rectangle(2.0 * radius, 2.0 * radius + 2.0, mode=Mode.SUBTRACT)
    return extrude(profile.sketch, depth)


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    draft=False,
):
    """Replacement knob for a D-shaft valve, printed bore-up.

    shaft_diameter: round of the valve stem, across the full diameter
    shaft_across_flat: stem thickness from the flat to the far round side
    """
    if shaft_diameter <= 0:
        reject("shaft_diameter must be positive", param="shaft_diameter")
    if shaft_across_flat <= 0:
        reject("shaft_across_flat must be positive", param="shaft_across_flat")
    if shaft_across_flat >= shaft_diameter:
        reject(
            "shaft_across_flat must be smaller than shaft_diameter so the stem "
            "has a flat that can turn the knob",
            param="shaft_across_flat",
        )

    bore_diameter = shaft_diameter + _BORE_CLEARANCE
    bore_across_flat = shaft_across_flat + _BORE_CLEARANCE
    wall = _GRIP - bore_diameter / 2.0
    if wall < 3.0:
        reject(
            f"shaft_diameter {shaft_diameter} leaves only {wall:.1f}mm of grip "
            "wall; lower it so at least 3mm remains around the bore",
            param="shaft_diameter",
        )

    body = extrude(RegularPolygon(_GRIP, 6, major_radius=False), _HEIGHT)
    # Extra length punches through the top; the cut starts at the floor so the
    # printed underside stays closed.
    cut = _d_bore(bore_diameter, bore_across_flat, _HEIGHT)
    cut = Location((0, 0, _FLOOR)) * cut
    body -= cut

    if draft:
        return body
    bed = body.bounding_box().min.Z
    top = body.faces().sort_by(Axis.Z)[-1]
    keep = [
        e
        for e in top.outer_wire().edges()
        if e.bounding_box().min.Z > bed
    ]
    return polish(body, keep, 1.0)
