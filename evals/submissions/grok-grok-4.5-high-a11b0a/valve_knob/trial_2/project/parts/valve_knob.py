from nurb import *


def _d_profile(diameter: float, across_flat: float):
    """D-shaped sketch: round of `diameter` with flat facing +X at across-flat."""
    r = diameter / 2.0
    flat_x = across_flat - r
    return Circle(r) - Pos(flat_x, 0) * Rectangle(
        2.0 * r + 2.0, 2.0 * r + 2.0, align=(Align.MIN, Align.CENTER)
    )


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    height=13.0,
    grip_width=30.0,
    lobe_reach=18.0,
    floor_thickness=2.5,
    draft=False,
):
    """Replacement knob for a D-shaft valve stem.

    shaft_diameter: full diameter of the stem across the round
    shaft_across_flat: stem thickness from the flat to the opposite round
    height: overall knob height as printed (bore opens up)
    grip_width: narrowest outside width through the center
    lobe_reach: how far lobe tips sit from the centerline
    floor_thickness: closed bed floor under the blind bore
    """
    if shaft_across_flat >= shaft_diameter:
        reject(
            f"shaft_across_flat {shaft_across_flat} must be under shaft_diameter "
            f"{shaft_diameter}",
            param="shaft_across_flat",
        )
    if height < 12.0:
        reject(f"height {height} must be at least 12 so the stem can seat", param="height")
    if grip_width < 28.0:
        reject(
            f"grip_width {grip_width} must be at least 28 for wet-hand purchase",
            param="grip_width",
        )
    if lobe_reach < 0.56 * grip_width:
        reject(
            f"lobe_reach {lobe_reach} must reach at least 12% past half of grip_width",
            param="lobe_reach",
        )

    # Clearance so a stem grown +0.3 passes and one grown +1.0 jams.
    clearance = 0.4
    bore_dia = shaft_diameter + clearance
    bore_flat = shaft_across_flat + clearance
    bore_depth = height - floor_thickness
    if bore_depth < 10.0:
        reject(
            f"bore depth {bore_depth} is under 10; lower floor_thickness or raise height",
            param="floor_thickness",
        )

    hub_r = grip_width / 2.0
    lobe_r = lobe_reach - hub_r
    if lobe_r < 1.0:
        reject(
            f"lobe_reach {lobe_reach} must sit past grip_width/2 ({hub_r})",
            param="lobe_reach",
        )

    z_align = (Align.CENTER, Align.CENTER, Align.MIN)
    hub = Cylinder(hub_r, height, align=z_align)
    lobes = hub
    for angle in (0.0, 90.0, 180.0, 270.0):
        lobes = lobes + Rot(0, 0, angle) * Pos(hub_r, 0, 0) * Cylinder(
            lobe_r, height, align=z_align
        )

    # Blind D-bore opening straight up; flat faces +X. Floor stays on the bed.
    bore = Pos(0, 0, floor_thickness) * extrude(
        _d_profile(bore_dia, bore_flat), bore_depth + 0.1
    )
    body = lobes - bore

    if draft:
        return body

    bed = body.bounding_box().min.Z
    bore_limit = (bore_dia / 2.0 + 1.0) ** 2

    def polishable(edge):
        bb = edge.bounding_box()
        if bb.min.Z <= bed + 1e-3:
            return False
        cx = 0.5 * (bb.min.X + bb.max.X)
        cy = 0.5 * (bb.min.Y + bb.max.Y)
        if cx * cx + cy * cy <= bore_limit:
            return False
        return True

    keep = body.edges().filter_by(polishable)
    # Skip concave junctions: a cosmetic chamfer there becomes a feather edge.
    concave = set(concave_edges(body))
    keep = ShapeList([e for e in keep if e not in concave])
    return polish(body, keep, 1.0)
