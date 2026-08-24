from nurb import *

shaft_dia = measured("shaft_diameter")
shaft_flat = measured("shaft_across_flat")


def _reach(edge):
    # How far the edge sits from the vertical centerline, at its farthest.
    bb = edge.bounding_box()
    return max(abs(bb.min.X), abs(bb.max.X), abs(bb.min.Y), abs(bb.max.Y))


@part
def valve_knob(
    shaft_diameter=shaft_dia,
    shaft_across_flat=shaft_flat,
    grip_width=29.0,
    knob_height=15.0,
    floor_thickness=2.5,
    fit_clearance=0.6,
    draft=False,
):
    """A replacement hand knob for the valve's D-shaft stem.

    shaft_diameter: how wide the valve stem is across its round sides
    shaft_across_flat: from the stem's flat side to its round side
    grip_width: how wide the knob is across its flat sides
    knob_height: how tall the knob stands
    floor_thickness: solid plastic between the end of the stem and the top of the knob in use
    fit_clearance: extra room in the socket so the knob slides onto the stem
    """
    if shaft_across_flat >= shaft_diameter:
        reject(
            f"shaft_across_flat {shaft_across_flat} is not under shaft_diameter "
            f"{shaft_diameter}: with no flat the socket cannot transmit torque",
            param="shaft_across_flat",
        )
    bore_r = (shaft_diameter + fit_clearance) / 2
    if grip_width < 2 * bore_r + 6:
        reject(
            f"grip_width {grip_width} leaves under 3mm of wall around the "
            f"{2 * bore_r:.1f}mm socket: raise it above {2 * bore_r + 6:.1f}",
            param="grip_width",
        )
    if knob_height - floor_thickness < shaft_across_flat:
        reject(
            f"knob_height {knob_height} minus floor_thickness {floor_thickness} "
            f"leaves a socket too shallow to grip the stem: raise knob_height "
            f"above {floor_thickness + shaft_across_flat}",
            param="knob_height",
        )

    body = extrude(Rectangle(grip_width, grip_width), knob_height)

    # The socket is the stem's D-section grown by fit_clearance on both the
    # diameter and the across-flat, opening straight up with the flat facing +X.
    flat_x = shaft_across_flat + fit_clearance - bore_r
    half_w = 2 * bore_r + 2
    d_profile = Circle(bore_r) & Pos(flat_x - half_w / 2, 0) * Rectangle(half_w, half_w)
    socket = Pos(0, 0, floor_thickness) * extrude(d_profile, knob_height - floor_thickness + 1)
    body = body - socket

    if draft:
        return body
    # Keep chamfers off the bed-plane edges and away from the socket, which is
    # fit-critical mating geometry; its interior edges are concave besides.
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().max.Z > 0.01 and _reach(e) > bore_r + 2
    )
    return polish(body, keep, 1.2)
