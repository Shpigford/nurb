from nurb import *


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    knob_radius=18.0,
    knob_height=16.0,
    draft=False,
):
    """A support-free replacement knob for a D-shaped valve stem.

    shaft_diameter: diameter of the round portion of the valve stem
    shaft_across_flat: distance from the stem's flat to its opposite round side
    knob_radius: reach from the center to each of the six grip corners
    knob_height: overall printed height of the knob
    """
    if shaft_diameter <= 0.0:
        reject("shaft_diameter must be greater than zero", param="shaft_diameter")
    if shaft_across_flat <= shaft_diameter / 2.0:
        reject(
            "shaft_across_flat must be greater than half shaft_diameter",
            param="shaft_across_flat",
        )
    if shaft_across_flat >= shaft_diameter:
        reject(
            "shaft_across_flat must be less than shaft_diameter for a D-shaft",
            param="shaft_across_flat",
        )

    # A regular hexagon supplies broad flats and six positive grip points while
    # using less material than a round knob with added lobes.
    body = extrude(RegularPolygon(knob_radius, 6), knob_height)

    # Printed bores close slightly. Adding 0.6 mm to both measured D-shaft
    # dimensions clears the +0.3 mm functional gauge while the +1.0 mm gauge
    # still jams. The flat is on +X, matching the stem orientation in use.
    fit_clearance = 0.6
    bore_diameter = shaft_diameter + fit_clearance
    bore_across_flat = shaft_across_flat + fit_clearance
    bore_radius = bore_diameter / 2.0
    bore_flat_x = -bore_radius + bore_across_flat
    bore_depth = 12.5
    bore_floor = knob_height - bore_depth

    round_bore = Pos(0.0, 0.0, bore_floor) * Cylinder(bore_radius, bore_depth)
    flat_clip = Pos(-bore_radius, 0.0, bore_floor) * Box(
        bore_radius + bore_flat_x,
        bore_diameter + 2.0,
        bore_depth,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    d_bore = round_bore & flat_clip
    body = body - d_bore

    if draft:
        return body

    # Dress only the six outer top edges. The bed face and the fit-critical
    # mouth of the D-bore remain dimensionally exact.
    outer_top = body.edges().filter_by(
        lambda edge: edge.bounding_box().min.Z > knob_height - 0.01
        and max(
            abs(edge.bounding_box().min.X),
            abs(edge.bounding_box().max.X),
            abs(edge.bounding_box().min.Y),
            abs(edge.bounding_box().max.Y),
        )
        > knob_radius * 0.75
    )
    return polish(body, outer_top, 1.0)
