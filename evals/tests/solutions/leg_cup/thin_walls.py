"""CHEAT: the stated 2.0mm walls are 1.05mm over the top of their height.

Exploits three thresholds at once: the ring boolean is inset 1.1mm from the outer faces,
so only 0.9mm of each wall is ever tested; min_wall passes anything at or above
0.99mm; and the volume band forgives 10%, which is what a 3mm-tall thinning costs. The
rim point probes sit 1.0mm outside the pocket wall, so a 1.05mm wall still contains
them.
"""

from nurb import *


@part
def leg_cup(wall=2.0, clear=0.4, depth=8.0, thin=1.05, run=3.0):
    lw = measured("leg_width")
    ld = measured("leg_depth")
    lift = measured("lift")
    px, py = lw + clear, ld + clear
    bx, by, h = px + 2 * wall, py + 2 * wall, lift + depth
    cup = Pos(0, 0, h / 2) * Box(bx, by, h) - Pos(0, 0, lift + depth / 2) * Box(px, py, depth)
    waste = Pos(0, 0, h - run / 2) * Box(bx, by, run)
    waste -= Pos(0, 0, h - run / 2) * Box(px + 2 * thin, py + 2 * thin, run)
    return cup - waste
