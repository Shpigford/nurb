import math

from nurb import *


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    bore_clearance=0.6,
    bore_depth=11.0,
    knob_height=14.0,
    knob_width=30.0,
    grip_bump_width=7.0,
    grip_bump_count=5,
    draft=False,
):
    """A replacement knob for a D-shaft valve stem, printed bore-up.

    shaft_diameter: how wide the valve stem is across its round sides
    shaft_across_flat: how far the stem measures from its flat to the round side
    bore_clearance: extra room the socket leaves around the stem
    bore_depth: how deep the stem socket goes from the top face
    knob_height: how tall the knob stands
    knob_width: how wide the knob body is across
    grip_bump_width: how wide each grip bump is
    grip_bump_count: how many grip bumps ring the knob
    """
    bore_radius = (shaft_diameter + bore_clearance) / 2
    body_radius = knob_width / 2

    if shaft_across_flat >= shaft_diameter:
        reject(
            f"shaft_across_flat {shaft_across_flat} is not under shaft_diameter "
            f"{shaft_diameter}: a D-shaft measures less across the flat than across "
            "the round, so lower shaft_across_flat",
            param="shaft_across_flat",
        )
    if bore_clearance < 0.3:
        reject(
            f"bore_clearance {bore_clearance} is under the 0.3 a printed socket "
            "needs to slide onto its shaft: raise it to 0.3 or more",
            param="bore_clearance",
        )
    if body_radius < bore_radius + 3.0:
        reject(
            f"knob_width {knob_width} leaves under 3mm of wall around the "
            f"{2 * bore_radius:.1f}mm bore: raise it above {2 * (bore_radius + 3.0):.1f}",
            param="knob_width",
        )
    if bore_depth > knob_height - 2.0:
        reject(
            f"bore_depth {bore_depth} leaves under 2mm of floor in a "
            f"{knob_height}mm knob: lower it below {knob_height - 2.0:.1f}",
            param="bore_depth",
        )

    # Grip outline: a circle ringed by bumps, so the section's widest reach
    # stands well proud of its narrowest and wet hands have something to hold.
    section = Circle(body_radius)
    for i in range(grip_bump_count):
        a = 2 * math.pi * i / grip_bump_count
        section += Pos(body_radius * math.cos(a), body_radius * math.sin(a)) * Circle(
            grip_bump_width / 2
        )
    body = extrude(section, knob_height)

    # Blind D-bore, opening straight up, flat facing +X. The clearance is split
    # evenly: the diameter grows by bore_clearance and so does the across-flat.
    flat_x = (shaft_across_flat + bore_clearance) - bore_radius
    rect_w = flat_x + bore_radius + 1.0
    d_section = Circle(bore_radius) & Pos((flat_x - bore_radius - 1.0) / 2, 0) * Rectangle(
        rect_w, 2 * bore_radius + 2.0
    )
    bore = Pos(0, 0, knob_height - bore_depth) * extrude(d_section, bore_depth)
    body -= bore

    if draft:
        return body

    # Polish the top rim only: the bottom edges lie in the bed face, the vertical
    # bump junctions are concave, and the bore mouth is fit-critical mating
    # geometry that never gets a lead-in chamfer.
    top = body.bounding_box().max.Z
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > top - 1e-6
        and math.hypot(e.bounding_box().center().X, e.bounding_box().center().Y)
        > bore_radius + 2.0
    )
    return polish(body, keep, 1.0)
