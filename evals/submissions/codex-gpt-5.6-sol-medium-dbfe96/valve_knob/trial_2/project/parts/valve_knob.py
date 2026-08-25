from nurb import *


@part
def valve_knob(
    shaft_diameter: float = 8.0,
    shaft_across_flat: float = 6.5,
    knob_height: float = 16.0,
    grip_radius: float = 17.2,
):
    """A support-free replacement knob for a D-shaped valve stem.

    shaft_diameter: measured diameter of the valve stem
    shaft_across_flat: measured distance from the flat to the opposite round side
    knob_height: overall height of the printed knob
    grip_radius: distance from the center to each of the six grip corners
    """
    if shaft_across_flat >= shaft_diameter:
        reject("shaft_across_flat must be smaller than shaft_diameter", "shaft_across_flat")

    body = extrude(RegularPolygon(grip_radius, 6), amount=knob_height)
    top_edges = body.edges().filter_by(
        lambda edge: edge.bounding_box().min.Z > knob_height - 0.01
    )
    body = polish(body, top_edges, 1.0)

    # Independent 0.5 mm clearance on the diameter and across-flat dimensions.
    bore_diameter = shaft_diameter + 0.5
    bore_across_flat = shaft_across_flat + 0.5
    bore_depth = 12.0
    bore_radius = bore_diameter / 2.0
    flat_x = bore_across_flat - bore_radius

    round_bore = Cylinder(
        bore_radius,
        bore_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).translate((0, 0, knob_height - bore_depth))
    flat_limit = Box(
        2.0 * bore_radius,
        2.0 * bore_radius,
        bore_depth,
        align=(Align.MAX, Align.CENTER, Align.MIN),
    ).translate((flat_x, 0, knob_height - bore_depth))
    d_bore = round_bore & flat_limit

    return body - d_bore
