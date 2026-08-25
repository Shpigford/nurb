"""A three-lobed replacement handle for an 8 mm D-shaft valve stem."""

from math import cos, radians, sin

from nurb import *


@part
def valve_knob(
    shaft_diameter: float = 8.0,
    shaft_across_flat: float = 6.5,
    knob_height: float = 18.0,
    grip_diameter: float = 28.0,
    lobe_reach: float = 19.0,
    fit_clearance: float = 0.4,
):
    """A compact, wet-hand-friendly valve knob.

    shaft_diameter: diameter across the round side of the valve's D-shaped stem
    shaft_across_flat: distance from the stem flat to its opposite round side
    knob_height: overall printed height of the knob
    grip_diameter: minimum body width through the middle of the knob
    lobe_reach: distance from the center to the tips of the three grip lobes
    fit_clearance: radial and flat clearance around the measured stem

    The bore opens upward while printing.  Its flat is on the +X side, so after
    the knob is flipped onto the valve it keys to a stem whose flat faces +X.
    """
    if shaft_across_flat >= shaft_diameter:
        reject("shaft_across_flat must be smaller than shaft_diameter", "shaft_across_flat")
    if knob_height < 14.0:
        reject("knob_height needs a 14 mm minimum for a durable bore floor", "knob_height")

    body_radius = grip_diameter / 2
    lobe_radius = 4.5
    lobe_center = lobe_reach - lobe_radius

    knob = Cylinder(body_radius, knob_height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    for angle in (0, 120, 240):
        a = radians(angle)
        lobe = Cylinder(lobe_radius, knob_height, align=(Align.CENTER, Align.CENTER, Align.MIN))
        lobe = lobe.moved(Location((lobe_center * cos(a), lobe_center * sin(a), 0)))
        knob = knob + lobe
    # A D profile is a round bore clipped by the +X flat.  The two shaft
    # measurements independently set the diameter and flat location.
    bore_radius = (shaft_diameter + 2 * fit_clearance) / 2
    bore_across_flat = shaft_across_flat + 2 * fit_clearance
    bore_flat_x = -bore_radius + bore_across_flat
    bore_depth = knob_height - 5.0
    bore = Cylinder(bore_radius, bore_depth, align=(Align.CENTER, Align.CENTER, Align.MIN))
    bore = bore.moved(Location((0, 0, knob_height - bore_depth)))
    flat_removal = Box(
        2 * bore_radius,
        2 * bore_radius,
        bore_depth,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    ).moved(Location((bore_flat_x, 0, knob_height - bore_depth)))
    d_bore = bore.cut(flat_removal)
    knob = knob.cut(d_bore)

    return knob
