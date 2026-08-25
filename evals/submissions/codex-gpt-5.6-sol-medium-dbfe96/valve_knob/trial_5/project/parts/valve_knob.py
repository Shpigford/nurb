from math import sqrt

from nurb import *


_SHAFT_DIAMETER = measured("shaft_diameter")
_SHAFT_ACROSS_FLAT = measured("shaft_across_flat")


@part
def valve_knob(
    shaft_diameter=_SHAFT_DIAMETER,
    shaft_across_flat=_SHAFT_ACROSS_FLAT,
):
    """A compact replacement knob for a D-shaped valve stem.

    shaft_diameter: diameter of the round portion of the valve stem
    shaft_across_flat: distance from the stem's flat to its opposite round side
    """
    clearance = 0.5
    knob_height = 18.0
    grip_across_flats = 28.6
    bore_depth = 12.5

    if shaft_diameter <= 0.0:
        reject("shaft_diameter must be greater than zero", param="shaft_diameter")
    if shaft_across_flat <= shaft_diameter / 2.0:
        reject(
            "shaft_across_flat must be greater than half shaft_diameter",
            param="shaft_across_flat",
        )
    if shaft_across_flat >= shaft_diameter:
        reject(
            "shaft_across_flat must be smaller than shaft_diameter to form a D-shaft",
            param="shaft_across_flat",
        )

    grip_radius = grip_across_flats / sqrt(3.0)
    body = extrude(RegularPolygon(grip_radius, 6), knob_height)

    bore_diameter = shaft_diameter + clearance
    bore_across_flat = shaft_across_flat + clearance
    bore_radius = bore_diameter / 2.0
    bore_floor = knob_height - bore_depth

    round_bore = Pos(0.0, 0.0, bore_floor) * Cylinder(
        bore_radius,
        bore_depth + 0.1,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    flat_clip = Pos(-bore_radius, 0.0, bore_floor) * Box(
        bore_across_flat,
        bore_diameter,
        bore_depth + 0.1,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    d_bore = round_bore & flat_clip

    return body - d_bore
