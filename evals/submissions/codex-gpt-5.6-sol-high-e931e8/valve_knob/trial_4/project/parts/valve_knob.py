from nurb import *


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    draft=False,
):
    """A broad hexagonal replacement knob for a D-shaped valve stem.

    shaft_diameter: diameter of the round portion of the valve stem
    shaft_across_flat: distance from the stem's flat to its round back
    """
    knob_height = 16.0
    knob_radius = 18.0
    bore_depth = 12.0
    bore_diameter_clearance = 0.6
    bore_flat_clearance = 0.6

    if shaft_across_flat >= shaft_diameter:
        reject(
            "shaft_across_flat must be smaller than shaft_diameter for a D-shaft",
            param="shaft_across_flat",
        )

    body = extrude(RegularPolygon(knob_radius, 6), amount=knob_height)
    if not draft:
        top_edges = body.edges().filter_by(
            lambda edge: edge.bounding_box().min.Z > knob_height - 0.1
        )
        body = polish(body, top_edges, 1.0)

    bore_radius = (shaft_diameter + bore_diameter_clearance) / 2.0
    bore_across_flat = shaft_across_flat + bore_flat_clearance
    bore_flat_x = bore_across_flat - bore_radius
    bore_bottom = knob_height - bore_depth

    round_cutter = Pos(0, 0, bore_bottom) * Cylinder(bore_radius, bore_depth + 0.1)
    flat_cutoff = Pos(bore_flat_x, -bore_radius - 1.0, bore_bottom) * Box(
        2.0 * bore_radius,
        2.0 * bore_radius + 2.0,
        bore_depth + 0.1,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    d_bore = round_cutter - flat_cutoff

    return body - d_bore
