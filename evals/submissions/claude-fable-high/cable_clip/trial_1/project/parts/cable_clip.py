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
    """A screw-down clip: the cable bundle lies in an open-top channel and a
    flat tab takes one screw beside it.

    bundle_diameter: how wide the cable bundle measures across
    wall_thickness: how thick each channel wall is
    base_thickness: how much material sits under the cable
    clip_length: how long the clip runs along the cable
    tab_length: how far the screw tab sticks out sideways
    screw_hole_width: how wide the screw hole is
    """
    clearance = 0.4
    channel_width = bundle_diameter + clearance
    channel_depth = bundle_diameter
    body_width = channel_width + 2 * wall_thickness
    height = base_thickness + channel_depth

    body = Box(body_width, clip_length, height,
               align=(Align.MIN, Align.MIN, Align.MIN))
    channel = Pos(wall_thickness, 0, base_thickness) * Box(
        channel_width, clip_length, channel_depth,
        align=(Align.MIN, Align.MIN, Align.MIN))
    body -= channel

    tab = Pos(body_width, 0, 0) * Box(
        tab_length, clip_length, base_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN))
    body += tab

    hole = Pos(body_width + tab_length / 2, clip_length / 2, 0) * Cylinder(
        screw_hole_width / 2, 3 * base_thickness)
    body -= hole

    if draft:
        return body

    # The channel and the screw hole are fit geometry and stay sharp; the
    # bottom face lies on the bed. Everything else convex gets the chamfer.
    tol = 1e-4

    def exposed(e):
        bb = e.bounding_box()
        if bb.max.Z <= tol:
            return False
        in_channel = (bb.min.X >= wall_thickness - tol
                      and bb.max.X <= wall_thickness + channel_width + tol
                      and bb.min.Z >= base_thickness - tol)
        if in_channel:
            return False
        # A wall-top end edge runs into the channel mouth, and its chamfer
        # would clip the inner wall face, so the channel stays square there.
        touches_mouth = (bb.min.Z >= height - tol
                         and bb.max.X >= wall_thickness - tol
                         and bb.min.X <= wall_thickness + channel_width + tol)
        if touches_mouth:
            return False
        if e.geom_type == GeomType.CIRCLE:
            return False
        return True

    # 1.2mm rather than the 1mm default: the corner triangles where three
    # chamfers meet then land above the 1mm2 sliver floor instead of under it.
    keep = body.edges().filter_by(exposed) - concave_edges(body)
    return polish(body, keep, 1.2)
