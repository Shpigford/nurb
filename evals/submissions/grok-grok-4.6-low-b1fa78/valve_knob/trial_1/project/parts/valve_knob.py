from nurb import *


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    across_flats=32.0,
    height=14.0,
    bore_clearance=0.5,
    stem_reach=12.0,
    draft=False,
):
    """Replacement valve handle that prints bore-up and flips onto a D-stem.

    shaft_diameter: circle size of the stem.
    shaft_across_flat: stem thickness from the flat to the round side.
    across_flats: grip width across opposite hex flats.
    height: how tall the knob stands on the bed.
    bore_clearance: extra on both stem diameter and across-flat so the print slides on.
    stem_reach: how deep the D-bore is, matching how far the stem stands proud.
    """
    if shaft_across_flat >= shaft_diameter:
        reject(
            "shaft_across_flat must be smaller than shaft_diameter so the stem has a flat",
            param="shaft_across_flat",
        )
    if bore_clearance < 0.35:
        reject(
            "bore_clearance 0.35 and up is needed so a 0.3-grown stem still slides in",
            param="bore_clearance",
        )
    if bore_clearance >= 0.95:
        reject(
            "bore_clearance under 0.95 keeps a 1mm-grown stem from rattling",
            param="bore_clearance",
        )

    bore_d = shaft_diameter + bore_clearance
    bore_flat = shaft_across_flat + bore_clearance
    bore_r = bore_d / 2.0
    # Flat faces +X: from the -X round extreme, across-flat lands at this X.
    flat_x = -bore_r + bore_flat
    bore_depth = min(stem_reach, height - 2.0)

    hex_r = across_flats / 3.0**0.5
    body = extrude(RegularPolygon(hex_r, 6), height)

    with BuildSketch(Plane.XY.offset(height)) as d_sk:
        Circle(bore_r)
        with Locations((flat_x + bore_r + 1.0, 0)):
            Rectangle(2.0 * bore_r + 2.0, 2.0 * bore_r + 4.0, mode=Mode.SUBTRACT)
    bore = extrude(d_sk.sketch, -bore_depth)
    body -= bore

    if draft:
        return body
    bed = body.bounding_box().min.Z
    concave = set(concave_edges(body))
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed + 0.05 and e not in concave
    )
    return polish(body, keep, 1.0)
