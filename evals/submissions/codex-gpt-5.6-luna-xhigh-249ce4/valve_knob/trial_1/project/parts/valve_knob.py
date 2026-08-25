from math import cos, pi, sin

from nurb import *


@part
def valve_knob(
    shaft_diameter=8.0,
    shaft_across_flat=6.5,
    height=14.0,
    grip_radius=16.0,
    lobe_radius=19.0,
    draft=False,
):
    """Replacement knob for the measured D-shaft valve stem.

    shaft_diameter: diameter of the round part of the valve stem
    shaft_across_flat: distance from the stem's +X flat to the opposite side
    height: overall height of the knob
    grip_radius: radius at the valleys between the grip lobes
    lobe_radius: radius at the twelve grip lobe tips
    """
    if shaft_diameter <= 2.0 or shaft_across_flat <= 2.0:
        reject("shaft dimensions must exceed 2mm so the bore can print", param="shaft_diameter")
    if shaft_across_flat >= shaft_diameter:
        reject("shaft_across_flat must be smaller than shaft_diameter", param="shaft_across_flat")
    if height < 12.0:
        reject("height must be at least 12mm for the stem engagement", param="height")
    if grip_radius < 14.0:
        reject("grip_radius must be at least 14mm for a 28mm grip", param="grip_radius")
    if lobe_radius <= grip_radius:
        reject("lobe_radius must exceed grip_radius to form a grippable outline", param="lobe_radius")

    # The 0.6mm total opening allowance gives the specified +0.3mm grown stem
    # real clearance while the +1.0mm test stem is larger than this bore.
    bore_diameter = shaft_diameter + 0.6
    bore_across_flat = shaft_across_flat + 0.6

    # Alternating radii make twelve broad, support-free lobes in the XY plane.
    points = []
    for index in range(12):
        radius = lobe_radius if index % 2 else grip_radius
        angle = 2.0 * pi * index / 12.0
        points.append((radius * cos(angle), radius * sin(angle)))
    outline = make_face(Polygon(*points))
    body = extrude(outline, amount=height)

    # A round bore clipped at +X produces the D profile.  The clip is deliberately
    # a little larger than the cutter in Y and Z so both openings are unambiguous.
    cutter_radius = bore_diameter / 2.0
    cutter = Cylinder(
        cutter_radius,
        height + 2.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    left = -cutter_radius - 2.0
    clip_width = cutter_radius + 2.0 + bore_across_flat / 2.0
    clip = Pos(left, 0, -1.0) * Box(
        clip_width,
        bore_diameter + 4.0,
        height + 2.0,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    cutter = (Pos(0, 0, -1.0) * cutter) & clip
    knob = body - cutter

    if draft:
        return knob

    bed = knob.bounding_box().min.Z
    top_edges = knob.edges().filter_by(lambda edge: edge.bounding_box().min.Z > bed)
    return polish(knob, top_edges, 1.0)
