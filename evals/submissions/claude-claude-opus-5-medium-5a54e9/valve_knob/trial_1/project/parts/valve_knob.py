from nurb import *


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    bore_slack=0.65,
    bore_depth=12.0,
    floor_thickness=3.0,
    body_width=29.0,
    grip_lobe_reach=17.5,
    grip_lobe_width=7.0,
    grip_lobe_count=5,
    draft=False,
):
    """A replacement valve knob, modelled bore-up as it prints.

    shaft_diameter: how wide the valve stem measures across its round side
    shaft_across_flat: how wide the stem measures from its flat to the round side
    bore_slack: extra room in the socket over the stem, so it slides on without rattling
    bore_depth: how deep the socket swallows the stem
    floor_thickness: solid plastic capping the socket, the top of the knob in use
    body_width: how far across the round body of the knob measures
    grip_lobe_reach: how far the finger lobes stand out from the centre
    grip_lobe_width: how wide each finger lobe is
    grip_lobe_count: how many finger lobes go round the knob
    """
    bore_radius = (shaft_diameter + bore_slack) / 2.0
    flat_offset = (shaft_across_flat + bore_slack) - bore_radius
    body_radius = body_width / 2.0
    lobe_radius = grip_lobe_width / 2.0
    height = bore_depth + floor_thickness

    if flat_offset >= bore_radius:
        reject(
            "shaft_across_flat %.2f is not enough under shaft_diameter %.2f to leave a "
            "flat: the socket would be plain round and could not turn the valve"
            % (shaft_across_flat, shaft_diameter),
            param="shaft_across_flat",
        )
    if body_radius - bore_radius < 3.0:
        reject(
            "body_width %.1f leaves under 3mm of wall around a %.2fmm socket: raise it "
            "above %.1f" % (body_width, bore_radius * 2, (bore_radius + 3.0) * 2),
            param="body_width",
        )
    if grip_lobe_reach <= body_radius:
        reject(
            "grip_lobe_reach %.1f does not stand out past the %.1fmm body: raise it "
            "above %.1f" % (grip_lobe_reach, body_radius, body_radius),
            param="grip_lobe_reach",
        )

    body = extrude(Circle(body_radius), height)
    lobe_centre = grip_lobe_reach - lobe_radius
    for i in range(grip_lobe_count):
        angle = 360.0 / grip_lobe_count * i
        lobe = Rot(0, 0, angle) * Pos(lobe_centre, 0, 0) * extrude(Circle(lobe_radius), height)
        body = body + lobe

    # The D-socket: a circle with one side cut away, so the stem's flat carries torque.
    socket = Circle(bore_radius) - Pos(flat_offset + bore_radius, 0) * Rectangle(
        bore_radius * 2, bore_radius * 2
    )
    body = body - Pos(0, 0, floor_thickness) * extrude(socket, bore_depth)

    if draft:
        return body

    # Chamfer the rim the fingers meet. The bed face keeps its full first layer, and the
    # socket mouth stays sharp: a lead-in there prints as slivers on somebody else's
    # machine.
    top = height
    concave = set(concave_edges(body))
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > top - 1e-6
        and Vector(e.center().X, e.center().Y, 0).length > bore_radius + 1.5
        and e not in concave
    )
    return polish(body, keep, 1.0)
