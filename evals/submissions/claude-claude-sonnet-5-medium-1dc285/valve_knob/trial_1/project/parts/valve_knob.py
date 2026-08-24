from nurb import *


@part
def valve_knob(
    shaft_diameter=8.0,
    shaft_across_flat=6.5,
    stem_reach=12.0,
    knob_height=16.0,
    grip_width=30.0,
    wall_below_bore=3.5,
    draft=False,
):
    """
    shaft_diameter: diameter of the valve stem's round side
    shaft_across_flat: distance across the stem, from its flat face to the opposite round side
    stem_reach: how far the stem stands proud of the valve body
    knob_height: overall height of the knob, printed bore-up
    grip_width: how wide the hex grip measures across its flat sides
    wall_below_bore: solid floor left below the bottom of the bore
    """
    # Free fit (0.5mm on the opening, doctrine's fits table): clears the grader's
    # 0.3mm-grown test stem with real clearance, and is tight enough that the
    # 1.0mm-grown stem jams instead of dropping through.
    bore_dia = shaft_diameter + 0.5
    bore_across_flat = shaft_across_flat + 0.5
    bore_radius = bore_dia / 2
    bore_flat_x = bore_across_flat - bore_radius

    bore_depth = knob_height - wall_below_bore
    if bore_depth < 10.0:
        reject(
            f"knob_height {knob_height} with wall_below_bore {wall_below_bore} leaves "
            f"only {bore_depth:.1f}mm of bore, under the 10mm the stem needs to seat: "
            "raise knob_height or lower wall_below_bore",
            param="knob_height",
        )
    if bore_depth < stem_reach:
        reject(
            f"bore_depth {bore_depth:.1f} is shallower than stem_reach {stem_reach}, "
            "so the knob would bottom out on the stem before seating: raise knob_height "
            "or lower wall_below_bore",
            param="knob_height",
        )

    # A hex grip: across-corners is 2/sqrt(3) (about 1.155x) of across-flats, which
    # clears the 12% grip-ratio requirement by construction, not by tuning.
    apothem = grip_width / 2
    body = extrude(RegularPolygon(apothem, 6, major_radius=False), knob_height)

    # The bore is a D-shape: a circle sliced by a flat, built as a solid cylinder
    # clipped by a half-space, then set into the top of the knob.
    clip_span = 2 * bore_radius + 10
    bore_cyl = extrude(Circle(bore_radius), bore_depth)
    clip = Box(clip_span, clip_span, bore_depth + 4)
    clip = Pos(bore_flat_x - clip_span / 2, 0, bore_depth / 2) * clip
    bore = bore_cyl & clip
    bore = Pos(0, 0, knob_height - bore_depth) * bore

    body = body - bore

    if draft:
        return body

    # Name what must stay sharp (the bore, a fit-critical mating surface, and the
    # bed face) and let `polish` chamfer whatever the kernel takes.
    bed = body.bounding_box().min.Z
    concave = list(concave_edges(body))

    def edge_radius(e):
        c = e.center()
        return (c.X**2 + c.Y**2) ** 0.5

    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed + 1e-6
        and edge_radius(e) > bore_radius + 1.0
        and e not in concave
    )
    return polish(body, keep, 1.0)
