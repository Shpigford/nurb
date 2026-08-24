from nurb import *


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    height=15.0,
    grip_radius=16.75,
    bore_depth=11.0,
    draft=False,
):
    """
    shaft_diameter: the valve stem's diameter across its round side
    shaft_across_flat: the stem's width from its flat face to the opposite round side
    height: overall knob height
    grip_radius: hex grip size, center to corner, sets how big a hand grabs
    bore_depth: how far the D-shaped bore cuts down from the top face
    """
    body = extrude(RegularPolygon(grip_radius, 6), height)

    # Bore sits midway between the 0.3mm-grown clearance stem and the
    # 1.0mm-grown rattle stem, on both the round side and the flat, so it
    # passes the loose stem, jams the tight one, and steers on the flat.
    clearance = 0.65
    bore_dia = shaft_diameter + clearance
    bore_af = shaft_across_flat + clearance
    bore_r = bore_dia / 2
    flat_x = bore_af - bore_r

    rect_w = 2 * bore_r + 2.0
    flat_cut = Pos(flat_x - rect_w / 2, 0) * Rectangle(rect_w, rect_w)
    bore_profile = Circle(bore_r) & flat_cut
    bore = extrude(bore_profile, bore_depth)
    top = body.bounding_box().max.Z
    bore = Pos(0, 0, top - bore_depth) * bore

    body = body - bore

    if draft:
        return body

    bed = body.bounding_box().min.Z
    concave = set(concave_edges(body))

    def keep_edge(e):
        bb = e.bounding_box()
        if bb.min.Z == bed and bb.max.Z == bed:
            return False
        if e in concave:
            return False
        return True

    keep = body.edges().filter_by(keep_edge)
    return polish(body, keep, 1.0)
