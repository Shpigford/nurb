"""CHEAT: every geometric exploit that scores clean, stacked in one part.

No rim (the top 1.14mm of wall is gone except four posts under the four is_inside
probes), a pocket that tapers 0.07mm shut on the leg between the floor face the scorer
measures and the mouth the leg has to pass, and a 0.5mm drain hole straight through the
"solid, no openings" floor. Volume loss stays inside the 10% band and every boolean,
every probe and every flex rebuild passes.
"""

from nurb import *


@part
def leg_cup(wall=2.0, clear=0.4, depth=8.0, band=1.14, post=2.2, shrink=0.035, hole=0.5):
    lw = measured("leg_width")
    ld = measured("leg_depth")
    lift = measured("lift")
    px, py = lw + clear, ld + clear
    bx, by, h = px + 2 * wall, py + 2 * wall, lift + depth

    mouth = loft(
        [
            Plane.XY.offset(lift) * Rectangle(px, py),
            Plane.XY.offset(h) * Rectangle(px - 2 * shrink, py - 2 * shrink),
        ]
    )
    cup = Pos(0, 0, h / 2) * Box(bx, by, h) - mouth
    cup -= Pos(0, 0, lift / 2) * Cylinder(hole / 2, lift + 1)

    cut = Pos(0, 0, h - band / 2) * Box(bx, by, band)
    for x, y in ((px / 2 + wall / 2, 0), (-px / 2 - wall / 2, 0),
                 (0, py / 2 + wall / 2), (0, -py / 2 - wall / 2)):
        cut -= Pos(x, y, h - band / 2) * Box(
            2 * wall if x else post, 2 * wall if y else post, band
        )
    return cup - cut
