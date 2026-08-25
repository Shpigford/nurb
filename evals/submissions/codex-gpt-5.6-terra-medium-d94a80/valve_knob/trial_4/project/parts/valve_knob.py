from nurb import *


@part
def valve_knob(
    shaft_diameter: float = measured("shaft_diameter"),
    shaft_across_flat: float = measured("shaft_across_flat"),
    knob_width: float = 30.0,
    knob_height: float = 14.0,
    fit_clearance: float = 0.4,
):
    """A compact four-flat replacement knob for an 8 mm D-shaft.

    shaft_diameter: diameter of the round side of the valve stem
    shaft_across_flat: distance from the stem flat to its opposite round side
    knob_width: width across the knob's straight grip flats
    knob_height: height of the knob as printed
    fit_clearance: radial clearance around the D-shaped stem
    """
    if shaft_diameter <= 0 or shaft_across_flat <= 0:
        reject("The shaft dimensions must be positive.", param="shaft_diameter")
    if shaft_across_flat > shaft_diameter:
        reject("shaft_across_flat cannot exceed shaft_diameter.", param="shaft_across_flat")
    if knob_width < 28.0:
        reject("knob_width must be at least 28 mm for a usable wet-hand grip.", param="knob_width")
    if knob_height < 12.0:
        reject("knob_height must be at least 12 mm to cover the valve stem.", param="knob_height")

    # The bore is intentionally modelled in the print orientation: open at +Z.
    # Its flat is at +X, matching the measured shaft orientation.
    bore_radius = shaft_diameter / 2 + fit_clearance
    bore_flat_x = shaft_across_flat - shaft_diameter / 2 + fit_clearance
    bore_depth = min(12.5, knob_height - 1.0)

    body = Box(knob_width, knob_width, knob_height)
    bore_center_z = knob_height / 2 - bore_depth / 2 + 0.05
    round_bore = Pos(0, 0, bore_center_z) * Cylinder(bore_radius, bore_depth)
    flat_limit = Pos(bore_flat_x - bore_radius, 0, bore_center_z) * Box(
        2 * bore_radius, 2 * bore_radius, bore_depth
    )
    d_bore = round_bore & flat_limit
    return body - d_bore
