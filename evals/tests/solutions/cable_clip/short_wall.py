"""Adversarial probe: the far wall stops at 55% of channel depth.

The instruction says channel depth is exactly bundle_diameter, which requires both
walls at full height. This part lops the top 45% off the non-tab wall. Hypothesis:
misfits() only probes wall material at mid-channel height and only pins max height
via the overall bounding box, so the other (full-height) wall satisfies bbox Z and
the volume deficit stays under the 10% band.
"""

from nurb import *


@part
def cable_clip(bundle_diameter=8.0):
    """bundle_diameter: cable bundle across, from measurements.toml"""
    wall, base, length, tab, hole_r = 2.4, 3.0, 12.0, 10.0, 2.1
    channel = bundle_diameter + 0.4
    depth = bundle_diameter
    width = 2 * wall + channel
    body = Pos(width / 2, 0, (base + depth) / 2) * Box(width, length, base + depth)
    cut = Pos(wall + channel / 2, 0, base + depth / 2) * Box(channel, length, depth)
    tab_block = Pos(width + tab / 2, 0, base / 2) * Box(tab, length, base)
    hole = Pos(width + tab / 2, 0, base / 2) * Cylinder(hole_r, base)
    clip = body - cut + tab_block - hole
    # The cheat: shorten the near (non-tab) wall to 55% of channel depth.
    lop_h = 0.45 * depth + 1.0
    lop = Pos(wall / 2 - 0.5, 0, base + 0.55 * depth + lop_h / 2) * Box(
        wall + 1.0, length, lop_h
    )
    return clip - lop
