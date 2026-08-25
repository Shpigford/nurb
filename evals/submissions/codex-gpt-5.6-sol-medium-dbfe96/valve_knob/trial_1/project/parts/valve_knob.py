from nurb import *


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    knob_height=16.0,
    grip_radius=17.5,
    bore_clearance=0.6,
    bore_depth=12.0,
    draft=False,
):
    """A support-free replacement knob for a valve with a D-shaped stem.

    shaft_diameter: diameter of the round portion of the valve stem
    shaft_across_flat: distance from the stem's flat to its opposite round side
    knob_height: overall printed height of the knob
    grip_radius: reach from the center to each of the six grip points
    bore_clearance: total extra size added to both stem measurements
    bore_depth: how far the stem socket extends down from the top
    """
    if shaft_across_flat >= shaft_diameter:
        reject(
            "shaft_across_flat must be smaller than shaft_diameter for a D-shaft",
            param="shaft_across_flat",
        )
    if bore_depth >= knob_height - 2.0:
        reject(
            "bore_depth must leave at least a 2mm floor under the socket",
            param="bore_depth",
        )

    body = extrude(RegularPolygon(grip_radius, 6), knob_height)

    bore_diameter = shaft_diameter + bore_clearance
    bore_across_flat = shaft_across_flat + bore_clearance
    bore_radius = bore_diameter / 2.0
    flat_x = bore_across_flat - bore_radius
    bore_bottom = knob_height - bore_depth

    round_bore = Pos(0, 0, bore_bottom) * Cylinder(bore_radius, bore_depth + 0.2)
    flat_clip = Pos(-bore_radius, 0, bore_bottom) * Box(
        bore_radius + flat_x,
        bore_diameter + 2.0,
        bore_depth + 0.2,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    bore = round_bore & flat_clip
    knob = body - bore

    if draft:
        return knob

    bed = knob.bounding_box().min.Z
    top = knob.bounding_box().max.Z
    finish_edges = knob.edges().filter_by(
        lambda edge: edge.bounding_box().min.Z > bed + 0.1
        and edge.bounding_box().max.Z >= top - 0.1
        and max(
            abs(edge.bounding_box().min.X),
            abs(edge.bounding_box().max.X),
            abs(edge.bounding_box().min.Y),
            abs(edge.bounding_box().max.Y),
        )
        > 10.0
    )
    return polish(knob, finish_edges, 1.0)
