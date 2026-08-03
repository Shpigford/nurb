from nurb import *


def _key(edge):
    c = edge.center()
    return (round(c.X, 4), round(c.Y, 4), round(c.Z, 4))


@part
def cable_clip(
    bundle_diameter=measured("bundle_diameter"),
    cable_clearance=0.4,
    wall_thickness=2.4,
    base_thickness=3.0,
    clip_length=12.0,
    tab_length=10.0,
    screw_hole_width=4.2,
    chamfer_size=1.15,
    draft=False,
):
    """A screw-down clip that traps a cable bundle in an open-top channel.

    bundle_diameter: how thick the cable bundle is across
    cable_clearance: extra room across the channel so the bundle drops in
    wall_thickness: how thick each channel wall is
    base_thickness: how much solid material sits under the cable
    clip_length: how far the clip runs along the cable
    tab_length: how far the screw tab sticks out past the wall
    screw_hole_width: width of the screw hole through the tab
    chamfer_size: how much is taken off each exposed outside edge
    """
    channel_width = bundle_diameter + cable_clearance
    channel_depth = bundle_diameter
    body_width = 2 * wall_thickness + channel_width
    height = base_thickness + channel_depth
    channel_x = wall_thickness + channel_width / 2
    hole_x = body_width + tab_length / 2

    # The channel is cut, not built from two walls, so its floor stays one face.
    body = Pos(body_width / 2, 0, height / 2) * Box(body_width, clip_length, height)
    body += Pos(hole_x, 0, base_thickness / 2) * Box(
        tab_length, clip_length, base_thickness
    )
    body -= Pos(channel_x, 0, base_thickness + channel_depth) * Box(
        channel_width, clip_length + 2, 2 * channel_depth
    )
    body -= Pos(hole_x, 0, base_thickness / 2) * Cylinder(
        screw_hole_width / 2, base_thickness + 2
    )

    if draft:
        return body

    bed = body.bounding_box().min.Z
    eps = 1e-6
    concave = {_key(e) for e in concave_edges(body)}

    def exposed(e):
        if _key(e) in concave:
            return False
        if e.geom_type != GeomType.LINE:
            return False  # the screw hole: no lead-in chamfer at a mating mouth
        bb = e.bounding_box()
        if bb.max.Z <= bed + eps:
            return False  # lies in the bed-contact face
        # Anything that so much as reaches the channel stays sharp: a chamfer on the
        # wall-top end edge looks outboard but shaves the inner wall's top corner.
        touches_channel = (
            bb.max.X >= wall_thickness - eps
            and bb.min.X <= wall_thickness + channel_width + eps
            and bb.max.Z >= base_thickness - eps
        )
        return not touches_channel

    return polish(body, body.edges().filter_by(exposed), chamfer_size)
