from nurb import *
from build123d import Align, Box, Cylinder, Pos


@part
def valve_knob(
    shaft_diameter: float = 8.0,
    shaft_across_flat: float = 6.5,
):
    """A support-free lobed replacement knob for a D-shaped valve stem.

    shaft_diameter: measured diameter across the valve stem
    shaft_across_flat: measured distance from the flat to the round side
    """
    height = 16.0
    body = Cylinder(14.0, height, align=(Align.CENTER, Align.CENTER, Align.MIN))

    # Four broad lobes provide positive purchase without spending the material
    # of a full circle at their maximum reach.
    for x, y in ((13.5, 0.0), (-13.5, 0.0), (0.0, 13.5), (0.0, -13.5)):
        body = body + Pos(x, y, 0) * Cylinder(
            5.0, height, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )

    # The bore opens upward and stops 2 mm above the bed.  Its diametral and
    # across-flat allowances sit between the specified pass and jam gauges.
    bore_diameter = shaft_diameter + 0.6
    bore_across_flat = shaft_across_flat + 0.6
    bore_radius = bore_diameter / 2.0
    flat_x = -bore_radius + bore_across_flat
    round_bore = Pos(0, 0, 2.0) * Cylinder(
        bore_radius,
        height - 2.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    keep_round_side = Pos(-bore_radius, -bore_radius, 2.0) * Box(
        bore_diameter,
        bore_diameter,
        height - 2.0,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    d_bore = round_bore & keep_round_side
    d_bore = d_bore & Pos(-bore_radius, -bore_radius, 2.0) * Box(
        flat_x + bore_radius,
        bore_diameter,
        height - 2.0,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )

    return body - d_bore
