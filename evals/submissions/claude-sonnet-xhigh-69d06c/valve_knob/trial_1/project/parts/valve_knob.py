from math import cos, radians, sin

from nurb import *


def _d_shape(radius, flat_offset):
    """A circle with the cap beyond `flat_offset` on +X cut away, D-shaft style."""
    big = radius * 4
    cutter = Pos(flat_offset + big / 2, 0, 0) * Rectangle(big, big)
    return Circle(radius) - cutter


def _rib(angle, inner_r, outer_r, width):
    """A radial grip rib, from `inner_r` to `outer_r`, `width` wide tangentially."""
    length = outer_r - inner_r
    center_r = (inner_r + outer_r) / 2
    blade = Pos(center_r, 0, 0) * Rectangle(length, width)
    return Rot(0, 0, angle) * blade


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    bore_clearance=0.35,
    grip_width=29.2,
    rib_reach=17.2,
    rib_count=6,
    rib_width=4.0,
    height=14.0,
    cap_thickness=3.0,
    draft=False,
):
    """A replacement knob for a broken D-shaft valve handle.

    shaft_diameter: the stem's diameter across its round side
    shaft_across_flat: the stem's narrower measurement, across the ground flat
    bore_clearance: how much room the bore leaves around the stem, on every side
    grip_width: how wide the knob measures hand-to-hand at its narrowest
    rib_reach: how far the grip ribs stick out from the centerline at their widest
    rib_count: how many grip ribs ring the knob
    rib_width: how wide each grip rib is, tip to tip sideways
    height: how tall the knob stands, base to top
    cap_thickness: how thick the solid cap above the bore's floor is
    """
    if cap_thickness <= 0 or cap_thickness >= height:
        reject(
            f"cap_thickness {cap_thickness:g} has to sit strictly between 0 and "
            f"height {height:g}, so the bore has both a floor and some depth",
            param="cap_thickness",
        )
    grip_radius = grip_width / 2
    shaft_radius = shaft_diameter / 2
    shaft_flat = shaft_across_flat - shaft_radius
    bore_radius = shaft_radius + bore_clearance
    bore_flat = shaft_flat + bore_clearance
    bore_reach = max(bore_radius, bore_flat)
    if bore_reach + 3.0 > grip_radius:
        reject(
            f"grip_width {grip_width:g} leaves under 3mm of wall around a "
            f"{2 * bore_reach:g}mm bore; raise grip_width above {2 * (bore_reach + 3.0):g}",
            param="grip_width",
        )
    if rib_reach <= grip_radius:
        reject(
            f"rib_reach {rib_reach:g} has to clear grip_width's radius "
            f"{grip_radius:g} for the ribs to add any grip",
            param="rib_reach",
        )

    outline = Circle(grip_radius)
    for i in range(rib_count):
        angle = 360.0 / rib_count * i
        outline = outline + _rib(angle, grip_radius - 2.0, rib_reach, rib_width)

    body = extrude(outline, height)

    bore_depth = height - cap_thickness
    bore = extrude(_d_shape(bore_radius, bore_flat), bore_depth)
    bore = Pos(0, 0, cap_thickness) * bore
    body = body - bore

    if draft:
        return body

    concave = concave_edges(body)
    bed = body.bounding_box().min.Z
    guard = bore_reach + 2.0

    def _far(edge):
        box = edge.bounding_box()
        return max(abs(box.min.X), abs(box.max.X), abs(box.min.Y), abs(box.max.Y))

    keep = body.edges().filter_by(
        lambda e: e not in concave and e.bounding_box().min.Z > bed + 1e-6 and _far(e) > guard
    )
    return polish(body, keep, 1.0)
