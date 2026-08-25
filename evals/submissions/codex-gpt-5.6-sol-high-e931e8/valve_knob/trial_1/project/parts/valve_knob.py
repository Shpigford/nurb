from nurb import *


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    knob_height=14.5,
    grip_width=30.0,
    grip_reach=18.0,
    bore_clearance=0.5,
    bore_depth=12.25,
    draft=False,
):
    """A support-free replacement knob for a valve's D-shaped stem.

    shaft_diameter: measured diameter of the valve stem
    shaft_across_flat: measured distance from the stem flat to its round side
    knob_height: overall printed height of the knob
    grip_width: narrow outside width of the hand grip
    grip_reach: farthest reach of each grip lobe from the centerline
    bore_clearance: total extra size added to both D-shaft measurements
    bore_depth: depth of the stem socket measured down from the top
    """
    if shaft_diameter <= 0.0:
        reject("shaft_diameter must be positive", param="shaft_diameter")
    if not shaft_diameter / 2.0 < shaft_across_flat < shaft_diameter:
        reject(
            "shaft_across_flat must be between half the shaft diameter and the full diameter",
            param="shaft_across_flat",
        )
    if grip_reach <= grip_width / 2.0:
        reject(
            "grip_reach must be greater than half grip_width to form the turning lobes",
            param="grip_reach",
        )
    if knob_height - bore_depth < 2.0:
        reject(
            "bore_depth leaves under 2mm of material at the bottom; reduce it or raise knob_height",
            param="bore_depth",
        )

    grip_radius = grip_width / 2.0
    lobe_offset = grip_reach - grip_radius

    center = Box(
        2.0 * lobe_offset,
        grip_width,
        knob_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    left_lobe = Pos(-lobe_offset, 0.0, 0.0) * Cylinder(
        grip_radius,
        knob_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    right_lobe = Pos(lobe_offset, 0.0, 0.0) * Cylinder(
        grip_radius,
        knob_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    body = center + left_lobe + right_lobe

    bore_radius = (shaft_diameter + bore_clearance) / 2.0
    bore_across_flat = shaft_across_flat + bore_clearance
    flat_x = bore_across_flat - bore_radius
    bore_bottom = knob_height - bore_depth

    round_bore = Pos(0.0, 0.0, bore_bottom) * Cylinder(
        bore_radius,
        bore_depth + 0.1,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    flat_clip = Pos(-bore_radius, 0.0, bore_bottom) * Box(
        bore_radius + flat_x,
        2.0 * bore_radius + 1.0,
        bore_depth + 0.1,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    d_bore = round_bore & flat_clip
    body = body - d_bore

    if draft:
        return body

    outer_top_edges = body.edges().filter_by(
        lambda edge: edge.bounding_box().min.Z > knob_height - 0.01
        and (
            edge.bounding_box().max.X > grip_radius
            or edge.bounding_box().min.X < -grip_radius
            or edge.bounding_box().max.Y > bore_radius + 1.0
            or edge.bounding_box().min.Y < -bore_radius - 1.0
        )
    )
    return polish(body, outer_top_edges, 1.0)
