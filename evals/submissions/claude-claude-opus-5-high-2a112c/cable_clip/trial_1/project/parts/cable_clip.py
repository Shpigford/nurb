from nurb import *


def _key(edge):
    c = edge.center()
    return (round(c.X, 4), round(c.Y, 4), round(c.Z, 4), round(edge.length, 4))


@part
def cable_clip(
    bundle_diameter=measured("bundle_diameter"),
    cable_clearance=0.4,
    wall_thickness=2.4,
    base_thickness=3.0,
    clip_length=12.0,
    tab_length=10.0,
    screw_hole_width=4.2,
    chamfer_size=1.0,
    draft=False,
):
    """A screw-down clip: the cable drops into an open channel, a screw through the
    side tab pulls the whole thing against the surface.

    bundle_diameter: how thick the cable bundle is across
    cable_clearance: extra channel width over the bundle, so it drops in
    wall_thickness: how thick each of the two channel walls is
    base_thickness: how much material sits under the cable, and how thick the tab is
    clip_length: how far the clip runs along the cable
    tab_length: how far the screw tab sticks out sideways past the wall
    screw_hole_width: the width of the screw hole through the tab
    chamfer_size: how big the chamfer on the exposed outside edges is
    """
    channel_width = bundle_diameter + cable_clearance
    channel_depth = bundle_diameter

    if channel_width < 2.0:
        reject(
            f"bundle_diameter {bundle_diameter} leaves a {channel_width:.1f}mm channel, "
            "which is narrower than a nozzle can cut: raise it above 1.6",
            param="bundle_diameter",
        )
    if screw_hole_width + 2 * chamfer_size >= tab_length:
        reject(
            f"tab_length {tab_length} has no material left around a "
            f"{screw_hole_width}mm hole: raise it above "
            f"{screw_hole_width + 2 * chamfer_size:.1f}",
            param="tab_length",
        )

    body_width = channel_width + 2 * wall_thickness
    height = base_thickness + channel_depth

    body = Box(
        body_width, clip_length, height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    tab = Pos(body_width / 2, 0, 0) * Box(
        tab_length, clip_length, base_thickness,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    # open top and open both ends: the channel is a slot, not a pocket
    channel = Pos(0, 0, base_thickness) * Box(
        channel_width, clip_length + 2, channel_depth + 1,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    screw_hole = Pos(body_width / 2 + tab_length / 2, 0, -1) * Cylinder(
        screw_hole_width / 2, base_thickness + 2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    solid = (body + tab) - channel - screw_hole

    if draft:
        return solid

    bed = solid.bounding_box().min.Z
    concave = {_key(e) for e in concave_edges(solid)}
    eps = 1e-6
    half_channel = channel_width / 2

    def exposed(edge):
        bb = edge.bounding_box()
        if _key(edge) in concave:
            return False
        # nothing that reaches into the cable channel: the floor stays one flat face
        # the full 8.4mm, the mouth stays exactly 8.4mm wide top to bottom, and the
        # open ends get no lead-in, which is the rule-3 case exactly
        if (
            bb.min.X <= half_channel + eps
            and bb.max.X >= -half_channel - eps
            and bb.max.Z >= base_thickness - eps
        ):
            return False
        # only the horizontal edges of the top surfaces. Leaving the vertical corners
        # sharp is what keeps three chamfers from ever meeting at one corner, and a
        # chamfer lying in the bed face buys nothing
        if bb.max.Z - bb.min.Z > eps or bb.min.Z < bed + eps:
            return False
        # the screw bore's rim: a 1mm cone through a 3mm tab is a feather edge, and
        # its toe lands 0.41mm under the top face
        if edge.geom_type == GeomType.CIRCLE:
            return False
        return True

    return polish(solid, solid.edges().filter_by(exposed), chamfer_size)
