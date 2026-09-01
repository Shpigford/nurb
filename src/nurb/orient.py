"""Diagonal print orientation: stand a part on a corner, on a flat it can grip.

Every check judges a solid the way it sits, building up in +z. So orientation is not
metadata to carry around; it is geometry. A part that should print tilted gets tilted,
seated on the bed, and handed to the same rules as any other solid, and they all stay
right without knowing anything happened.

The one piece of new physics is the facet. A tilted part meets the bed along an edge,
and an edge is a single extrusion line on the first layer: it peels, and the print tips.
The corner gets shaved flat so the part stands on a real face. The doctrine's number is
2mm minimum, measured across the flat.

Past about twenty times the facet in height, adhesion is holding a lever, and the fix is
fins: break-away triangular walls behind the lean, grown here because the recipe is
print-farm practice with fixed numbers, not a judgement. The fin body stays clear of the
part; only the tines touch, each a single-layer bead that rubs off with a fingernail.
"""

from math import radians, sin

from build123d import Axis, Box, CenterOf, Keep, Plane, Polygon, Pos, Vector, extrude, split

from . import supports
from .checks import LEVERAGE

FIN_THICK = 1.0  # a couple of beads of wall: stiff enough to hold, thin enough to lift
                 # off whole, and exactly the printer's min_wall so the checker does
                 # not read a deliberate sacrificial blade as a defect
FIN_RISE = 0.7  # how far up the part a fin reaches, as a fraction of its height
GAP = 0.7  # horizontal clearance between fin and part, about half a millimetre square-on
TINE = 0.3  # a tine is one layer tall, so it prints as a single continuous bead
TINE_WIDE = 0.5  # and a bead or so wide, so it rubs off without a scar
BITE = 0.6  # how far a tine reaches into each body, so both ends actually fuse
PAD_THICK = 1.0  # the doctrine's base pad: thick enough to peel without leaving veneer
PAD_MARGIN = 1.9  # pad width beyond the fin blade, kept clear of the 5mm stance strip


def stand(shape, tilt=45.0, axis=Axis.Y, facet=2.0, fins=True):
    """Tilt a part for diagonal printing and shave a flat for it to stand on.

    Rotates `tilt` degrees about the horizontal `axis`, seats the part on the bed, and
    cuts the corner below the bed plane away so the part stands on a flat `facet` wide
    instead of a knife edge. The result is real geometry in print orientation: every
    check, the viewer, and export judge it exactly as it will build.

    `facet` is the width of the flat across the down corner, exact when that corner is
    square. A wider corner gives a wider flat, which is fine: the doctrine's 2mm is a
    minimum. The sign and size of `tilt` pick which corner goes down, and past 90 is
    often the point: an L stands on the outside of its elbow, legs up, which is its
    model rolled about 135 degrees with the sign set by which way it faces. Check the
    result rather than reasoning about the sign. Stand a part on the corner that
    grounds all of it, the lowest such stance by preference; a corner that leaves some
    region hanging in air is the `floating` finding.

    A part standing taller than the adhesion rule allows grows break-away support fins
    behind its lean, one at each side, tined on and rubbed off after printing. `fins`
    is on by default and only builds them when the stance earns them; pass False to
    see the raw stability finding instead. Fins currently understand the default Y
    tilt axis only.

    Run the polish pass before this, in the functional orientation. The facet's own
    edges stay unpolished, the same as any bed-contact face.
    """
    if abs(sin(radians(2 * tilt))) < 0.05:
        raise ValueError(
            f"stand() needs a tilt away from 0, 90 and 180 degrees, got {tilt:g}. "
            "At those angles a flat face is already down and there is no corner to "
            "stand on; this is for diagonal prints."
        )
    if facet <= 0:
        raise ValueError(f"facet is the width of the bed flat in mm, got {facet:g}")
    if abs(axis.direction.normalized().dot(Vector(0, 0, 1))) > 1e-6:
        raise ValueError(
            "stand() needs a horizontal rotation axis; an axis with a Z component "
            "does not tilt the part cleanly toward the bed."
        )
    tilted = shape.rotate(axis, tilt)
    # For a square corner tilted t, a cut d deep makes a flat 2*d/|sin(2t)| wide, so
    # d = facet * |sin(2t)| / 2. At 45 or 135 degrees that is half the facet.
    depth = facet * abs(sin(radians(2 * tilt))) / 2
    drop = -tilted.bounding_box().min.Z - depth
    # Any `supported()` mark was made while modelling upright, so it describes where the
    # feature was, not where it is about to print. Same rotation, same seating: this is
    # the only operation in the vocabulary that moves a whole finished part.
    supports.remap(lambda marked: Pos(0, 0, drop) * marked.rotate(axis, tilt))
    seated = Pos(0, 0, drop) * tilted
    seated = split(seated, bisect_by=Plane.XY, keep=Keep.TOP)
    height = seated.bounding_box().max.Z
    if not fins or height <= LEVERAGE * facet:
        return seated
    if abs(axis.direction.dot(Vector(0, 1, 0))) < 0.999:
        raise ValueError(
            "stand() grows fins for the default Y tilt axis only; rotate the model "
            "so its tilt is about Y, or pass fins=False and model the fin by hand."
        )
    return seated + _fins(seated, height)


