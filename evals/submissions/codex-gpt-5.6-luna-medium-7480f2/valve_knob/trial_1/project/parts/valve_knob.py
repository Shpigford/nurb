from nurb import *


@part
def valve_knob(shaft_diameter=8.0, shaft_across_flat=6.5, height=16.0, draft=False):
    """Replacement valve knob.

    shaft_diameter: measured round diameter of the valve stem
    shaft_across_flat: measured distance from the stem flat to its opposite round side
    height: overall knob height above the print bed
    """
    round_clearance = 0.35
    flat_clearance = 0.35

    # A 15mm hub plus six small radial lobes gives a wet-hand grip while
    # keeping the part light.  All features start on the bed and rise together.
    body = Cylinder(15.0, height)
    for angle in range(0, 360, 60):
        lobe = Pos(14.0, 0, 0) * Cylinder(3.0, height)
        body = body + (Rot(0, 0, angle) * lobe)

    # The flat is on +X.  For a D whose opposite side is the round tangent,
    # flat_x = across_flat - radius.  Intersecting the clearance cylinder with
    # that half-space makes a non-round socket that transmits torque.
    bore_radius = shaft_diameter / 2.0 + round_clearance
    bore_across_flat = shaft_across_flat + flat_clearance
    flat_x = bore_across_flat - bore_radius
    bore_round = Cylinder(bore_radius, height + 0.4)
    bore_halfspace = Pos(-bore_radius, 0, -0.2) * Box(
        flat_x + bore_radius, 2.0 * bore_radius, height + 0.4,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    bore = bore_round & bore_halfspace
    body = body - bore
    if draft:
        return body
    # Keep the bed, bore, and concave lobe seams fit-critical; soften only
    # exposed convex edges.
    bed = body.bounding_box().min.Z
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed and e.bounding_box().max.Z > bed
    ).filter_by(lambda e: e not in concave_edges(body))
    return polish(body, keep, 1.0)
