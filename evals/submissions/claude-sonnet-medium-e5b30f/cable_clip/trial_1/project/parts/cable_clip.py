import math

from nurb import *


@part
def cable_clip(bundle_diameter=measured("bundle_diameter"), draft=False):
    """
    bundle_diameter: the diameter of the cable bundle the clip grips
    """
    wall = 2.4
    base = 3.0
    length_y = 12.0
    tab_length = 10.0
    hole_dia = 4.2
    overshoot = 5.0

    channel_width = bundle_diameter + 0.4
    channel_depth = bundle_diameter
    body_width = channel_width + 2 * wall
    body_height = base + channel_depth

    body = Pos(body_width / 2, length_y / 2, body_height / 2) * Box(
        body_width, length_y, body_height
    )

    channel = Pos(
        body_width / 2, length_y / 2, base + (channel_depth + overshoot) / 2
    ) * Box(channel_width, length_y + 2 * overshoot, channel_depth + overshoot)

    tab = Pos(body_width + tab_length / 2, length_y / 2, base / 2) * Box(
        tab_length, length_y, base
    )

    hole = Pos(body_width + tab_length / 2, length_y / 2, base / 2) * Cylinder(
        hole_dia / 2, base + 2 * overshoot
    )

    solid = (body + tab) - channel - hole

    if draft:
        return solid

    concave = concave_edges(solid)
    bed = solid.bounding_box().min.Z
    hole_circumference = math.pi * hole_dia
    channel_x = (wall, wall + channel_width)
    wall_top_x = (0.0, wall, body_width - wall, body_width)

    def on_channel_rim(e):
        bb = e.bounding_box()
        return bb.min.X == bb.max.X and any(
            abs(bb.min.X - x) < 1e-6 for x in channel_x
        )

    def on_wall_top_end_cap(e):
        bb = e.bounding_box()
        if abs(bb.min.Z - body_height) > 1e-6 or abs(bb.max.Z - body_height) > 1e-6:
            return False
        if bb.min.Y != bb.max.Y:
            return False
        return any(
            abs(bb.min.X - x0) < 1e-6 and abs(bb.max.X - x1) < 1e-6
            for x0, x1 in (wall_top_x[0:2], wall_top_x[2:4])
        )

    keep = solid.edges().filter_by(lambda e: e.bounding_box().min.Z > bed)
    keep = keep.filter_by(lambda e: e not in concave)
    keep = keep.filter_by(lambda e: abs(e.length - hole_circumference) > 0.01)
    keep = keep.filter_by(lambda e: not on_channel_rim(e))
    keep = keep.filter_by(lambda e: not on_wall_top_end_cap(e))
    return polish(solid, keep, 1.0)
