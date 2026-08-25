from nurb import *


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    draft=False,
):
    """A support-free replacement knob for a D-shaped valve stem.

    shaft_diameter: diameter of the round portion of the valve stem
    shaft_across_flat: distance from the stem's flat to its opposite round side
    """
    if shaft_across_flat >= shaft_diameter:
        reject(
            "shaft_across_flat must be smaller than shaft_diameter for a D-shaped stem",
            param="shaft_across_flat",
        )

    knob_height = 15.0
    knob_radius = 18.0
    bore_depth = 12.2
    bore_allowance = 0.8

    # A six-sided grip has a 31.2 mm minimum width and an 18 mm reach at
    # the corners, giving wet fingers positive flats and corners to push on.
    grip = extrude(RegularPolygon(knob_radius, 6), amount=knob_height)
    if not draft:
        top_rim = grip.edges().filter_by(
            lambda edge: edge.bounding_box().min.Z > knob_height - 0.1
        )
        grip = polish(grip, top_rim, 1.0)

    # Build the D opening from both measured stem dimensions.  The clipping
    # rectangle starts at the circle's -X extreme, leaving the flat facing +X.
    bore_diameter = shaft_diameter + bore_allowance
    bore_across_flat = shaft_across_flat + bore_allowance
    bore_radius = bore_diameter / 2.0
    bore_profile = Circle(bore_radius) & (
        Pos(-bore_radius, 0) *
        Rectangle(
            bore_across_flat,
            bore_diameter,
            align=(Align.MIN, Align.CENTER),
        )
    )
    bore = Pos(0, 0, knob_height - bore_depth) * extrude(
        bore_profile,
        amount=bore_depth + 0.2,
    )

    return grip - bore
