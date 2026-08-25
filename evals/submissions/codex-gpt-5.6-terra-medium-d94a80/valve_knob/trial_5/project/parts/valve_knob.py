from nurb import *


@part
def valve_knob(
    shaft_diameter: float = measured("shaft_diameter"),
    shaft_across_flat: float = measured("shaft_across_flat"),
    bore_clearance: float = 0.5,
    knob_height: float = 14.0,
):
    """A four-lobed replacement knob for an 8 mm D-shaft.

    shaft_diameter: diameter across the round portion of the valve stem
    shaft_across_flat: distance from the stem's flat to its opposite round side
    bore_clearance: extra room in both measured bore dimensions for an easy fit
    knob_height: overall printed height of the knob
    """
    # The flat faces +X.  A D profile is the circular shaft clipped at this plane.
    bore_diameter = shaft_diameter + bore_clearance
    bore_across_flat = shaft_across_flat + bore_clearance
    bore_radius = bore_diameter / 2
    flat_x = bore_across_flat - bore_radius

    # A compact 32 mm core supplies the broad, stable print footprint.  The four
    # small pads give wet fingers positive lobes without making a bulky knob.
    core = Cylinder(16, knob_height)
    pads = [
        Pos(15, 0) * Cylinder(4, knob_height),
        Pos(-15, 0) * Cylinder(4, knob_height),
        Pos(0, 15) * Cylinder(4, knob_height),
        Pos(0, -15) * Cylinder(4, knob_height),
    ]
    outer = core
    for pad in pads:
        outer += pad

    # Solids are centred vertically by default: this reaches from 2 mm above the
    # bed to the top face, leaving a 2 mm floor and a full 12 mm stem engagement.
    bore_cylinder = Pos(0, 0, 1) * Cylinder(bore_radius, knob_height - 2)
    bore_limit = Pos(flat_x - 10, 0, 1) * Box(20, 20, knob_height - 2)
    d_bore = bore_cylinder & bore_limit
    return outer - d_bore
