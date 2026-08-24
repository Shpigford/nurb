"""A low-profile, three-lobed replacement knob for an 8 mm D valve stem."""

from math import cos, pi, sin

from nurb import *


@part
def valve_knob(
    shaft_diameter=8.0,
    shaft_across_flat=6.5,
    knob_height=18.0,
    knob_radius=14.0,
    lobe_reach=3.0,
    fit_clearance=0.45,
):
    """ 
    shaft_diameter: measured round diameter of the valve stem.
    shaft_across_flat: distance from the round side to the D-flat on the stem.
    knob_height: overall height of the printed knob.
    knob_radius: radius of the round core that makes the stable print base.
    lobe_reach: how far each of the three grip lobes extends beyond the core.
    fit_clearance: radial clearance around the stem for an easy printed fit.

    The bore is open at the top while printing.  Its straight wall at +X is
    the D-flat, so flipping the print over transfers torque to the stem.
    """
    if shaft_across_flat >= shaft_diameter:
        reject("shaft_across_flat must be smaller than shaft_diameter", "shaft_across_flat")
    if knob_height < 14.0:
        reject("knob_height needs a 12 mm bore and a solid floor", "knob_height")

    # Keep the D profile derived from both recorded stem dimensions.  The
    # circular portion clears in radius; the flat is offset by the same amount.
    stem_radius = shaft_diameter / 2.0
    bore_radius = stem_radius + fit_clearance
    flat_x = -stem_radius + shaft_across_flat + fit_clearance
    bore_depth = 13.0

    body = Cylinder(knob_radius, knob_height)
    # Three generous lobes make the maximum reach substantially larger than
    # the 28 mm minimum waist without wasting the volume of a large disk.
    lobe_radius = lobe_reach + 1.0
    lobe_center = knob_radius - 1.0
    for angle in (0.0, 2.0 * pi / 3.0, 4.0 * pi / 3.0):
        body += Cylinder(lobe_radius, knob_height).translate(
            (lobe_center * cos(angle), lobe_center * sin(angle), 0)
        )

    # Intersecting the round bore with this box creates the D-shaped socket:
    # its flat faces +X and the bore opens from the printed top face.
    round_bore = Cylinder(bore_radius, bore_depth).translate((0, 0, knob_height - bore_depth))
    # Trim the +X side of the circular bore at the derived D-flat position.
    d_limit = Box(flat_x + bore_radius, 2.0 * bore_radius, bore_depth).translate(
        (-bore_radius, -bore_radius, knob_height - bore_depth)
    )
    d_bore = round_bore & d_limit
    return body - d_bore
