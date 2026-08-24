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
    """A screw-down cable clip: the bundle presses into the open channel and a
    flat tab screws the clip to the surface.

    bundle_diameter: how thick the cable bundle is across
    wall_thickness: how thick each channel wall is
    base_thickness: how much material sits under the cable
    clip_length: how long the clip runs along the cable
    tab_length: how far the mounting tab sticks out sideways
    screw_hole_width: how wide the screw hole in the tab is
    """
    if bundle_diameter < 2.0:
        reject(
            "bundle_diameter under 2 leaves a channel too small to print or use: raise it",
            param="bundle_diameter",
        )
    if screw_hole_width < 2.0:
        reject(
            "screw_hole_width under 2 prints as a smear: use 2 or more, or drill it",
            param="screw_hole_width",
        )

    channel_width = bundle_diameter + 0.4  # snug drop-in for the taped bundle
    channel_depth = bundle_diameter
    body_width = channel_width + 2 * wall_thickness
    height = base_thickness + channel_depth

    # Channel body, min corner at the origin, bed at z=0.
    body = Pos(body_width / 2, clip_length / 2, height / 2) * Box(
        body_width, clip_length, height
    )
    body -= Pos(
        wall_thickness + channel_width / 2,
        clip_length / 2,
        base_thickness + channel_depth / 2,
    ) * Box(channel_width, clip_length, channel_depth)

    # Mounting tab, flush with the bottom, off the +X wall.
    body += Pos(body_width + tab_length / 2, clip_length / 2, base_thickness / 2) * Box(
        tab_length, clip_length, base_thickness
    )
    body -= Pos(body_width + tab_length / 2, clip_length / 2, base_thickness / 2) * Cylinder(
        screw_hole_width / 2, base_thickness + 2
    )

    if draft:
        return body

    # Polish everything except the bottom face, the channel (fit geometry stays
    # square: no lead-ins, flat floor), the screw bore, and concave junctions.
    tol = 0.01
    cavity_centers = [e.center() for e in concave_edges(body)]

    def polishable(e):
        bb = e.bounding_box()
        if bb.max.Z < tol:  # lies in the bed face
            return False
        if (
            bb.min.Z > base_thickness - tol
            and bb.min.X < wall_thickness + channel_width + tol
            and bb.max.X > wall_thickness - tol
        ):
            # Bounds or touches the channel: chamfering the wall-top end edges
            # clips the channel's inner-face corners, so those stay sharp too.
            return False
        if e.geom_type == GeomType.CIRCLE:
            return False  # the screw bore stays a plain 4.2 hole
        c = e.center()
        if any((c - cc).length < tol for cc in cavity_centers):
            return False
        return True

    # 1.2 rather than the 1.0 default: the corner triangles three chamfers
    # leave then sit above the 1mm2 sliver bar instead of just under it.
    keep = body.edges().filter_by(polishable)
    return polish(body, keep, 1.2)
