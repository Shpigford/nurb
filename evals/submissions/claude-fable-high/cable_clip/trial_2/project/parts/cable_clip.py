from nurb import *


@part
def cable_clip(
    bundle_diameter=measured("bundle_diameter"),
    cable_clearance=0.4,
    wall_thickness=2.4,
    base_thickness=3.0,
    clip_length=12.0,
    tab_length=10.0,
    screw_hole_diameter=4.2,
    draft=False,
):
    """A screw-down clip: an open-top channel the cable presses into, with a flat
    tab to one side for a single screw.

    bundle_diameter: how wide the cable bundle measures across
    cable_clearance: extra channel width beyond the bundle, so it drops in
    wall_thickness: how thick each channel wall is
    base_thickness: how much material sits under the channel floor
    clip_length: how long the clip runs along the cable
    tab_length: how far the screw tab sticks out sideways
    screw_hole_diameter: how wide the screw hole is
    """
    channel_width = bundle_diameter + cable_clearance
    channel_depth = bundle_diameter
    body_width = channel_width + 2 * wall_thickness
    body_height = base_thickness + channel_depth

    body = Box(
        body_width, clip_length, body_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    channel = Pos(0, 0, base_thickness) * Box(
        channel_width, clip_length, channel_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    tab = Pos(body_width / 2, 0, 0) * Box(
        tab_length, clip_length, base_thickness,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    hole = Pos(body_width / 2 + tab_length / 2, 0, 0) * Cylinder(
        screw_hole_diameter / 2, base_thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    clip = body + tab - channel - hole

    if draft:
        return clip

    # Polish: chamfer exposed edges, excluding the bed face, concave junctions,
    # everything the channel touches (fit-critical: the cable slides in it), and
    # the screw hole rim.
    eps = 1e-3
    half_cw = channel_width / 2
    concave = concave_edges(clip)

    def excluded(e):
        bb = e.bounding_box()
        if bb.max.Z < eps:  # lies in the bed face
            return True
        if (bb.min.X < half_cw + eps and bb.max.X > -half_cw - eps
                and bb.min.Z > base_thickness - eps):
            # Touches the channel or its mouth. The channel is fit-critical, so
            # nothing chamfered may reach it, not even a top edge ending there.
            return True
        if e.geom_type == GeomType.CIRCLE:  # screw hole rim
            return True
        d = (e @ 1 - e @ 0).normalized()
        if abs(d.Z) > 1 - eps:  # vertical corners: chamfering them would leave
            return True         # sub-mm triangle facets where three chamfers meet
        c = e.center()
        return any((c - k.center()).length < eps for k in concave)

    keep = clip.edges().filter_by(lambda e: not excluded(e))
    return polish(clip, keep, 1.0)
