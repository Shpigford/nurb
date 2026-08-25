from nurb import *


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    height=14.0,
    grip_width=30.0,
    lobe_reach=18.0,
    draft=False,
):
    """Replacement knob for a D-stem valve, printed bore-up.

    shaft_diameter: round width of the valve stem
    shaft_across_flat: stem thickness from the flat to the opposite round
    height: how tall the knob is
    grip_width: across the hub, the narrowest outside
    lobe_reach: how far each lobe sticks out from the center
    """
    if shaft_across_flat >= shaft_diameter:
        reject(
            "shaft_across_flat must be smaller than shaft_diameter to form a D-stem",
            param="shaft_across_flat",
        )
    if grip_width < 28.0:
        reject("grip_width must stay at least 28mm across", param="grip_width")
    if lobe_reach < grip_width / 2 * 1.12:
        reject(
            "lobe_reach must reach at least 12% past the hub radius for wet-hand grip",
            param="lobe_reach",
        )
    if height < 12.0:
        reject("height must be at least 12mm to cover the stem", param="height")

    # Clearance between the 0.3mm fit stem and the 1.0mm rattle stem.
    bore_diameter = shaft_diameter + 0.5
    bore_across_flat = shaft_across_flat + 0.5
    bore_depth = min(height - 3.0, height - 1.0)
    if bore_depth < 10.5:
        bore_depth = height - 2.5

    hub_r = grip_width / 2
    lobe_r = 7.5
    lobe_offset = lobe_reach - lobe_r

    with BuildSketch() as outline:
        Circle(hub_r)
        with PolarLocations(lobe_offset, 5):
            Circle(lobe_r)

    body = extrude(outline.sketch, amount=height)

    bore_r = bore_diameter / 2
    flat_x = bore_across_flat - bore_r
    cap_w = bore_r * 2 + 2.0
    with BuildSketch() as d_sk:
        Circle(bore_r)
        with Locations((flat_x + cap_w / 2, 0)):
            Rectangle(cap_w, bore_r * 2 + 2.0, mode=Mode.SUBTRACT)

    cutter = Pos(0, 0, height - bore_depth) * extrude(
        d_sk.sketch, amount=bore_depth + 2.0
    )
    body = body - cutter

    if draft:
        return body

    bed = body.bounding_box().min.Z
    keep = body.edges().filter_by(lambda e: e.bounding_box().min.Z > bed + 0.05)
    keep -= concave_edges(body)
    # Leave the D-bore sharp so the flat can transmit torque.
    keep = keep.filter_by(
        lambda e: (e.center().X ** 2 + e.center().Y ** 2) ** 0.5 > bore_r + 0.8
    )
    return polish(body, keep, 1.0)
