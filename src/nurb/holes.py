"""Support-free counterbores: the stepped bridging hole.

A counterbored hole prints mouth toward the bed, because that is where the screw head
comes from. That floats its ceiling: the shelf the head bears on is laid flat over the
open bore, and the smaller hole's first rim is a circle drawn on air. Slicers print it
badly or demand support inside a pocket nobody can clean.

The print-farm fix is sequential bridging, two sacrificial layers between bore and
hole. First a slot the hole's width, bridged chord-to-chord across the bore; then the
same slot turned ninety degrees, bridged across the first; then the round hole starts
over the crossing, ringed by material that bridges the short way at every point. Each
layer spans only what the one before it laid, so the whole stack prints support-free
and the screw never notices: the steps sit above the head's seat and every opening
clears the shaft.
"""

from build123d import Align, Box, Cylinder, Pos

# How far the cutter reaches past its own mouth, so a caller seating the mouth flush
# on the part's bottom face never leaves a coplanar-face boolean to the kernel's mood.
LEAD = 1.0

_SEATED = (Align.CENTER, Align.CENTER, Align.MIN)


def counterbore(hole_dia, head_dia, head_depth, depth, layer=1.0):
    """The negative space of a counterbored hole whose ceiling prints without support.

    Returns a cutter to subtract: mouth centred at the origin opening downward, hole
    rising up +z, which is a counterbore printed the way one is used, head toward the
    bed. `hole_dia` is the shaft's hole, `head_dia` and `head_depth` the head's pocket,
    `depth` the full reach of the hole from the mouth. Position it at the part's bottom
    face; the mouth runs 1mm long so a flush seat still cuts clean, and `depth` can
    be generous for a through hole, the excess sticks out the top harmlessly.

    Between pocket and hole sit two bridge steps, each `layer` tall: a slot across the
    bore, then the same slot turned ninety degrees across the first. Anything at or
    above the printed layer height bridges; the default is 1mm, exactly the printer's
    min_wall, so the sacrificial laminae between the steps never read as thin walls to
    the checker. Shrink it only when depth is tight, and expect min_wall to notice.
    """
    if hole_dia <= 0 or head_dia <= 0 or head_depth <= 0 or layer <= 0:
        raise ValueError("counterbore() needs positive dimensions throughout")
    if head_dia <= hole_dia:
        raise ValueError(
            f"a counterbore needs a head pocket wider than its hole, got head_dia "
            f"{head_dia:g} against hole_dia {hole_dia:g}. For a plain hole, cut a Cylinder."
        )
    if depth < head_depth + 2 * layer + 1e-9:
        raise ValueError(
            f"depth {depth:g} leaves no hole above the pocket: the head takes "
            f"{head_depth:g} and the two bridge steps take {2 * layer:g}"
        )
    pocket = Pos(0, 0, -LEAD) * Cylinder(head_dia / 2, head_depth + LEAD, align=_SEATED)
    # The steps stay inside the pocket's circle: a slot cut square would notch the wall.
    inside = Pos(0, 0, head_depth) * Cylinder(head_dia / 2, 2 * layer, align=_SEATED)
    first = Pos(0, 0, head_depth) * Box(head_dia, hole_dia, layer, align=_SEATED) & inside
    second = Pos(0, 0, head_depth + layer) * Box(hole_dia, head_dia, layer, align=_SEATED) & inside
    shaft = Pos(0, 0, -LEAD) * Cylinder(hole_dia / 2, depth + LEAD, align=_SEATED)
    return pocket + first + second + shaft
