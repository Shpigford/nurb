from math import cos, radians, sin

from nurb import *


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    shaft_length=12.0,
    bore_slack=0.7,
    floor_thickness=3.0,
    knob_width=29.2,
    grip_lobe_count=3,
    grip_lobe_reach=17.0,
    grip_lobe_width=13.0,
    draft=False,
):
    """A replacement valve handle that presses onto a D-shaped stem.

    shaft_diameter: how wide the valve stem measures across its round side
    shaft_across_flat: how far the stem measures from its flat to the round side
    shaft_length: how far the stem stands proud of the valve body
    bore_slack: how much wider than the stem the socket is cut, so it slides on
    floor_thickness: how much solid plastic caps the end of the socket
    knob_width: how far across the knob measures between the lobes
    grip_lobe_count: how many thumb lobes stand out around the knob
    grip_lobe_reach: how far a lobe reaches out from the knob's centre
    grip_lobe_width: how wide across each thumb lobe is
    """
    body_radius = knob_width / 2
    bore_radius = (shaft_diameter + bore_slack) / 2
    # The flat wall of the socket, measured from the centreline: the socket spans
    # `shaft_across_flat + bore_slack` from that wall to the far side of the bore.
    flat_offset = (shaft_across_flat + bore_slack) - bore_radius
    bore_depth = shaft_length + 0.5
    height = bore_depth + floor_thickness
    lobe_radius = grip_lobe_width / 2
    lobe_offset = grip_lobe_reach - lobe_radius

    if flat_offset <= 0.0 or flat_offset >= bore_radius:
        reject(
            f"shaft_across_flat {shaft_across_flat} leaves no flat against a "
            f"{shaft_diameter}mm stem: it has to sit between "
            f"{shaft_diameter / 2:.1f} and {shaft_diameter:.1f}",
            param="shaft_across_flat",
        )
    if body_radius - bore_radius < 3.0:
        reject(
            f"knob_width {knob_width} leaves {body_radius - bore_radius:.1f}mm of wall "
            f"around the socket: raise it above {2 * (bore_radius + 3.0):.1f}",
            param="knob_width",
        )
    if lobe_offset <= 0.0 or grip_lobe_reach <= body_radius:
        reject(
            f"grip_lobe_reach {grip_lobe_reach} does not stand out past the "
            f"{body_radius:.1f}mm body: raise it above {body_radius * 1.15:.1f}",
            param="grip_lobe_reach",
        )

    outline = Circle(body_radius)
    for i in range(grip_lobe_count):
        a = radians(360.0 * i / grip_lobe_count)
        outline += Pos(lobe_offset * cos(a), lobe_offset * sin(a)) * Circle(lobe_radius)
    body = extrude(outline, amount=height)

    # The socket: a circle flattened on +X, opening straight up out of the top face.
    # It prints as a plain vertical blind bore, so nothing inside it needs support.
    socket = extrude(Circle(bore_radius), amount=bore_depth)
    socket -= Pos(flat_offset + bore_radius, 0, bore_depth / 2) * Box(
        2 * bore_radius, 4 * bore_radius, 2 * bore_depth
    )
    body -= Pos(0, 0, floor_thickness) * socket

    if draft:
        return body

    # Polish the top rim only. The bed edge would lay a knife edge into the first
    # layer, the socket mouth is fit-critical, and the lobe roots are concave.
    top = height - 0.01
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > top
        and e.bounding_box().max.X ** 2 + e.bounding_box().max.Y ** 2 > body_radius**2 / 4
    )
    return polish(body, keep, 1.0)
