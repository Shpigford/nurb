from nurb import *
from math import sqrt, cos, sin, pi


def _d_profile(radius: float, center_to_flat: float):
    """D face: round of `radius`, flat at +X = center_to_flat (flat faces +X)."""
    if center_to_flat >= radius:
        reject(
            f"shaft flat is past the round ({center_to_flat} >= {radius}): "
            "across-flat must be less than the diameter",
            param="shaft_across_flat",
        )
    half = sqrt(radius * radius - center_to_flat * center_to_flat)
    with BuildSketch() as sk:
        with BuildLine():
            ThreePointArc(
                (center_to_flat, half),
                (-radius, 0),
                (center_to_flat, -half),
            )
            Line((center_to_flat, -half), (center_to_flat, half))
        make_face()
    return sk.sketch


@part
def valve_knob(
    shaft_diameter=float(measured("shaft_diameter")),
    shaft_across_flat=float(measured("shaft_across_flat")),
    height=14.0,
    grip_width=30.0,
    lobe_reach=22.0,
    lobe_width=12.0,
    bore_clearance=0.45,
    draft=False,
):
    """Replacement knob for a D-shaft valve stem.

    shaft_diameter: round diameter of the valve stem
    shaft_across_flat: stem thickness from the flat to the opposite round
    height: overall knob height as printed (bore opens upward)
    grip_width: narrowest outer span at the waist (disk diameter)
    lobe_reach: how far each grip lobe extends from the centerline
    lobe_width: diameter of each grip lobe
    bore_clearance: added to both stem measures to size the D-bore
    """
    if shaft_across_flat >= shaft_diameter:
        reject(
            "shaft_across_flat must be less than shaft_diameter",
            param="shaft_across_flat",
        )
    if bore_clearance < 0.3:
        reject(
            "bore_clearance under 0.3 will bind on a 0.3-grown stem",
            param="bore_clearance",
        )
    if bore_clearance >= 1.0:
        reject(
            "bore_clearance at or above 1.0 leaves the stem rattling",
            param="bore_clearance",
        )

    bore_radius = (shaft_diameter + bore_clearance) / 2.0
    bore_across = shaft_across_flat + bore_clearance
    center_to_flat = bore_across - bore_radius

    # Blind bore open at the top, solid floor on the bed.
    bore_depth = height - 3.0
    if bore_depth < 10.0:
        reject(
            f"height {height} leaves bore_depth {bore_depth} under the 10mm insert path",
            param="height",
        )

    body = Cylinder(grip_width / 2.0, height)
    lobe_r = lobe_width / 2.0
    for i in range(4):
        ang = i * pi / 2
        cx = (lobe_reach - lobe_r) * cos(ang)
        cy = (lobe_reach - lobe_r) * sin(ang)
        body = body + Cylinder(lobe_r, height).locate(Location((cx, cy, 0)))

    # build123d Cylinder is centered on Z; seat the solid on the bed.
    bb = body.bounding_box()
    if abs(bb.min.Z) > 1e-6:
        body = body.translate((0, 0, -bb.min.Z))

    bore = extrude(_d_profile(bore_radius, center_to_flat), amount=bore_depth)
    bore = bore.translate((0, 0, height - bore_depth))
    body = body - bore

    if draft:
        return body

    bed = body.bounding_box().min.Z
    # Outer edges only: leave the D-bore un-chamfered for fit and torque.
    rim2 = (bore_radius + 1.5) ** 2

    def _outer_edge(e):
        c = e.center()
        if c.Z <= bed + 0.05:
            return False
        if c.X * c.X + c.Y * c.Y <= rim2:
            return False
        return True

    return polish(body, body.edges().filter_by(_outer_edge), 1.0)

