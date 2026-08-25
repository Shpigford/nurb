from nurb import *


@part
def cable_clip(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Screw-down clip that holds a cable bundle against a surface.

    bundle_diameter: measured width of the cable bundle the channel holds
    """
    clearance = 0.4
    wall = 2.4
    base = 3.0
    length = 12.0
    tab_length = 10.0
    hole_dia = 4.2

    if bundle_diameter <= 0:
        reject(
            "bundle_diameter must be positive so the channel has a floor",
            param="bundle_diameter",
        )

    channel_width = bundle_diameter + clearance
    channel_depth = bundle_diameter
    body_width = channel_width + 2 * wall
    height = base + channel_depth

    body = Box(body_width, length, height).moved(
        Location((body_width / 2, 0, height / 2))
    )
    cut = Box(channel_width, length + 2.0, channel_depth + 1.0).moved(
        Location((wall + channel_width / 2, 0, base + (channel_depth + 1.0) / 2))
    )
    tab = Box(tab_length, length, base).moved(
        Location((body_width + tab_length / 2, 0, base / 2))
    )
    hole = Cylinder(hole_dia / 2, base + 2.0).moved(
        Location((body_width + tab_length / 2, 0, base / 2))
    )
    clip = (body + tab) - cut - hole

    if draft:
        return clip

    # Polish only long horizontal edges along Y. That keeps the channel square,
    # leaves the screw hole untouched, and avoids the tiny corner triangles a
    # three-way 1mm chamfer leaves on the wall tops.
    bed = clip.bounding_box().min.Z
    channel_x_max = wall + channel_width

    def polishable(edge):
        bb = edge.bounding_box()
        dx = bb.max.X - bb.min.X
        dy = bb.max.Y - bb.min.Y
        dz = bb.max.Z - bb.min.Z
        if bb.min.Z <= bed + 1e-4:
            return False
        if bb.min.X >= wall - 1e-3 and bb.max.X <= channel_x_max + 1e-3 and bb.min.Z >= base - 1e-3:
            return False
        return dy > 5.0 and dx < 0.2 and dz < 0.2

    keep = clip.edges().filter_by(polishable)
    keep = keep - concave_edges(clip)
    return polish(clip, keep, 1.0)
