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
    """A screw-down clip that holds a cable bundle in an open-top channel.

    bundle_diameter: how thick the cable bundle is that the channel holds
    wall_thickness: how thick each channel wall is
    base_thickness: how much material sits under the cable
    clip_length: how long the clip runs along the cable
    tab_length: how far the mounting tab sticks out sideways
    screw_hole_width: how wide the screw hole in the tab is
    """
    if bundle_diameter < 2.0:
        reject(
            "bundle_diameter under 2 leaves a channel too small to print cleanly: "
            "raise it to 2 or more",
            param="bundle_diameter",
        )

    channel_width = bundle_diameter + 0.4
    channel_depth = bundle_diameter
    body_width = channel_width + 2 * wall_thickness
    body_height = channel_depth + base_thickness

    body = Pos(body_width / 2, clip_length / 2, body_height / 2) * Box(
        body_width, clip_length, body_height
    )
    channel = Pos(
        wall_thickness + channel_width / 2,
        clip_length / 2,
        base_thickness + channel_depth / 2,
    ) * Box(channel_width, clip_length, channel_depth)
    tab = Pos(body_width + tab_length / 2, clip_length / 2, base_thickness / 2) * Box(
        tab_length, clip_length, base_thickness
    )
    hole = Pos(body_width + tab_length / 2, clip_length / 2, base_thickness / 2) * Cylinder(
        screw_hole_width / 2, base_thickness + 2
    )

    clip = body + tab - channel - hole

    if draft:
        return clip

    # The channel is the fit: nothing inside it or at its mouth gets touched.
    bed = clip.bounding_box().min.Z
    tol = 1e-4
    inner_lo = wall_thickness - tol
    inner_hi = wall_thickness + channel_width + tol
    concave_centers = [e.center() for e in concave_edges(clip)]

    def wants_chamfer(e):
        if e.geom_type != GeomType.LINE:
            return False
        bb = e.bounding_box()
        if bb.max.Z <= bed + tol:  # lies in the bed face
            return False
        # Any edge reaching the channel opening is out: a chamfer that so much as
        # ends there nicks the channel's inner faces and flares the mouth.
        if bb.max.X > inner_lo and bb.min.X < inner_hi and bb.max.Z > base_thickness - tol:
            return False
        c = e.center()
        return all((c - cc).length > tol for cc in concave_centers)

    # 1.1 rather than the usual 1.0 so the corner triangles where three chamfers
    # meet land above the 1.0mm2 sliver threshold instead of just under it.
    keep = clip.edges().filter_by(wants_chamfer)
    return polish(clip, keep, 1.1)
