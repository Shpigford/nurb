from nurb import *


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    grip_width=30.0,
    height=15.0,
    bore_depth=11.0,
    socket_clearance=0.7,
    draft=False,
):
    """Replacement knob for a broken valve handle, socketed onto a D-shaft stem.

    Printed bore-up: the socket opens through the top face as modelled, on the
    centerline, with the stem's flat facing +X. In use the knob flips over onto
    the stem, so the face that sits on the bed here is the one the hand grips.

    shaft_diameter: the stem's diameter across its round side
    shaft_across_flat: the stem's width measured across its ground flat
    grip_width: how wide the knob is across its flats, hand to hand
    height: how tall the knob stands
    bore_depth: how far the socket reaches up into the knob from the top face
    socket_clearance: how much extra room the socket leaves around the grown stem
    """
    if shaft_across_flat >= shaft_diameter:
        reject(
            f"shaft_across_flat {shaft_across_flat} is not under shaft_diameter "
            f"{shaft_diameter}: a flat cannot be as wide as the round it is cut from",
            param="shaft_across_flat",
        )
    if bore_depth < 10.0:
        reject(
            f"bore_depth {bore_depth} is under the 10mm the stem needs to seat: "
            f"raise it to at least 10.0",
            param="bore_depth",
        )
    floor = height - bore_depth
    if floor < 3.0:
        reject(
            f"bore_depth {bore_depth} leaves only {floor:.1f}mm of material over the "
            f"socket at height {height}: raise height or shorten bore_depth so at "
            f"least 3mm of floor remains",
            param="bore_depth",
        )

    apothem = grip_width / 2.0
    body = extrude(RegularPolygon(apothem, 6, major_radius=False), height)

    # The stem's D cross-section: a circle with a chord cut off on the +X side,
    # sized so the round span is `shaft_diameter` and the flat-to-round span is
    # `shaft_across_flat`. The socket is the same shape grown by `socket_clearance`.
    bore_r = (shaft_diameter + socket_clearance) / 2.0
    flat_x = (shaft_across_flat + socket_clearance) - bore_r
    pad = bore_r + apothem
    trim = Pos(flat_x + pad, 0) * Rectangle(2 * pad, 2 * pad)
    bore_profile = Circle(bore_r) - trim
    bore = Pos(0, 0, floor) * extrude(bore_profile, bore_depth)
    body = body - bore

    if draft:
        return body

    # Only the outer vertical corners take the polish pass: the top and bottom
    # hex rims stay sharp so no vertex ever carries three chamfers at once, and
    # the bore's own edges are concave, which polish must never touch anyway.
    bed_z = body.bounding_box().min.Z
    top_z = body.bounding_box().max.Z
    vertical = body.edges().filter_by(
        lambda e: (e.bounding_box().max.Z - e.bounding_box().min.Z) > (top_z - bed_z) * 0.5
    )
    keep = vertical - concave_edges(body)
    return polish(body, keep, 1.0)
