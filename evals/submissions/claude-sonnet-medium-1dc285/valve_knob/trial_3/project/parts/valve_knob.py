from nurb import *
from build123d import Circle, Rectangle, Pos, Rot, extrude


def d_profile(diameter, across_flat):
    """A round profile truncated by one flat, flat facing +X."""
    r = diameter / 2.0
    flat_x = across_flat - r
    cutter_size = diameter * 2.0
    cutter = Pos(flat_x + cutter_size / 2.0, 0) * Rectangle(cutter_size, cutter_size)
    return Circle(r) - cutter


@part
def valve_knob(
    shaft_diameter=8.0,
    shaft_across_flat=6.5,
    grip_radius=14.2,
    lobe_reach=2.2,
    height=15.0,
    bore_depth=11.5,
    fin_count=6,
    fin_width=4.0,
    draft=False,
):
    """
    shaft_diameter: the D-shaft's full round diameter the bore must clear
    shaft_across_flat: the D-shaft's narrower flat-to-round distance the bore must clear
    grip_radius: the knob's narrowest reach from centerline, for wet-hand grip
    lobe_reach: how much farther the ribs stick out past the grip radius
    height: how tall the knob stands
    bore_depth: how deep the D-shaped bore is cut from the top face
    fin_count: how many grip ribs run around the knob
    fin_width: how wide each grip rib is
    """
    lobe_radius = grip_radius + lobe_reach

    profile = Circle(grip_radius)
    for i in range(fin_count):
        angle = 360.0 / fin_count * i
        fin = (
            Rot(0, 0, angle)
            * Pos((grip_radius + lobe_radius) / 2.0, 0)
            * Rectangle(lobe_radius - grip_radius + 2.0, fin_width)
        )
        profile = profile + fin

    body = extrude(profile, height)

    bore_dia = shaft_diameter + 0.5
    bore_flat = shaft_across_flat + 0.5
    bore_profile = d_profile(bore_dia, bore_flat)
    bore = Pos(0, 0, height - bore_depth) * extrude(bore_profile, bore_depth + 1.0)
    body = body - bore

    if draft:
        return body

    bed = body.bounding_box().min.Z
    concave = set(concave_edges(body))
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed and e not in concave
    )
    return polish(body, keep, 1.0)
