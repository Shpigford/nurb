from nurb import *


def _d_profile(diameter, across_flat):
    """A D-shaped sketch: a circle of `diameter` with a flat cut so the
    distance from the flat to the far round side is `across_flat`, the flat
    facing +X."""
    radius = diameter / 2
    offset = across_flat - radius
    margin = 100.0
    circle = Circle(radius)
    cutter = Pos(offset + margin, 0, 0) * Rectangle(2 * margin, 2 * margin)
    return circle - cutter


@part
def valve_knob(
    shaft_diameter=8.0,
    shaft_across_flat=6.5,
    grip_width=30.0,
    height=14.0,
    draft=False,
):
    """Replacement hand knob for a broken valve handle: prints bore-up, then
    flips over to press onto the D-shaft stem.

    shaft_diameter: diameter of the valve stem, across its round side
    shaft_across_flat: width of the valve stem, from its flat to the opposite round side
    grip_width: how wide the knob is, flat side to flat side, for a solid handhold
    height: how tall the knob stands off the valve body
    """
    if shaft_across_flat >= shaft_diameter:
        reject(
            f"shaft_across_flat {shaft_across_flat} must be under shaft_diameter "
            f"{shaft_diameter}: a D-shaft's flat is always narrower than its round side",
            param="shaft_across_flat",
        )
    if grip_width < 28.0:
        reject(
            f"grip_width {grip_width} is under the 28.0mm a hand needs to turn this: "
            "raise it",
            param="grip_width",
        )

    # Clearance the bore carries over the stem: enough to clear a stem grown by
    # 0.3mm, not enough to pass one grown by 1.0mm, so it seats without rattling.
    bore_clearance = 0.6
    floor_thickness = 3.0
    bore_depth = height - floor_thickness

    if bore_depth < 10.5:
        reject(
            f"height {height} leaves only {bore_depth:.1f}mm for the bore, under the "
            "10.5mm the stem needs to seat: raise height above 13.5",
            param="height",
        )

    apothem = grip_width / 2
    stem_radius = shaft_diameter / 2 + bore_clearance / 2
    if apothem - stem_radius < 5.0:
        reject(
            f"grip_width {grip_width} leaves under 5mm of wall around the bore: raise it",
            param="grip_width",
        )

    body = extrude(RegularPolygon(apothem, 6, major_radius=False), amount=height)

    bore_z0 = height - bore_depth
    bore = extrude(
        _d_profile(shaft_diameter + bore_clearance, shaft_across_flat + bore_clearance),
        amount=bore_depth + 1.0,
    )
    bore = Pos(0, 0, bore_z0) * bore

    knob = body - bore

    if draft:
        return knob

    bed = knob.bounding_box().min.Z
    concave = concave_edges(knob)
    keep = knob.edges().filter_by(
        lambda e: e.bounding_box().max.Z > bed + 1e-6 and e not in concave
    )
    return polish(knob, keep, 1.0)
