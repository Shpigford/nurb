from nurb import *


@part
def valve_knob(
    shaft_diameter=8.0,
    shaft_across_flat=6.5,
    shaft_fit=0.5,
    knob_width=29.0,
    knob_height=15.0,
    bore_depth=12.5,
    lobe_count=4,
    lobe_width=8.0,
    chamfer_size=1.0,
    draft=False,
):
    """A replacement valve knob that presses onto a D-shaped stem.

    shaft_diameter: how wide the valve stem measures across its round side
    shaft_across_flat: how wide the stem measures from its flat to the round side
    shaft_fit: extra room in the bore so the knob slides onto the stem
    knob_width: how wide the round body of the knob is
    knob_height: how tall the knob stands
    bore_depth: how deep the stem socket goes into the knob
    lobe_count: how many finger lobes stand around the knob
    lobe_width: how wide each finger lobe is
    chamfer_size: how big the bevel on the handled edges is
    """
    bore_radius = (shaft_diameter + shaft_fit) / 2.0
    flat_offset = shaft_across_flat + shaft_fit - bore_radius
    body_radius = knob_width / 2.0
    lobe_radius = lobe_width / 2.0
    floor = knob_height - bore_depth

    if flat_offset >= bore_radius:
        reject("the stem's flat is too shallow to cut a bore that can carry torque",
               param="shaft_across_flat")
    if floor < 2.0:
        reject("the bore leaves less than 2mm of floor under the stem", param="bore_depth")
    if body_radius - bore_radius < 3.0:
        reject("the knob is too narrow to leave a wall around the bore", param="knob_width")

    body = extrude(Circle(body_radius), knob_height)

    # Finger lobes, so a wet hand has something to bear against.
    lobe_centre = body_radius - lobe_radius * 0.35
    for i in range(lobe_count):
        angle = 360.0 / lobe_count * i
        lobe = Pos(lobe_centre, 0, 0) * extrude(Circle(lobe_radius), knob_height)
        body = body + Rot(0, 0, angle) * lobe

    # The D bore: a round hole with one side cut back to the stem's flat.
    profile = Circle(bore_radius) - Pos(
        flat_offset + bore_radius, 0, 0
    ) * Rectangle(2 * bore_radius, 4 * bore_radius)
    bore = Pos(0, 0, floor) * extrude(profile, bore_depth + 1.0)
    body = body - bore

    if draft:
        return body

    bed = body.bounding_box().min.Z
    top = body.bounding_box().max.Z
    concave = set(concave_edges(body))
    keep = []
    for e in body.edges():
        if e in concave:
            continue
        bb = e.bounding_box()
        if bb.max.Z <= bed + 1e-6:          # lying in the bed face
            continue
        if bb.max.Z >= top - 1e-6 and bb.min.Z >= top - 1e-6:
            # top-face edges: keep the outside, leave the bore mouth sharp
            if max(abs(bb.min.X), abs(bb.max.X), abs(bb.min.Y), abs(bb.max.Y)) < bore_radius + 1.0:
                continue
        keep.append(e)
    return polish(body, keep, chamfer_size)
