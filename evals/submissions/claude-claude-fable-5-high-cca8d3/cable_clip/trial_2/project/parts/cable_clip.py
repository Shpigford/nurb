from nurb import *


@part
def cable_clip(
    bundle_diameter=measured("bundle_diameter"),
    wall_thickness=2.4,
    base_thickness=3.0,
    clip_length=12.0,
    tab_length=10.0,
    tab_thickness=3.0,
    screw_hole_width=4.2,
    draft=False,
):
    """Screw-down clip: an open-top channel holds the cable bundle, a flat tab
    beside it takes one screw.

    bundle_diameter: how thick the cable bundle is that the channel holds
    wall_thickness: how thick each channel wall is
    base_thickness: how much material sits under the cable
    clip_length: how long the clip runs along the cable
    tab_length: how far the screw tab sticks out sideways
    tab_thickness: how thick the screw tab is
    screw_hole_width: how wide the screw hole in the tab is
    """
    channel_width = bundle_diameter + 0.4
    channel_depth = bundle_diameter
    body_width = 2 * wall_thickness + channel_width
    height = base_thickness + channel_depth

    corner = (Align.MIN, Align.MIN, Align.MIN)
    body = Box(body_width, clip_length, height, align=corner)
    channel = Pos(wall_thickness, 0, base_thickness) * Box(
        channel_width, clip_length, channel_depth + 1, align=corner
    )
    tab = Pos(body_width, 0, 0) * Box(tab_length, clip_length, tab_thickness, align=corner)
    hole = Pos(body_width + tab_length / 2, clip_length / 2, 0) * Cylinder(
        screw_hole_width / 2, tab_thickness, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )

    clip = body + tab - channel - hole
    if draft:
        return clip

    # The channel is fit geometry: its floor, walls and mouth stay square, so
    # everything between the wall inner faces from the floor up is off limits.
    eps = 1e-4
    channel_min_x = wall_thickness
    channel_max_x = wall_thickness + channel_width
    concave = set(concave_edges(clip))
    keep = []
    for edge in clip.edges().filter_by(GeomType.LINE):  # circles are the hole's rims
        if edge in concave:
            continue
        bb = edge.bounding_box()
        if bb.max.Z <= eps:  # lying in the bed face
            continue
        if (
            bb.max.X >= channel_min_x - eps
            and bb.min.X <= channel_max_x + eps
            and bb.min.Z >= base_thickness - eps
        ):
            continue
        keep.append(edge)
    # 1.1mm, not the usual 1.0: the corner triangles where three chamfers meet
    # then come out at 0.866 * 1.1^2 = 1.05mm2, above the sliver line, and the
    # 2.4mm wall top still keeps 1.3mm of flat beside its chamfer.
    return polish(clip, keep, 1.1)
