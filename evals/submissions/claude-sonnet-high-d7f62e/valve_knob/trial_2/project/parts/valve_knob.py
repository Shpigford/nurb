from nurb import *


@part
def valve_knob(
    shaft_diameter=8.0,
    shaft_across_flat=6.5,
    grip_width=30.0,
    knob_height=14.0,
    socket_depth=11.0,
    socket_clearance=0.65,
    draft=False,
):
    """
    shaft_diameter: diameter of the valve stem this knob slides onto
    shaft_across_flat: width across the stem's flat side
    grip_width: side length of the knob's square grip
    knob_height: total height of the knob
    socket_depth: how deep the stem socket is cut into the knob
    socket_clearance: extra room added around the stem for a smooth slide-on fit
    """
    socket_dia = shaft_diameter + socket_clearance
    socket_flat = shaft_across_flat + socket_clearance
    socket_r = socket_dia / 2
    flat_cut = socket_dia - socket_flat
    flat_x = socket_r - flat_cut

    body = Box(grip_width, grip_width, knob_height)
    bed = body.bounding_box().min.Z
    top = body.bounding_box().max.Z

    socket_profile = Circle(socket_r) - Pos(flat_x + socket_r, 0) * Rectangle(
        2 * socket_r, 4 * socket_r
    )
    socket = Pos(0, 0, top - socket_depth) * extrude(socket_profile, socket_depth)
    body = body - socket

    if draft:
        return body

    # Name what must stay sharp, then let `polish` chamfer whatever the kernel takes.
    # A bare `chamfer(...)` is all or nothing: one edge that cannot land loses the lot.
    concave = concave_edges(body)
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed
        and abs(e.bounding_box().min.Z - top) < 1e-6
        and e not in concave
    )
    return polish(body, keep, 1.0)
