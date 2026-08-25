from nurb import *
import math


def _d_profile(diameter: float, across_flat: float):
    """D-shaft cross-section: round of `diameter` with flat facing +X at across-flat."""
    r = diameter / 2.0
    flat_x = across_flat - r
    with BuildSketch() as sk:
        Circle(r)
        # Drop the cap beyond the flat (material on the +X side of the flat plane).
        with Locations((flat_x + r + 1.0, 0)):
            Rectangle(2.0 * r + 2.0, 2.0 * r + 2.0, mode=Mode.SUBTRACT)
    return sk.sketch


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    knob_width=32.0,
    height=14.0,
    floor_thickness=2.0,
    bore_clearance=0.4,
    draft=False,
):
    """Replacement knob for a broken valve handle on a D-shaft stem.

    shaft_diameter: round diameter of the valve stem
    shaft_across_flat: stem size from the flat face to the opposite round side
    knob_width: distance across the hex flats (grip size)
    height: overall printed height, bore opening upward
    floor_thickness: solid bed under the blind bore (becomes the knob top in use)
    bore_clearance: added to both stem diameter and across-flat for print fit
    """
    if shaft_across_flat >= shaft_diameter:
        reject(
            f"shaft_across_flat {shaft_across_flat} must be under shaft_diameter "
            f"{shaft_diameter}",
            param="shaft_across_flat",
        )
    if bore_clearance < 0.3:
        reject(
            f"bore_clearance {bore_clearance} must be at least 0.3 so a +0.3 stem fits",
            param="bore_clearance",
        )
    if bore_clearance >= 1.0:
        reject(
            f"bore_clearance {bore_clearance} must stay under 1.0 so a +1.0 stem jams",
            param="bore_clearance",
        )
    if height < 12.0:
        reject(f"height {height} must be at least 12.0 for stem engagement", param="height")
    if knob_width < 28.0:
        reject(f"knob_width {knob_width} must be at least 28.0 for grip", param="knob_width")
    if floor_thickness < 1.5:
        reject(
            f"floor_thickness {floor_thickness} is too thin to print as a closed top",
            param="floor_thickness",
        )

    # Hex prism, flat-to-flat = knob_width. Vertex radius from across-flats.
    hex_r = (knob_width / 2.0) / math.cos(math.pi / 6.0)
    body = extrude(RegularPolygon(hex_r, 6), height)

    if not draft:
        bed = body.bounding_box().min.Z
        # Keep the bed face sharp; polish everything else before cutting the bore
        # so the D-bore mating edges stay fit-critical and unchamfered.
        keep = body.edges().filter_by(lambda e: e.bounding_box().min.Z > bed + 1e-4)
        body = polish(body, keep, 1.0)

    bore_d = shaft_diameter + bore_clearance
    bore_af = shaft_across_flat + bore_clearance
    # Blind bore opens at the top (+Z); cutter overruns the top face slightly.
    cutter = Pos(0, 0, floor_thickness) * extrude(
        _d_profile(bore_d, bore_af), height - floor_thickness + 1.0
    )
    return body - cutter
