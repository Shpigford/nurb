from nurb import *


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    fit_clearance=0.7,
    knob_width=29.0,
    knob_height=15.0,
    wing_count=2,
    wing_size=6.5,
    bore_depth=12.5,
    draft=False,
):
    """A replacement knob for a D-shaft valve stem, printed bore-up and flipped
    over onto the stem in use.

    shaft_diameter: the valve stem measured across its round sides
    shaft_across_flat: the valve stem measured from the flat to the round side
    fit_clearance: extra bore room over the stem, shared by both measurements
    knob_width: how wide the round core of the knob is
    knob_height: how tall the knob stands
    wing_count: how many grip wings around the rim
    wing_size: how far each grip wing swells out
    bore_depth: how deep the stem socket reaches from the opening
    """
    bore_dia = shaft_diameter + fit_clearance
    bore_r = bore_dia / 2
    flat_x = (shaft_across_flat + fit_clearance) - bore_r
    core_r = knob_width / 2
    floor = knob_height - bore_depth

    if shaft_across_flat >= shaft_diameter:
        reject(
            f"shaft_across_flat {shaft_across_flat} is not under shaft_diameter "
            f"{shaft_diameter}: with no flat the bore is round and cannot turn the stem",
            param="shaft_across_flat",
        )
    if flat_x <= 0.5:
        reject(
            f"shaft_across_flat {shaft_across_flat} cuts the flat past the bore's "
            f"centerline: raise it above {bore_r - fit_clearance + 0.5:.1f}",
            param="shaft_across_flat",
        )
    if core_r - bore_r < 3.0:
        reject(
            f"knob_width {knob_width} leaves under 3mm of wall around the "
            f"{bore_dia:.1f}mm bore: raise it above {bore_dia + 6:.1f}",
            param="knob_width",
        )
    if floor < 2.0:
        reject(
            f"bore_depth {bore_depth} leaves a floor under 2mm in a {knob_height}mm "
            f"knob: lower it below {knob_height - 2:.1f}",
            param="bore_depth",
        )

    outline = Circle(core_r)
    for loc in PolarLocations(core_r, wing_count):
        outline += loc * Circle(wing_size)
    body = extrude(outline, knob_height)

    # D-shaped bore: the stem's circle with its flat facing +X, opening straight up.
    d_profile = Circle(bore_r) & Pos(flat_x - bore_r, 0) * Rectangle(
        2 * bore_r, 2 * bore_r + 2
    )
    body -= Pos(0, 0, floor) * extrude(d_profile, bore_depth + 1)

    if draft:
        return body
    # Chamfer the top rim only: the bottom face is the bed, the vertical
    # lobe junctions are concave, and the bore mouth is mating geometry.
    top = body.bounding_box().max.Z
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > top - 1e-4
        and max(
            abs(e.bounding_box().min.X),
            abs(e.bounding_box().max.X),
            abs(e.bounding_box().min.Y),
            abs(e.bounding_box().max.Y),
        )
        > core_r / 2
    )
    return polish(body, keep, 1.0)
