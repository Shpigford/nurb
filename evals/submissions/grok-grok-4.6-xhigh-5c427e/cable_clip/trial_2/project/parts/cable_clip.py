from nurb import *


@part
def cable_clip(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Screw-down clip that holds a cable bundle in an open-top channel.

    bundle_diameter: how wide the taped cable bundle is across
    """
    wall = 2.4
    base = 3.0
    length = 12.0
    tab_length = 10.0
    hole_diameter = 4.2
    channel_width = bundle_diameter + 0.4
    channel_depth = bundle_diameter
    if bundle_diameter < 3.0:
        reject(
            f"bundle_diameter {bundle_diameter} is too small for a printable "
            "channel: raise it above 3.0",
            param="bundle_diameter",
        )

    body_width = channel_width + 2 * wall
    height = base + channel_depth
    total_x = body_width + tab_length

    profile = Plane.XZ * Polygon(
        (0, 0),
        (total_x, 0),
        (total_x, base),
        (body_width, base),
        (body_width, height),
        (body_width - wall, height),
        (body_width - wall, base),
        (wall, base),
        (wall, height),
        (0, height),
    )
    clip = extrude(profile, amount=length)

    span = clip.bounding_box()
    hole_x = body_width + tab_length / 2
    hole_y = (span.min.Y + span.max.Y) / 2
    hole = Cylinder(
        hole_diameter / 2,
        base + 2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    clip = clip - Pos(hole_x, hole_y, -1) * hole

    if draft:
        return clip

    # Channel interior is fit-critical: square floor the full width, no lead-in
    # at the mouth. Bed-lying edges stay off the polish pass so the first layer
    # is not a knife. Long Y edges never meet each other, so 1mm chamfers cannot
    # leave the three-chamfer corner slivers the checker would then fail.
    bed = clip.bounding_box().min.Z
    x0, x1, z0 = wall, wall + channel_width, base
    channel = ShapeList(
        e
        for e in clip.edges()
        if e.bounding_box().min.X >= x0 - 1e-4
        and e.bounding_box().max.X <= x1 + 1e-4
        and e.bounding_box().min.Z >= z0 - 1e-4
    )
    on_bed = ShapeList(
        e for e in clip.edges() if e.bounding_box().max.Z <= bed + 1e-4
    )
    keep = clip.edges().filter_by(Axis.Y) - on_bed - concave_edges(clip) - channel
    return polish(clip, keep, 1.0)
