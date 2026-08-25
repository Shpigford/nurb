from nurb import *

# Slack so a slightly oversized stem still drops in, while 1 mm oversize jams.
_BORE_SLACK = 0.5


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    draft=False,
):
    """Replacement knob for a D-shaft valve stem, printed bore-up.

    shaft_diameter: round diameter of the valve stem
    shaft_across_flat: stem thickness from the flat to the opposite round side
    """
    knob_width = 32.0
    knob_height = 15.0

    if shaft_across_flat >= shaft_diameter:
        reject(
            f"shaft_across_flat {shaft_across_flat} must be under the {shaft_diameter} mm diameter",
            param="shaft_across_flat",
        )
    if shaft_diameter < 2.0:
        reject(
            f"shaft_diameter {shaft_diameter} mm is under 2 mm; the bore would smear",
            param="shaft_diameter",
        )

    bore_dia = shaft_diameter + _BORE_SLACK
    bore_across_flat = shaft_across_flat + _BORE_SLACK
    bore_r = bore_dia / 2.0
    # Flat faces +X: round side at -bore_r, so the flat sits at across_flat - radius.
    flat_x = bore_across_flat - bore_r
    if flat_x <= -bore_r + 0.4:
        reject(
            f"shaft_across_flat {shaft_across_flat} leaves no D-flat on the bore",
            param="shaft_across_flat",
        )
    if bore_dia + 6.0 > knob_width:
        reject(
            f"shaft_diameter {shaft_diameter} mm leaves the grip thinner than 3 mm",
            param="shaft_diameter",
        )

    body = extrude(
        RegularPolygon(knob_width / 2.0, 6, major_radius=False),
        amount=knob_height,
    )

    # Through D-bore, opening straight up on the centerline. A cylinder cut
    # by a +X half-space leaves the stem's flat facing +X.
    cyl = Pos(0, 0, -1) * Cylinder(
        bore_r,
        knob_height + 2.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    cutter = Pos(flat_x, 0, -2) * Box(
        bore_dia + 4.0,
        bore_dia + 4.0,
        knob_height + 4.0,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    knob = body - (cyl - cutter)

    if draft:
        return knob
    # Outer top rim only. The D-bore is a fit surface and must stay a prism.
    top_z = knob.bounding_box().max.Z
    keep = knob.edges().filter_by(
        lambda e: abs(e.bounding_box().min.Z - top_z) < 0.05
        and abs(e.bounding_box().max.Z - top_z) < 0.05
        and (e.center().X ** 2 + e.center().Y ** 2) ** 0.5 > 10.0
    )
    return polish(knob, keep, 1.0)
