from math import cos, pi, sin

from nurb import *


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    bore_clearance=0.6,
    knob_width=35.0,
    knob_height=14.0,
    floor_thickness=2.0,
    finger_scoops=6,
    finger_scoop_radius=5.0,
    finger_scoop_depth=3.0,
    chamfer_size=1.0,
    draft=False,
):
    """A replacement knob for a valve with a D-shaped stem.

    shaft_diameter: how wide the valve stem measures across its round side
    shaft_across_flat: how wide the stem measures from its flat across to the round side
    bore_clearance: how much wider than the stem the bore is cut, so the knob slides on
    knob_width: how far across the knob measures at its widest
    knob_height: how tall the knob stands
    floor_thickness: how much solid plastic caps the closed end of the bore
    finger_scoops: how many finger scoops run around the rim
    finger_scoop_radius: how round each finger scoop is
    finger_scoop_depth: how far each finger scoop bites into the rim
    chamfer_size: how big a chamfer the exposed edges get
    """
    stem_length = measured("stem_length")

    if shaft_across_flat >= shaft_diameter:
        reject(
            f"shaft_across_flat {shaft_across_flat} is not under shaft_diameter "
            f"{shaft_diameter}, so there is no flat to key against: measure again "
            "from the flat across to the round side",
            param="shaft_across_flat",
        )
    if shaft_across_flat <= shaft_diameter / 2:
        reject(
            f"shaft_across_flat {shaft_across_flat} is at or past the stem's axis: "
            f"raise it above {shaft_diameter / 2:.2f}",
            param="shaft_across_flat",
        )

    bore_radius = (shaft_diameter + bore_clearance) / 2
    bore_flat = shaft_across_flat + bore_clearance - bore_radius
    bore_depth = knob_height - floor_thickness

    if bore_depth < stem_length - 1e-9:
        reject(
            f"the bore is only {bore_depth:.1f}mm deep and has to swallow the whole "
            f"{stem_length:.1f}mm stem: raise knob_height above "
            f"{stem_length + floor_thickness:.1f}",
            param="knob_height",
        )

    outer_radius = knob_width / 2
    waist = outer_radius - finger_scoop_depth
    if waist - bore_radius < 3.0:
        reject(
            f"only {waist - bore_radius:.1f}mm of plastic is left between the bore and "
            f"the bottom of a finger scoop: raise knob_width above "
            f"{2 * (bore_radius + 3.0 + finger_scoop_depth):.1f}",
            param="knob_width",
        )

    # The grip: a round body scalloped by finger scoops, so a wet hand finds purchase.
    outline = Circle(outer_radius)
    reach = outer_radius + finger_scoop_radius - finger_scoop_depth
    for i in range(finger_scoops):
        angle = 2 * pi * i / finger_scoops
        outline -= Pos(reach * cos(angle), reach * sin(angle)) * Circle(finger_scoop_radius)
    body = extrude(outline, knob_height)

    # The bore: a D, keyed on the stem's flat, opening straight up as it prints.
    bore = Cylinder(bore_radius, bore_depth, align=(Align.CENTER, Align.CENTER, Align.MIN))
    bore -= Pos(bore_flat, 0, -1) * Box(
        bore_radius,
        2 * bore_radius + 2,
        bore_depth + 2,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    body -= Pos(0, 0, floor_thickness) * bore

    if draft:
        return body

    # Polish the top rim and the vertical points between the scoops, which are the
    # edges a hand actually lands on. The bed face keeps its corner, and the bore
    # mouth is mating geometry that never gets a lead-in.
    top = body.bounding_box().max.Z

    def outboard(e):
        c = e.center()
        return (c.X**2 + c.Y**2) ** 0.5 > outer_radius / 2

    def in_top(e):
        return e.bounding_box().min.Z > top - 1e-6 and outboard(e)

    def upright(e):
        box = e.bounding_box()
        return box.min.Z < 1e-6 and box.max.Z > top - 1e-6 and outboard(e)

    exposed = body.edges().filter_by(lambda e: in_top(e) or upright(e))
    return polish(body, exposed, chamfer_size)