def _underside(seated, s, z):
    """Where the lean-side surface sits at height `z`, in lean coordinates.

    Lean coordinates put outward positive whichever way the part leans: u = s * x.
    Measured off a thin slice rather than derived from the tilt, because the fin has
    to hug the face that is actually there, whatever cut it.
    """
    slab = seated & Pos(0, 0, z) * Box(10000, 10000, 0.05)
    box = slab.bounding_box()
    return s * (box.max.X if s > 0 else box.min.X)


def _fins(seated, height):
    """Two break-away fins behind the lean, with their pads and tines.

    The recipe is print-farm practice: a thin wall whose top edge parallels the
    part's leaning underside across a small gap, standing on a 1mm pad for its own
    adhesion, joined to the part by a handful of single-layer tines biased toward
    the bottom, where the young print is least stable. One fin at each side of the
    part, because scars hide at corners and two fins also stop twist.
    """
    bb = seated.bounding_box()
    bed = [f for f in seated.faces() if abs(f.bounding_box().max.Z) < 1e-6]
    footing = sum(f.center().X * f.area for f in bed) / sum(f.area for f in bed)
    s = 1.0 if seated.center(CenterOf.MASS).X >= footing else -1.0

    # The lean line u(z) = c + m*z, fitted mid-part where the silhouette is the lean
    # face itself rather than whatever bulk sits near the bed.
    z1, z2 = 0.45 * height, 0.65 * height
    u1, u2 = _underside(seated, s, z1), _underside(seated, s, z2)
    m = max((u2 - u1) / (z2 - z1), 0.0)
    c = u1 - m * z1
    # The fin foot starts beyond whatever the part puts near the bed, grip lumps
    # included, so the blade breaks away instead of fusing into them.
    start = max(c + GAP, _underside(seated, s, PAD_THICK) + GAP)
    rise = FIN_RISE * height
    lip = min((start - c - GAP) / m if m > 0 else 0.0, rise * 0.5)

    def at(u, z):
        return (s * u, z)

    outer = c + GAP + m * rise
    points = [at(start, 0), at(outer, 0), at(outer, rise)]
    if lip > 0:
        points.append(at(start, lip))
    blade = extrude(Plane.XZ * Polygon(*points, align=None), FIN_THICK)
    pad_u = (min(start, outer), max(start, outer) + PAD_MARGIN)
    pad = Box(pad_u[1] - pad_u[0], FIN_THICK + 2 * PAD_MARGIN, PAD_THICK)
    pad = Pos(s * (pad_u[0] + pad_u[1]) / 2, 0, PAD_THICK / 2) * pad

    # Tines every so often up the blade, geometrically spaced so most sit low.
    heights, z = [], lip + 2.0
    while z < rise and len(heights) < 6:
        heights.append(z)
        z = lip + 2.0 + (z - lip) * 1.8
    grown = []
    for edge in (bb.min.Y, bb.max.Y - FIN_THICK):
        y = edge - blade.bounding_box().min.Y
        grown.append(Pos(0, y, 0) * blade)
        grown.append(Pos(0, edge + FIN_THICK / 2 - pad.center().Y, 0) * pad)
        for z in heights:
            u0, u1t = c + m * z - BITE, c + GAP + m * z + BITE
            tine = Box(u1t - u0, TINE_WIDE, TINE)
            grown.append(Pos(s * (u0 + u1t) / 2, edge + FIN_THICK / 2, z + TINE / 2) * tine)
    body = grown[0]
    for piece in grown[1:]:
        body = body + piece
    return body
