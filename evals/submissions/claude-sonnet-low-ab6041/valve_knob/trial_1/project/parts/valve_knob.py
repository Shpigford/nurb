from nurb import *


@part
def valve_knob(
    shaft_diameter=8.0,
    shaft_across_flat=6.5,
    height=14.0,
    grip_across_flats=30.0,
    bore_depth=11.0,
    bore_clearance=0.65,
    draft=False,
):
    """
    shaft_diameter: diameter of the valve stem the knob presses onto
    shaft_across_flat: the stem's flat-to-round distance, so the bore drives it
    height: overall knob height
    grip_across_flats: hex grip width, measured flat to flat, for a wet-hand grip
    bore_depth: how far the D-shaped bore reaches down from the top face
    bore_clearance: total growth added to the stem's diameter and flat to size the bore
    """
    if bore_depth >= height:
        reject(
            f"bore_depth {bore_depth} leaves no floor below height {height}: "
            "lower bore_depth or raise height",
            param="bore_depth",
        )

    bore_r = (shaft_diameter + bore_clearance) / 2.0
    bore_flat_x = (shaft_across_flat + bore_clearance) - bore_r
    if bore_flat_x >= bore_r:
        reject(
            "bore_clearance leaves the bore round instead of D-shaped: "
            "raise bore_clearance or check shaft_across_flat",
            param="bore_clearance",
        )

    body = extrude(RegularPolygon(grip_across_flats / 2.0, 6, major_radius=False), height)

    cut_width = 2 * bore_r + 10.0
    bore_profile = Circle(bore_r) - Pos(bore_flat_x + cut_width / 2.0, 0) * Rectangle(
        cut_width, cut_width
    )
    bore_solid = Pos(0, 0, height - bore_depth) * extrude(bore_profile, bore_depth)

    knob = body - bore_solid

    if draft:
        return knob

    bed = knob.bounding_box().min.Z
    concave = set(concave_edges(knob))
    keep = knob.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed and e not in concave
    )
    return polish(knob, keep, 1.0)
