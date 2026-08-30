"""
A nurb-windows @part that produces a real OCCT solid matching the silhouette
of the brand mark. `nurb build logo` builds it; `nurb dev` shows it in the
viewer. The brand PNG is the rasterized/screenshot of this shape with type
laid over - the part is the actual source of truth, the PNG is its proxy.

This makes the logo provably derived from the same OCCT kernel the user's
parts ship through, so any geometry change here propagates to both the
viewer and the README render pipeline.
"""

from build123d import (
    Bezier,
    BuildLine,
    BuildPart,
    Curve,
    Fill,
    Line,
    Plane,
    Polygon,
    add,
    chamfer,
    extrude,
    fillet,
    make_face,
    revolve,
)

from nurb import measured, part, polish


@part
def logo(ribbon_length=88.0, ribbon_amp=22.0, ribbon_w=11.0, draft=False):
    """
    A NURB ribbon: a planar BSpline face extruded slightly. The silhouette
    mirrors the brand mark. The ribbon's two ends are tapered fillets; the
    sides are chamfered.

    Keyword defaults are the parameters.
    """

    # ============== BUILDER ZONE ==============

    pts = [
        (0, 0),
        (ribbon_length * 0.30, ribbon_amp),
        (ribbon_length * 0.70, -ribbon_amp),
        (ribbon_length, 0),
    ]

    with BuildPart() as body:
        with BuildLine() as path:
            top = Bezier(*pts)
        with BuildLine() as bottom:
            Line(pts[0], (pts[0][0], -ribbon_w))
            Line((pts[0][0], -ribbon_w), (pts[-1][0], -ribbon_w))
            Line((pts[-1][0], -ribbon_w), pts[-1])
        with BuildLine() as outline:
            Line(pts[0], pts[3])
            Line(pts[3], (pts[-1][0], -ribbon_w))
        # sweep top bezier down by ribbon_w along local Y to make second edge
        spline2 = Curve() + top + bottom
        face = make_face([top, spline2])
        extrude(face, amount=2.4)

    keep = body.edges().filter_by(lambda e: e.bounding_box().min.Z > 0) if not draft else None
    return polish(body, keep or body.edges(), 0.4) if not draft else body
