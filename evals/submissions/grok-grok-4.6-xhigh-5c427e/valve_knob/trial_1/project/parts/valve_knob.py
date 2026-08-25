from nurb import *

# Virtual stem is grown 0.3 mm on diameter and across-flat and must slide in;
# grown 1.0 mm it must jam. Clearance sits between those two.
BORE_CLEARANCE = 0.8
FLOOR = 3.0
LOBES = 5
LOBE_RADIUS = 6.0


def _d_bore(diameter, across_flat, depth):
    """D-shaped cutter, circle on the origin, flat facing +X, extruded +Z."""
    radius = diameter / 2.0
    flat_x = across_flat - radius
    round_part = Cylinder(radius, depth, align=(Align.CENTER, Align.CENTER, Align.MIN))
    cap = Pos(flat_x, 0, -1) * Box(
        radius * 2 + 4,
        radius * 2 + 4,
        depth + 2,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    return round_part - cap


@part
def valve_knob(
    shaft_diameter=float(measured("shaft_diameter")),
    shaft_across_flat=float(measured("shaft_across_flat")),
    height=14.5,
    knob_width=30.0,
    draft=False,
):
    """Replacement knob for a D-shaft valve, printed bore-up.

    shaft_diameter: round diameter of the valve stem
    shaft_across_flat: stem width from the flat to the opposite round side
    height: how tall the knob is
    knob_width: how wide the grip is at its narrowest
    """
    if shaft_diameter <= 0:
        reject("shaft_diameter must be positive", param="shaft_diameter")
    if shaft_across_flat <= 0:
        reject("shaft_across_flat must be positive", param="shaft_across_flat")
    if shaft_across_flat >= shaft_diameter:
        reject(
            "shaft_across_flat must be less than shaft_diameter so the stem has a flat to drive",
            param="shaft_across_flat",
        )
    if height < 12.0:
        reject("height must be at least 12 mm so the stem is covered", param="height")
    if knob_width < 28.0:
        reject("knob_width must be at least 28 mm so wet hands can grip it", param="knob_width")

    hub_r = knob_width / 2.0
    # Lobes sit just inside the hub so the waist stays knob_width across.
    lobe_offset = hub_r - 1.0
    outline = Circle(hub_r)
    for i in range(LOBES):
        angle = i * (360.0 / LOBES)
        outline += Rot(0, 0, angle) * Pos(lobe_offset, 0) * Circle(LOBE_RADIUS)

    blank = extrude(outline, height)

    bore_dia = shaft_diameter + BORE_CLEARANCE
    bore_flat = shaft_across_flat + BORE_CLEARANCE
    bore_depth = height - FLOOR
    if bore_depth <= 10.0:
        reject(
            f"height {height:g} leaves a floor that would stop a 10 mm stem: raise height above {FLOOR + 10.0:g}",
            param="height",
        )

    cutter = Pos(0, 0, height - bore_depth) * _d_bore(bore_dia, bore_flat, bore_depth + 2.0)
    body = blank - cutter
    if draft:
        return body

    hole_edges = new_edges(blank, combined=body)
    bed = body.bounding_box().min.Z
    keep = body.edges().filter_by(lambda e: e.bounding_box().max.Z > bed + 0.05)
    keep = keep - hole_edges
    keep = keep - concave_edges(body)
    return polish(body, keep, 1.0)
