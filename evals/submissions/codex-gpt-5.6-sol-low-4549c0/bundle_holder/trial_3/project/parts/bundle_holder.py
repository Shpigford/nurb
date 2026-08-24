from nurb import *


@part
def bundle_holder(bundle_diameter=8.0, draft=False):
    """A wall-mounted, thread-through holder for a horizontal cable bundle.

    bundle_diameter: measured width of the cable bundle the tunnel holds
    """
    clearance = 0.4
    # 1.2 mm is three 0.4 mm extrusion lines: printable, but lean enough to keep
    # this small non-structural clip well inside its material budget.
    wall = 1.2
    length = 12.0
    cable_width = bundle_diameter + clearance
    outside = cable_width + 2.0 * wall

    # Square outside gives a broad wall face and a stable, support-free footprint.
    tunnel = Box(outside, length, outside, align=(Align.MIN, Align.MIN, Align.MIN))
    cable_space = Pos(wall + cable_width / 2.0, 0, wall + cable_width / 2.0) * (
        Rot(-90, 0, 0) * Cylinder(
            cable_width / 2.0,
            length,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    )
    tunnel = tunnel - cable_space

    # The screw sits above the cable so its shank and pan head cannot obstruct it.
    boss_center_z = outside + 5.5
    boss_depth = 7.0
    boss_width = 10.4
    boss = Pos(0, (length - boss_width) / 2.0, outside - wall) * Box(
        boss_depth,
        boss_width,
        15.0,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    body = tunnel + boss

    # Circumscribed 45-degree pockets clear the round fastener while giving every
    # internal roof printable slopes. Three millimetres precede the head seat.
    bore_r = 2.2
    bore_span = bore_r * 2 ** 0.5
    bore_profile = Plane.YZ * Polygon(
        (0, -bore_span),
        (bore_span, 0),
        (0, bore_span),
        (-bore_span, 0),
    )
    screw_bore = Pos(0, length / 2.0, boss_center_z) * extrude(
        bore_profile, 3.0
    )

    head_r = 4.2
    roof = head_r * 2 ** 0.5
    head_profile = Plane.YZ * Polygon(
        (-head_r, -head_r),
        (head_r, -head_r),
        (head_r, roof - head_r),
        (0, roof),
        (-head_r, roof - head_r),
    )
    head_space = Pos(3.0, length / 2.0, boss_center_z) * extrude(
        head_profile, boss_depth
    )
    body = body - screw_bore - head_space

    if draft:
        return body
    return body
