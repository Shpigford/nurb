from nurb import *


@part
def cable_clip(
    bundle_diameter=measured("bundle_diameter"),
    cable_clearance=0.4,
    wall_thickness=2.4,
    base_thickness=3.0,
    clip_length=12.0,
    tab_length=10.0,
    screw_hole_width=4.2,
    draft=False,
):
    """A screw-down cable clip: the bundle lies in an open channel, one screw holds it.

    bundle_diameter: how wide the cable bundle is, straight across
    cable_clearance: extra channel width so the bundle drops in
    wall_thickness: how thick each channel wall is
    base_thickness: how much material sits under the cable and in the tab
    clip_length: how long the clip runs along the cable
    tab_length: how far the screw tab sticks out sideways
    screw_hole_width: how wide the screw hole is
    """
    if bundle_diameter < 2.0:
        reject(
            "bundle_diameter under 2mm makes a channel too narrow to print: "
            "raise it to 2 or more",
            param="bundle_diameter",
        )

    channel_width = bundle_diameter + cable_clearance
    channel_depth = bundle_diameter
    body_width = channel_width + 2 * wall_thickness
    height = base_thickness + channel_depth

    body = Pos(0, 0, height / 2) * Box(body_width, clip_length, height)
    body -= Pos(0, 0, base_thickness + channel_depth / 2) * Box(
        channel_width, clip_length, channel_depth
    )

    body += Pos(body_width / 2 + tab_length / 2, 0, base_thickness / 2) * Box(
        tab_length, clip_length, base_thickness
    )
    body -= Pos(body_width / 2 + tab_length / 2, 0, base_thickness / 2) * Cylinder(
        screw_hole_width / 2, base_thickness
    )

    if draft:
        return body

    concave = set(concave_edges(body))
    half_channel = channel_width / 2
    eps = 1e-6

    def polishable(e):
        bb = e.bounding_box()
        if bb.max.Z <= eps:  # lies in the bed-contact face
            return False
        if e in concave:
            return False
        # nothing touching the channel: it is fit geometry, and even an edge that
        # only ends on the rim would chamfer a lead-in into the mouth
        if (
            bb.min.X <= half_channel + eps
            and bb.max.X >= -half_channel - eps
            and bb.max.Z >= base_thickness - eps
        ):
            return False
        # the screw bore's rim stays sharp so the hole prints at size
        if bb.min.X > body_width / 2 and e.geom_type == GeomType.CIRCLE:
            return False
        return True

    keep = body.edges().filter_by(polishable)
    # 1.1 rather than the default 1.0: the corner triangles where three chamfers
    # meet then land above the 1mm2 sliver threshold instead of just under it.
    return polish(body, keep, 1.1)
