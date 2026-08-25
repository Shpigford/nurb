from math import cos, radians, sin

from nurb import *


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    bore_clearance=0.65,
    bore_depth=10.5,
    knob_width=35.0,
    knob_height=13.0,
    grip_depth=3.0,
    grip_radius=5.0,
    finger_count=5,
    chamfer_size=1.0,
    draft=False,
):
    """A replacement valve knob for a D-shaped stem.

    shaft_diameter: how wide the valve stem measures across its round side
    shaft_across_flat: how far it measures from the flat to the round side
    bore_clearance: extra room in the bore over the stem, on both of those
    bore_depth: how deep the stem socket runs down from the top face
    knob_width: how far the knob measures across its widest lobes
    knob_height: how tall the knob stands
    grip_depth: how far each finger scallop is scooped into the rim
    grip_radius: how rounded each finger scallop is
    finger_count: how many finger scallops run around the rim
    chamfer_size: how big the chamfer on the exposed edges is
    """
    outer_r = knob_width / 2.0
    bore_r = (shaft_diameter + bore_clearance) / 2.0
    flat_x = (shaft_across_flat + bore_clearance) - bore_r

    if shaft_across_flat >= shaft_diameter:
        reject(
            f"shaft_across_flat {shaft_across_flat} is not under shaft_diameter "
            f"{shaft_diameter}, so the stem has no flat to drive against",
            param="shaft_across_flat",
        )
    if flat_x <= 0.0:
        reject(
            f"shaft_across_flat {shaft_across_flat} cuts past the middle of the stem: "
            f"raise it above {bore_r + bore_clearance / 2.0:.2f}",
            param="shaft_across_flat",
        )
    if bore_clearance < 0.3:
        reject(
            f"bore_clearance {bore_clearance} is under the 0.3 a printed sliding fit "
            "needs: raise it to 0.3 or more",
            param="bore_clearance",
        )
    wall = outer_r - grip_depth - bore_r
    if wall < 2.0:
        reject(
            f"only {wall:.2f}mm of material between the bore and the scallop bottoms: "
            f"raise knob_width above {2.0 * (bore_r + grip_depth + 2.0):.1f}",
            param="knob_width",
        )
    if bore_depth >= knob_height - 2.0:
        reject(
            f"bore_depth {bore_depth} leaves under 2mm of floor under the stem: "
            f"raise knob_height above {bore_depth + 2.0:.1f}",
            param="bore_depth",
        )

    body = Cylinder(outer_r, knob_height, align=(Align.CENTER, Align.CENTER, Align.MIN))

    # Finger scallops: one cylinder scooped out of the rim per finger, so the knob
    # reads as lobes and a wet hand has something to pull against.
    scoop_at = outer_r - grip_depth + grip_radius
    scoop = Cylinder(
        grip_radius, knob_height + 2.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    for i in range(int(finger_count)):
        a = radians(360.0 * i / int(finger_count))
        body -= Pos(scoop_at * cos(a), scoop_at * sin(a), -1.0) * scoop

    # The D bore, opening straight up so it prints without support. The knob flips
    # over onto the stem in use; the flat faces +X as modelled.
    void = Pos(0.0, 0.0, knob_height - bore_depth) * Cylinder(
        bore_r, bore_depth + 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    void -= Pos(flat_x + outer_r, 0.0, 0.0) * Box(2.0 * outer_r, 4.0 * outer_r, 4.0 * outer_r)
    body -= void

    if draft:
        return body

    # Keep sharp: the bed face, every concave junction, and the bore mouth, which is
    # mating geometry a lead-in chamfer would only make print worse.
    bed = body.bounding_box().min.Z
    top = body.bounding_box().max.Z
    concave = [e.center() for e in concave_edges(body)]

    def keepable(e):
        bb = e.bounding_box()
        if bb.max.Z <= bed + 1e-6:
            return False
        c = e.center()
        if any((c - k).length < 1e-6 for k in concave):
            return False
        reach = max(abs(bb.min.X), abs(bb.max.X), abs(bb.min.Y), abs(bb.max.Y))
        if bb.min.Z >= top - 1e-6 and reach <= bore_r + 0.5:
            return False
        return True

    keep = body.edges().filter_by(keepable)
    return polish(body, keep, chamfer_size)
