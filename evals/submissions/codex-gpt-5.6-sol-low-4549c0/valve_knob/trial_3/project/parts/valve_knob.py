from nurb import *


@part
def valve_knob(
    shaft_diameter: float = 8.0,
    shaft_across_flat: float = 6.5,
    draft=False,
):
    """A low, two-lobed replacement knob for a D-shaped valve stem.

    shaft_diameter: measured diameter of the valve's D-shaped stem
    shaft_across_flat: measured distance from the stem flat to the opposite arc
    """
    if shaft_diameter <= 0:
        reject("shaft_diameter must be greater than zero", param="shaft_diameter")
    if not 0 < shaft_across_flat < shaft_diameter:
        reject(
            "shaft_across_flat must be greater than zero and less than shaft_diameter",
            param="shaft_across_flat",
        )

    height = 16.0
    core_radius = 15.0

    # The cylindrical core guarantees a 30 mm minimum grip at every azimuth.
    body = Cylinder(core_radius, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    for x in (-14.0, 14.0):
        body = body + Cylinder(
            5.0, height, align=(Align.CENTER, Align.CENTER, Align.MIN)
        ).translate((x, 0, 0))

    # Clearance lies safely above the +0.3 mm test stem, but below the +1.0 mm
    # no-rattle stem.  The flat is on +X, matching the installed stem datum.
    bore_diameter = shaft_diameter + 0.5
    bore_across_flat = shaft_across_flat + 0.5
    bore_radius = bore_diameter / 2.0
    flat_x = bore_across_flat - bore_radius
    bore_depth = 12.0
    bore = Cylinder(
        bore_radius,
        bore_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).translate((0, 0, height - bore_depth))
    flat_clip = Box(
        bore_radius * 2.0,
        bore_radius * 2.0,
        bore_depth,
        align=(Align.MAX, Align.CENTER, Align.MIN),
    ).translate((flat_x, 0, height - bore_depth))
    bore = bore & flat_clip
    body = body - bore

    # The circular top and bottom rims are intentionally left square: the bottom
    # is the print bed, while the top surrounds the fit-critical socket mouth.
    return body
