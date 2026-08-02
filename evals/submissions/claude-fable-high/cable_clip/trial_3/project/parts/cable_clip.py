from nurb import *


@part
def cable_clip(
    bundle_diameter=measured("bundle_diameter"),
    wall_thickness=2.4,
    base_thickness=3.0,
    clip_length=12.0,
    tab_length=10.0,
    screw_hole_width=4.2,
    draft=False,
):
    """A screw-down clip: the cable lies in an open channel, a flat tab takes the screw.

    bundle_diameter: how wide the cable bundle measures across
    wall_thickness: how thick each channel wall is
    base_thickness: how much material sits under the cable
    clip_length: how long the clip runs along the cable
    tab_length: how far the screw tab sticks out sideways
    screw_hole_width: how wide the screw hole is
    """
    channel_width = bundle_diameter + 0.4
    channel_depth = bundle_diameter
    body_width = channel_width + 2 * wall_thickness
    body_height = base_thickness + channel_depth

    body = Pos(body_width / 2, 0, body_height / 2) * Box(
        body_width, clip_length, body_height
    )
    channel = Pos(
        wall_thickness + channel_width / 2, 0, base_thickness + (channel_depth + 1) / 2
    ) * Box(channel_width, clip_length + 2, channel_depth + 1)
    body -= channel

    tab = Pos(body_width + (tab_length - 1) / 2, 0, base_thickness / 2) * Box(
        tab_length + 1, clip_length, base_thickness
    )
    hole = Pos(body_width + tab_length / 2, 0, base_thickness / 2) * Cylinder(
        screw_hole_width / 2, base_thickness + 2
    )
    clip = body + tab - hole

    if draft:
        return clip

    # The channel is fit geometry and the bottom is the bed face; neither is polished.
    bed = clip.bounding_box().min.Z
    channel_lo = wall_thickness - 1e-6
    channel_hi = wall_thickness + channel_width + 1e-6

    def exposed(e):
        bb = e.bounding_box()
        if bb.max.Z <= bed + 1e-6:
            return False
        if channel_lo <= bb.min.X and bb.max.X <= channel_hi:
            if bb.max.Z >= base_thickness - 1e-6:
                return False
        # Vertical corners stay sharp: chamfering them leaves sub-1mm2 corner
        # triangles where three chamfers meet.
        if bb.max.X - bb.min.X < 1e-6 and bb.max.Y - bb.min.Y < 1e-6:
            return False
        return True

    concave = concave_edges(clip)
    keep = [
        e
        for e in clip.edges().filter_by(GeomType.LINE).filter_by(exposed)
        if e not in concave
    ]
    return polish(clip, keep, 1.0)
