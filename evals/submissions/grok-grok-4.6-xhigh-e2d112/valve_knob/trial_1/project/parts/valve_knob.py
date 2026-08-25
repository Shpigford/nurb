from nurb import *


def _d_stem(diameter, across_flat, z0, z1):
    """D-shaped prism on the Z axis, flat facing +X."""
    radius = diameter / 2.0
    height = z1 - z0
    core = Pos(0, 0, z0) * Cylinder(
        radius, height, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    flat_x = -radius + across_flat
    cap_width = radius + 4.0
    cap = Pos(flat_x + cap_width / 2.0, 0, z0 + height / 2.0) * Box(
        cap_width, 2.0 * radius + 8.0, height + 2.0
    )
    return core - cap


@part
def valve_knob(
    shaft_diameter=8.0,
    shaft_across_flat=6.5,
    knob_width=30.0,
    knob_length=40.0,
    knob_height=14.0,
    draft=False,
):
    """Replacement knob for a valve with a D-shaped stem.

    Prints bore-up and flips onto the stem in use.

    shaft_diameter: caliper reading across the round of the stem
    shaft_across_flat: caliper reading from the stem's flat to the round side
    knob_width: how wide the grip is at its narrowest
    knob_length: how long the grip is, for wet-hand leverage
    knob_height: how tall the knob is
    """
    clearance = 0.5
    if shaft_across_flat >= shaft_diameter:
        reject(
            f"shaft_across_flat {shaft_across_flat} must be below "
            f"shaft_diameter {shaft_diameter} so the stem has a flat to drive",
            param="shaft_across_flat",
        )
    if shaft_diameter < 2.0:
        reject(
            f"shaft_diameter {shaft_diameter} is under 2mm and will not print as a bore",
            param="shaft_diameter",
        )
    if knob_length < knob_width * 1.12:
        reject(
            f"knob_length {knob_length} must stay at least 12% past knob_width "
            f"{knob_width} so wet hands can turn it",
            param="knob_length",
        )
    if knob_width - (shaft_diameter + clearance) < 5.0:
        reject(
            f"knob_width {knob_width} leaves under 2.5mm of wall around a "
            f"{shaft_diameter}mm stem; raise it",
            param="knob_width",
        )

    bore_dia = shaft_diameter + clearance
    bore_across_flat = shaft_across_flat + clearance

    body = extrude(SlotOverall(knob_length, knob_width), knob_height)
    outer = body
    body = body - _d_stem(bore_dia, bore_across_flat, -1.0, knob_height + 1.0)

    if draft:
        return body

    bed = body.bounding_box().min.Z
    bore_edges = new_edges(outer, combined=body)

    def keep_edge(edge):
        if edge.bounding_box().max.Z <= bed + 0.05:
            return False
        for bore_edge in bore_edges:
            if edge.is_same(bore_edge):
                return False
        return True

    keep = body.edges().filter_by(keep_edge)
    return polish(body, keep, 1.0)
