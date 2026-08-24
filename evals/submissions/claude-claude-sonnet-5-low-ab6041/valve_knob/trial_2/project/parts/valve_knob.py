from nurb import *


@part
def valve_knob(
    shaft_diameter=8.0,
    shaft_across_flat=6.5,
    knob_height=13.5,
    hub_radius=14.1,
    lobe_radius=8.5,
    lobe_offset=14.8,
    draft=False,
):
    """
    shaft_diameter: the valve stem's diameter across its round side
    shaft_across_flat: the valve stem's diameter measured across its flat
    knob_height: how tall the knob stands off the bed
    hub_radius: the knob's base radius, set by hand size
    lobe_radius: how big the two grip lobes are
    lobe_offset: how far the grip lobes sit from the centerline
    """
    if shaft_across_flat >= shaft_diameter:
        reject(
            f"shaft_across_flat {shaft_across_flat} must be under shaft_diameter {shaft_diameter}",
            param="shaft_across_flat",
        )

    bore_depth = 11.0

    shaft_radius = shaft_diameter / 2.0
    flat_offset = shaft_across_flat - shaft_radius

    bore_radius = shaft_radius + 0.35
    bore_flat_offset = flat_offset + 0.4

    profile = (
        Circle(hub_radius)
        + Pos(0, lobe_offset) * Circle(lobe_radius)
        + Pos(0, -lobe_offset) * Circle(lobe_radius)
    )
    body = extrude(profile, knob_height)

    if draft:
        return body

    cut_span = bore_radius * 2.0 + 4.0
    bore_face = Circle(bore_radius) - Pos(bore_flat_offset + cut_span / 2.0, 0) * Rectangle(
        cut_span, bore_radius * 2.0 + 4.0
    )
    bore = extrude(bore_face, bore_depth + 1.0)
    bore = Pos(0, 0, knob_height - bore_depth) * bore

    body = body - bore

    bed = body.bounding_box().min.Z
    concave = set(concave_edges(body))
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed and e not in concave
    )
    return polish(body, keep, 1.0)
