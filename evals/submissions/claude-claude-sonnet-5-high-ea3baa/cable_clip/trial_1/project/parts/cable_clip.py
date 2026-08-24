from nurb import *


@part
def cable_clip(bundle_diameter=measured("bundle_diameter"), draft=False):
    """
    bundle_diameter: the diameter of the cable bundle the clip grips
    """
    clearance = 0.4
    wall = 2.4
    base = 3.0
    length = 12.0
    tab_length = 10.0
    tab_thickness = base
    hole_dia = 4.2

    channel_width = bundle_diameter + clearance
    channel_depth = bundle_diameter
    block_width = wall + channel_width + wall
    height = base + channel_depth

    block = Box(
        block_width, length, height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    channel = Box(
        channel_width, length, channel_depth,
        align=(Align.CENTER, Align.MIN, Align.MIN),
    ).translate((block_width / 2, 0, height - channel_depth))
    body = block - channel

    tab = Box(
        tab_length, length, tab_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    ).translate((-tab_length, 0, 0))
    hole = Cylinder(
        hole_dia / 2, tab_thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).translate((-tab_length / 2, length / 2, 0))
    tab = tab - hole

    body = body + tab

    if draft:
        return body

    bed = body.bounding_box().min.Z
    concave = concave_edges(body)
    channel_x_min = wall
    channel_x_max = wall + channel_width

    def in_channel(edge):
        bb = edge.bounding_box()
        return bb.max.X > channel_x_min - 1e-6 and bb.min.X < channel_x_max + 1e-6 and bb.max.Z > height - channel_depth - 1e-6

    def is_hole_rim(edge):
        return edge.geom_type == GeomType.CIRCLE

    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed + 1e-6
        and e not in concave
        and not in_channel(e)
        and not is_hole_rim(e)
    )
    return polish(body, keep, 1.0)
