from nurb import *


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    draft=False,
):
    """Replacement knob for a broken D-shaft valve handle.

    shaft_diameter: full round diameter of the valve stem
    shaft_across_flat: stem size from the flat to the opposite round
    """
    if shaft_across_flat >= shaft_diameter:
        reject(
            f"shaft_across_flat {shaft_across_flat} must be under shaft_diameter {shaft_diameter} so the D-flat can turn the stem",
            param="shaft_across_flat",
        )
    if shaft_diameter < 4.0:
        reject(
            f"shaft_diameter {shaft_diameter} is too small to print a D-bore around",
            param="shaft_diameter",
        )

    # Prints bore-up: D-bore opens at the top, flat facing +X. Flip onto the stem to use.
    height = 12.5
    hub_radius = 15.0
    arm_width = 6.0
    tip_radius = 4.0
    reach = 36.0
    # Between the 0.3-grown slip stem and the 1.0-grown rattle stem.
    clearance = 0.8

    hub = Cylinder(hub_radius, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    body = hub
    tip_center = reach - tip_radius
    for angle in (0.0, 120.0, 240.0):
        loc = Rot(0, 0, angle)
        bar = loc * Pos(tip_center / 2.0, 0, 0) * Box(
            tip_center,
            arm_width,
            height,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        tip = loc * Pos(tip_center, 0, 0) * Cylinder(
            tip_radius,
            height,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        body = body + bar + tip

    bore_dia = shaft_diameter + clearance
    bore_across = shaft_across_flat + clearance
    bore_r = bore_dia / 2.0
    flat_x = bore_across - bore_r
    cap = Pos(flat_x + bore_r + 1.0, 0) * Rectangle(2.0 * bore_r + 2.0, 2.0 * bore_r + 4.0)
    profile = Circle(bore_r) - cap
    cutter = Pos(0, 0, -1.0) * extrude(profile, amount=height + 2.0)
    body = body - cutter

    if draft:
        return body
    bed = body.bounding_box().min.Z
    keep = body.edges().filter_by(lambda e: e.bounding_box().min.Z > bed + 0.05)
    return polish(body, keep, 1.0)
