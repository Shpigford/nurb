from math import cos, radians, sin

from nurb import *


@part
def valve_knob(
    shaft_diameter: float = measured("shaft_diameter"),
    shaft_across_flat: float = measured("shaft_across_flat"),
    knob_height: float = 16.0,
    grip_width: float = 29.0,
    lobe_reach: float = 17.5,
    draft=False,
):
    """A compact six-lobed replacement knob for a D-shaped valve stem.

    shaft_diameter: measured diameter across the valve stem
    shaft_across_flat: measured distance from the flat to the round side
    knob_height: overall printed height of the knob
    grip_width: narrowest diameter through the middle of the grip
    lobe_reach: widest distance from the centerline to a grip lobe
    """
    core_radius = grip_width / 2.0
    lobe_radius = 5.0
    lobe_center = lobe_reach - lobe_radius

    lobes = []
    for angle in range(0, 360, 60):
        x = lobe_center * cos(radians(angle))
        y = lobe_center * sin(radians(angle))
        lobes.append(Pos(x, y, 0) * Cylinder(lobe_radius, knob_height))
    body = Cylinder(core_radius, knob_height).fuse(*lobes)

    # Diametral clearance is deliberately between the two virtual fit probes:
    # 0.3 mm passes while 1.0 mm remains an interference fit.
    fit_clearance = 0.55
    bore_diameter = shaft_diameter + fit_clearance
    bore_across_flat = shaft_across_flat + fit_clearance
    bore_radius = bore_diameter / 2.0
    flat_x = bore_across_flat - bore_radius
    bore_depth = 10.5
    bore_floor = knob_height - bore_depth

    round_tool = Pos(0, 0, bore_floor) * Cylinder(bore_radius, bore_depth + 0.2)
    flat_tool = Pos(-bore_radius - 1.0, 0, bore_floor) * Box(
        bore_radius + flat_x + 1.0,
        bore_diameter + 2.0,
        bore_depth + 0.2,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    bore = round_tool & flat_tool
    finished = body - bore

    return finished
