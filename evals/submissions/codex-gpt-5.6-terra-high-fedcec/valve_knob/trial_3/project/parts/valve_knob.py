from nurb import *


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    knob_radius=17.0,
    knob_height=18.0,
    bore_clearance=0.7,
    draft=False,
):
    """Replacement knob for an 8 mm D-shaft valve stem.

    shaft_diameter: full round diameter of the D-shaped valve stem
    shaft_across_flat: distance from the stem flat to its opposite round side
    knob_radius: center-to-corner reach of the six-sided hand grip
    knob_height: printed height of the knob
    bore_clearance: extra size on both D-bore measurements for print fit
    """
    if shaft_diameter <= 0.0:
        reject("shaft_diameter must be positive", param="shaft_diameter")
    if shaft_across_flat <= 0.0 or shaft_across_flat >= shaft_diameter:
        reject(
            "shaft_across_flat must be positive and smaller than shaft_diameter",
            param="shaft_across_flat",
        )
    if bore_clearance <= 0.3:
        reject("bore_clearance must be above 0.3 mm for the required stem clearance", param="bore_clearance")
    if knob_height < 15.0:
        reject("knob_height must leave a 5 mm floor beneath the 10 mm stem engagement", param="knob_height")

    # A hexagonal exterior gives broad flats for the hand and corners beyond them
    # for positive wet-hand grip. The D bore opens upward for support-free printing.
    outer = extrude(RegularPolygon(knob_radius, 6), knob_height)
    if not draft:
        bed = outer.bounding_box().min.Z
        outer = polish(
            outer,
            outer.edges().filter_by(lambda edge: edge.bounding_box().min.Z > bed),
            1.0,
        )

    bore_diameter = shaft_diameter + bore_clearance
    bore_across_flat = shaft_across_flat + bore_clearance
    bore_radius = bore_diameter / 2.0
    # The shaft flat faces +X. Its plane is bore_across_flat from the -X tangent.
    flat_x = bore_across_flat - bore_radius
    bore_depth = knob_height - 5.0
    round_bore = Pos(0, 0, 5.0) * Cylinder(bore_radius, bore_depth)
    flat_cut = Pos(flat_x, 0, 5.0) * Box(
        bore_radius * 2.0,
        bore_radius * 2.0,
        bore_depth,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    d_bore = round_bore - flat_cut
    return outer - d_bore
