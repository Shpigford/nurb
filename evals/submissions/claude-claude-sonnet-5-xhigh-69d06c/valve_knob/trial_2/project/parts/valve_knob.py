import math

from nurb import *


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    height=16.0,
    grip_width=29.0,
    draft=False,
):
    """
    shaft_diameter: the valve's D-shaft, full diameter across the round side
    shaft_across_flat: the D-shaft's width from its flat to the far round side
    height: how tall the knob stands
    grip_width: how wide the hex grip measures across its flats
    """
    clearance = 0.6  # total growth the bore gets over the stem, on both diameter and across-flat
    bore_depth = 12.5  # a hair past the stem's 12mm proud, so the knob seats on the valve body, not the tip
    floor_min = 3.0
    wall_min = 2.5

    if height < bore_depth + floor_min:
        reject(
            f"height {height} is under the {bore_depth + floor_min}mm the {bore_depth}mm bore "
            f"depth plus a {floor_min}mm floor needs; raise it above {bore_depth + floor_min}",
            param="height",
        )

    bore_r = (shaft_diameter + clearance) / 2
    bore_x_flat = (shaft_across_flat + clearance) - bore_r

    apothem = grip_width / 2
    if apothem < bore_r + wall_min:
        reject(
            f"grip_width {grip_width} leaves under {wall_min}mm of wall around the "
            f"{2 * bore_r:.1f}mm bore; raise it above {2 * (bore_r + wall_min):.1f}",
            param="grip_width",
        )
    circumradius = apothem / math.cos(math.radians(30))

    body = extrude(RegularPolygon(circumradius, 6), height)

    # The bore's D-shape: a round hole with a flat facing +X, sized off the
    # grown stem so it seats the shaft and blocks it from spinning free.
    flat_cutter = Pos(X=bore_x_flat - 2 * bore_r) * Rectangle(4 * bore_r, 4 * bore_r)
    bore_profile = Circle(bore_r) & flat_cutter
    bore = extrude(bore_profile, bore_depth)
    bore = Pos(Z=height - bore_depth) * bore
    body = body - bore

    if draft:
        return body

    # Only the top rim: the bore's own edges are fit-critical and stay sharp,
    # and skipping the vertical corners here keeps every kept edge on its own
    # loop, clear of any three-chamfer corner.
    top_z = body.bounding_box().max.Z
    axis_threshold = (bore_r + apothem) / 2

    def is_top_rim(e):
        bb = e.bounding_box()
        on_top = abs(bb.min.Z - top_z) < 1e-6 and abs(bb.max.Z - top_z) < 1e-6
        far_from_bore = math.hypot(bb.center().X, bb.center().Y) > axis_threshold
        return on_top and far_from_bore

    keep = body.edges().filter_by(is_top_rim)
    return polish(body, keep, 1.0)
