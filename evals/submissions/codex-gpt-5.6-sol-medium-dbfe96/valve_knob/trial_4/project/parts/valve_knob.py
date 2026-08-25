from nurb import *


@part
def valve_knob(
    shaft_diameter: float = 8.0,
    shaft_across_flat: float = 6.5,
    knob_height: float = 18.0,
    grip_width: float = 38.0,
):
    """A compact, two-lobed replacement knob for a D-shaped valve stem.

    shaft_diameter: diameter of the round portion of the valve stem
    shaft_across_flat: distance from the stem's flat to its opposite round side
    knob_height: overall printed height of the knob
    grip_width: overall reach across the two opposed grip lobes
    """
    hub_radius = 14.5
    lobe_radius = 5.0
    lobe_offset = grip_width / 2.0 - lobe_radius

    body = Cylinder(hub_radius, knob_height)
    body = body + Pos(lobe_offset, 0, 0) * Cylinder(lobe_radius, knob_height)
    body = body + Pos(-lobe_offset, 0, 0) * Cylinder(lobe_radius, knob_height)

    # Clearance is 0.6 mm on each measured overall dimension: the 0.3-grown
    # verification stem passes, while the 1.0-grown stem remains an interference.
    bore_diameter = shaft_diameter + 0.6
    bore_across_flat = shaft_across_flat + 0.6
    bore_radius = bore_diameter / 2.0
    flat_x = bore_across_flat - bore_radius
    bore_depth = min(12.5, knob_height - 3.0)
    bore_center_z = knob_height / 2.0 - bore_depth / 2.0

    round_bore = Pos(0, 0, bore_center_z) * Cylinder(
        bore_radius, bore_depth + 0.1
    )
    clip_width = bore_radius + flat_x
    clip_center_x = (flat_x - bore_radius) / 2.0
    flat_limit = Pos(clip_center_x, 0, bore_center_z) * Box(
        clip_width, 2.0 * bore_radius, bore_depth + 0.1
    )
    d_bore = round_bore & flat_limit
    body = body - d_bore

    # Keep the functional bore and first-layer perimeter sharp. Chamfering the
    # mixed line/arc D profile creates tiny sliver faces and changes its fit.
    return body
