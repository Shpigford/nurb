from math import cos, pi, sin

from nurb import *


@part
def valve_knob(
    shaft_diameter=8.0,
    shaft_across_flat=6.5,
    knob_height=16.0,
    draft=False,
):
    """A three-lobed replacement valve handle, printed bore-up.

    shaft_diameter: measured round diameter of the valve's D-shaped stem
    shaft_across_flat: measured distance from the stem flat to its round side
    knob_height: overall printed height; the stem socket remains 3 mm above the bed
    """
    if shaft_diameter <= 0.0 or shaft_across_flat <= 0.0:
        reject("shaft dimensions must be positive", param="shaft_diameter")
    if shaft_across_flat >= shaft_diameter:
        reject(
            "shaft_across_flat must be smaller than shaft_diameter for a D-shaft",
            param="shaft_across_flat",
        )
    if knob_height < 15.0:
        reject("knob_height must be at least 15 mm to retain a 12 mm-deep socket", param="knob_height")

    # The socket adds 0.4 mm radially and 0.8 mm across the D profile. This
    # clears the specified 0.3 mm virtual growth, but a 1.0 mm growth cannot enter.
    bore_radius = shaft_diameter / 2.0 + 0.4
    bore_across_flat = shaft_across_flat + 0.8
    bore_flat_x = -bore_radius + bore_across_flat
    bore_floor = 3.0
    bore_depth = knob_height - bore_floor

    # A 28 mm circular core guarantees the narrow grip dimension. Three grounded
    # lobes give wet hands a positive turning purchase without wasting material.
    body = Cylinder(14.0, knob_height)
    for angle in (0.0, 120.0, 240.0):
        radians = angle * pi / 180.0
        lobe = Cylinder(4.0, knob_height).translate(
            (14.5 * cos(radians), 14.5 * sin(radians), 0.0)
        )
        body = body + lobe

    # Flat faces +X, matching the installed stem orientation. The cutter opens
    # upward and leaves a continuous 3 mm bed-side floor.
    round_socket = Cylinder(bore_radius, bore_depth).translate((0.0, 0.0, bore_floor))
    flat_cut = Box(
        bore_radius * 2.0 + 4.0,
        bore_radius * 2.0 + 4.0,
        bore_depth + 2.0,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    ).translate((bore_flat_x, 0.0, bore_floor - 1.0))
    d_socket = round_socket - flat_cut
    return body - d_socket
