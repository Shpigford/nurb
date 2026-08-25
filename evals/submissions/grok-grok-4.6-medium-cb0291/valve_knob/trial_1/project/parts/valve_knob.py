from nurb import *

# Printed clearance on the D-bore. The 0.3-grown stem (diameter + 0.3,
# across-flat + 0.3) must pass; the 1.0-grown stem must jam.
_BORE_CLEARANCE = 0.5


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    draft=False,
):
    """Replacement knob for a D-shaft valve, printed bore-up.

    shaft_diameter: stem diameter across the round
    shaft_across_flat: stem size from the flat to the round side
    """
    if shaft_across_flat >= shaft_diameter:
        reject(
            "shaft_across_flat must be smaller than shaft_diameter for a D-shaft",
            param="shaft_across_flat",
        )
    if shaft_diameter < 2.0:
        reject("shaft_diameter is too small to print a D-bore", param="shaft_diameter")

    # Oval grip: 28mm across the minor axis, 36mm across the major (lever) axis.
    # At half height the section is unchanged by the top chamfer.
    grip_half_narrow = 14.0
    grip_half_wide = 18.0
    knob_height = 16.0
    floor = 2.5

    bore_r = (shaft_diameter + _BORE_CLEARANCE) / 2.0
    # Stem flat at +X: distance from center = across_flat - radius.
    # Add half the diametral clearance so the 0.3-grown flat still clears.
    flat_x = shaft_across_flat - shaft_diameter / 2.0 + _BORE_CLEARANCE / 2.0

    body = extrude(Ellipse(grip_half_wide, grip_half_narrow), knob_height)

    cyl = Pos(0, 0, floor) * Cylinder(
        bore_r,
        knob_height - floor + 1.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    # Keep the +X chord of material: the void is the cylinder cut to x <= flat_x.
    cap = Pos(flat_x, 0, floor - 0.5) * Box(
        bore_r * 4.0,
        bore_r * 4.0,
        knob_height - floor + 2.0,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    body = body - (cyl - cap)

    if draft:
        return body

    bed = body.bounding_box().min.Z
    concave = concave_edges(body)
    # Bore edges sit inside ~shaft radius; the oval rim is at 14–18mm.
    inner = 10.0 ** 2

    def polishable(e):
        bb = e.bounding_box()
        if bb.min.Z <= bed + 0.05:
            return False
        corners = (
            (bb.min.X, bb.min.Y),
            (bb.min.X, bb.max.Y),
            (bb.max.X, bb.min.Y),
            (bb.max.X, bb.max.Y),
        )
        if all(x * x + y * y < inner for x, y in corners):
            return False
        return True

    keep = body.edges().filter_by(polishable) - concave
    return polish(body, keep, 1.0)
