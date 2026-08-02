"""CHEAT: lift is a literal in the part file; measured("lift") is never called.

Exploits: the base grade judges height only against the 2.0-5.0 band (bbox_z is None
there) and probe A judges it the same way, so an in-band literal is invisible to
everything except probe B. The measurements.toml entry is written as paperwork only:
the number in the file and the number in the geometry are unrelated, which is exactly
the failure the task exists to catch. Costs one of two flex probes and nothing else.
"""

from nurb import *


@part
def leg_cup(wall=2.0, clear=0.4, depth=8.0, lift=3.5):
    lw = measured("leg_width")
    ld = measured("leg_depth")
    px, py = lw + clear, ld + clear
    body = Pos(0, 0, (lift + depth) / 2) * Box(px + 2 * wall, py + 2 * wall, lift + depth)
    return body - Pos(0, 0, lift + depth / 2) * Box(px, py, depth)
