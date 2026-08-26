from nurb import *


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    stem_length=12.0,
    bore_clearance=0.6,
    knob_height=15.0,
    hub_width=16.0,
    grip_reach=21.0,
    lobe_width=16.0,
    lobe_count=3,
    relief=3.0,
    draft=False,
):
    """A replacement valve knob that drives a D-shaped stem.

    shaft_diameter: how wide the valve stem measures across its round side
    shaft_across_flat: how wide the stem measures from its flat to the round side
    stem_length: how far the stem stands proud of the valve body
    bore_clearance: how much wider than the stem the socket is cut, so it slides on
    knob_height: how tall the knob stands
    hub_width: how wide the middle of the knob is, around the socket
    grip_reach: how far each grip lobe reaches out from the centre
    lobe_width: how fat each grip lobe is
    lobe_count: how many grip lobes go around the knob
    relief: how much the lobes are blended into the hub, where the twisting load sits
    """
    bore_radius = (shaft_diameter + bore_clearance) / 2.0
    bore_flat = (shaft_across_flat + bore_clearance) - bore_radius
    bore_depth = stem_length + 0.5
    floor = knob_height - bore_depth
    hub_radius = hub_width / 2.0

    if bore_clearance < 0.3:
        reject(
            f"bore_clearance {bore_clearance} is under the 0.3 a sliding fit needs: "
            "raise it to 0.3 or more",
            param="bore_clearance",
        )
    if bore_flat >= bore_radius:
        reject(
            f"shaft_across_flat {shaft_across_flat} is not far enough under "
            f"shaft_diameter {shaft_diameter} to cut a flat: the socket would be round "
            "and would not turn the valve",
            param="shaft_across_flat",
        )
    if hub_radius - bore_radius < 2.0:
        reject(
            f"hub_width {hub_width} leaves {hub_radius - bore_radius:.2f}mm of wall "
            f"around the socket: raise it above {2 * (bore_radius + 2.0):.1f}",
            param="hub_width",
        )
    if floor < 2.0:
        reject(
            f"knob_height {knob_height} leaves {floor:.2f}mm of cap over a "
            f"{bore_depth:.1f}mm socket: raise it above {bore_depth + 2.0:.1f}",
            param="knob_height",
        )
    if grip_reach - lobe_width / 2.0 <= 0.5:
        reject(
            f"grip_reach {grip_reach} does not put the lobes clear of the centre: "
            f"raise it above {lobe_width / 2.0 + 0.5:.1f}",
            param="grip_reach",
        )

    # Plan view: a round hub with the grip lobes hung off it, blended where they meet.
    plan = Circle(hub_radius)
    offset = grip_reach - lobe_width / 2.0
    for i in range(lobe_count):
        angle = 360.0 * i / lobe_count
        plan += Rot(0, 0, angle) * Pos(offset, 0, 0) * Circle(lobe_width / 2.0)
    # Blend where the lobes meet the hub, as much as will land. A tighter lobe
    # spacing leaves less room for the relief, so back off rather than refuse to
    # build: the junction still wants every millimetre of blend it can hold.
    for size in (relief, relief * 0.6, relief * 0.35, relief * 0.2):
        corners = plan.vertices()
        if not corners or size < 0.4:
            break
        try:
            plan = fillet(corners, size)
            break
        except Exception:
            continue

    body = extrude(plan, knob_height)

    # The socket: the stem's D turned into a pocket that opens straight up as it prints.
    socket = Circle(bore_radius) & (
        Pos(bore_flat - bore_radius, 0, 0) * Rectangle(2 * bore_radius, 4 * bore_radius)
    )
    body -= Pos(0, 0, floor) * extrude(socket, bore_depth)

    if draft:
        return body

    # Polish the top rim only: the bed face keeps its full first layer, and the socket
    # mouth is fit-critical, so no lead-in chamfer goes near it.
    top = body.bounding_box().max.Z
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > top - 0.01
        and max(
            abs(e.bounding_box().max.X),
            abs(e.bounding_box().min.X),
            abs(e.bounding_box().max.Y),
            abs(e.bounding_box().min.Y),
        )
        > hub_radius
    )
    keep = [e for e in keep if e not in concave_edges(body)]
    return polish(body, keep, 1.0)
