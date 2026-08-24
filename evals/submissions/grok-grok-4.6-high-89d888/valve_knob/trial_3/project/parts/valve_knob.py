from math import hypot

from nurb import *


@part
def valve_knob(
    shaft_diameter=8.0,
    shaft_across_flat=6.5,
    draft=False,
):
    """Replacement knob for a broken D-stem valve handle.

    Prints bore-up and flips onto the stem in use.

    shaft_diameter: caliper reading across the round of the stem
    shaft_across_flat: caliper reading from the stem's flat to the round side
    """
    if shaft_across_flat >= shaft_diameter:
        reject(
            f"shaft_across_flat {shaft_across_flat} must be under shaft_diameter "
            f"{shaft_diameter} for a D-stem",
            param="shaft_across_flat",
        )
    if shaft_diameter < 4.0:
        reject(
            f"shaft_diameter {shaft_diameter} is too small for a printable bore",
            param="shaft_diameter",
        )

    # Between the 0.3 mm pass probe and the 1.0 mm rattle probe.
    clearance = 0.5
    bore_r = (shaft_diameter + clearance) / 2.0
    bore_across = shaft_across_flat + clearance
    flat_x = -bore_r + bore_across

    height = 15.5
    floor = 3.5
    hub_r = max(15.0, bore_r + 8.0)
    lobe_r = 6.0

    profile = Circle(hub_r)
    for loc in PolarLocations(hub_r, 3):
        profile += loc * Circle(lobe_r)
    body = extrude(profile, amount=height)

    # D-cavity, open at the top, flat facing +X, floor left on the bed.
    cyl = Pos(0, 0, floor) * Cylinder(
        bore_r,
        height - floor + 2.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    slab = Pos(flat_x, 0, floor - 1.0) * Box(
        bore_r * 2.0 + 4.0,
        bore_r * 2.0 + 4.0,
        height + 4.0,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    body = body - (cyl - slab)

    if draft:
        return body

    bed = body.bounding_box().min.Z
    inner = body.edges().filter_by(
        lambda e: hypot(e.center().X, e.center().Y) < bore_r + 1.5
    )
    keep = body.edges().filter_by(lambda e: e.bounding_box().min.Z > bed)
    keep = keep - inner - concave_edges(body)
    return polish(body, keep, 1.0)
