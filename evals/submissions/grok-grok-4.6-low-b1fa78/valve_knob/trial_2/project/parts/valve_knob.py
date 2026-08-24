from math import cos, pi

from nurb import *


@part
def valve_knob(
    shaft_diameter=8.0,
    shaft_across_flat=6.5,
    draft=False,
):
    """Replacement knob for a D-shaft valve stem, printed bore-up.

    shaft_diameter: round of the stem, measured across
    shaft_across_flat: stem from the flat to the opposite round
    """
    height = 16.0
    across_flats = 30.0
    floor = 3.0
    clearance = 0.45

    if shaft_across_flat >= shaft_diameter:
        reject(
            "shaft_across_flat must be smaller than shaft_diameter",
            param="shaft_across_flat",
        )

    bore_d = shaft_diameter + clearance
    bore_af = shaft_across_flat + clearance
    bore_r = bore_d / 2.0
    flat_x = bore_af - bore_r

    hex_r = (across_flats / 2.0) / cos(pi / 6.0)
    body = extrude(RegularPolygon(hex_r, 6), amount=height)

    bore_h = height - floor
    cyl = Cylinder(radius=bore_r, height=bore_h)
    cyl = cyl.moved(Location((0, 0, floor + bore_h / 2.0)))
    cutter = Box(24.0, 24.0, bore_h + 2.0)
    cutter = cutter.moved(Location((flat_x + 12.0, 0, floor + bore_h / 2.0)))
    body = body - (cyl - cutter)

    if draft:
        return body
    bed = body.bounding_box().min.Z
    keep = (body.edges() - concave_edges(body)).filter_by(
        lambda e: e.bounding_box().min.Z > bed + 0.05
    )
    return polish(body, keep, 1.0)
