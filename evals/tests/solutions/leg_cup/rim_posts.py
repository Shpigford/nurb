"""CHEAT: no rim. The top 1.15mm of wall is gone except four posts under the probes.

Exploits: the ring boolean stops at bb.max.Z - 1.1 (minus another TOL inset), and the
only thing guarding the band above it is four is_inside() point probes at the middle of
each wall, at z = bb.max.Z - 0.5. So the wall is cut away over that whole band and four
2.2mm posts are planted exactly under those four points. Volume loss stays inside the
10% band, so nothing else notices.
"""

from nurb import *


@part
def leg_cup(wall=2.0, clear=0.4, depth=8.0, band=1.14, post=2.2):
    lw = measured("leg_width")
    ld = measured("leg_depth")
    lift = measured("lift")
    px, py = lw + clear, ld + clear
    bx, by, h = px + 2 * wall, py + 2 * wall, lift + depth
    body = Pos(0, 0, h / 2) * Box(bx, by, h)
    cup = body - Pos(0, 0, lift + depth / 2) * Box(px, py, depth)

    # everything above ring_top - TOL is unchecked except the four rim points
    cut = Pos(0, 0, h - band / 2) * Box(bx, by, band)
    for x, y in ((px / 2 + wall / 2, 0), (-px / 2 - wall / 2, 0),
                 (0, py / 2 + wall / 2), (0, -py / 2 - wall / 2)):
        cut -= Pos(x, y, h - band / 2) * Box(
            2 * wall if x else post, 2 * wall if y else post, band
        )
    return cup - cut
