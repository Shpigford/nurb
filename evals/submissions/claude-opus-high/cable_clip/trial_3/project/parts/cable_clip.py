from nurb import *

CHAMFER = 1.0
TOL = 1e-6


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
    """A screw-down clip: the bundle drops into an open-top channel, one screw holds it.

    bundle_diameter: how thick the cable bundle is across
    cable_clearance: how much wider than the bundle the channel is cut
    wall_thickness: how thick each channel wall is
    base_thickness: how thick the floor under the cable is, and the mounting tab
    clip_length: how far the clip runs along the cable
    tab_length: how far the mounting tab sticks out past the wall
    screw_hole_width: how wide the screw hole through the tab is
    """
    channel_width = bundle_diameter + cable_clearance
    channel_depth = bundle_diameter
    body_width = channel_width + 2 * wall_thickness
    body_height = base_thickness + channel_depth

    corner = (Align.MIN, Align.MIN, Align.MIN)

    body = Box(body_width, clip_length, body_height, align=corner)
    # Open at the top and at both ends: the cable lies along Y through the whole part,
    # and the cut runs past both end faces so the boolean has no coincident faces.
    channel = Box(channel_width, clip_length + 2, channel_depth + 1, align=corner).translate(
        (wall_thickness, -1, base_thickness)
    )
    tab = Box(tab_length, clip_length, base_thickness, align=corner).translate((body_width, 0, 0))

    screw_x = body_width + tab_length / 2
    screw_y = clip_length / 2
    screw_radius = screw_hole_width / 2
    screw = Cylinder(
        screw_radius,
        base_thickness + 2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).translate((screw_x, screw_y, -1))

    solid = (body - channel) + tab - screw

    if draft:
        return solid

    bed = solid.bounding_box().min.Z
    concave = set(concave_edges(solid))

    def keepable(e):
        bb = e.bounding_box()
        if e in concave:
            return False
        # Nothing lying in the bed face: a chamfer there buys nothing and slivers.
        # A vertical corner that merely ends on the bed is still fair game.
        if bb.max.Z <= bed + TOL:
            return False
        # Nothing on the channel. The bundle beds against the floor and both walls, so
        # they stay square: floor one flat face the full width, walls full height.
        if (
            bb.min.X >= wall_thickness - TOL
            and bb.max.X <= wall_thickness + channel_width + TOL
            and bb.min.Z >= base_thickness - TOL
        ):
            return False
        # Nothing on the screw hole: a lead-in there is fit geometry, not polish.
        if (
            max(abs(bb.min.X - screw_x), abs(bb.max.X - screw_x)) <= screw_radius + TOL
            and max(abs(bb.min.Y - screw_y), abs(bb.max.Y - screw_y)) <= screw_radius + TOL
        ):
            return False
        # Nothing running across the part at either end. Across the wall tops such an
        # edge is the channel mouth, where a lead-in is forbidden outright; across the
        # tab it would land a third chamfer on corners that already have two, and three
        # chamfers meeting leave a facet under a square millimetre.
        if bb.max.Y - bb.min.Y <= TOL and bb.max.Z - bb.min.Z <= TOL:
            return False
        return True

    keep = solid.edges().filter_by(keepable)
    return polish(solid, keep, CHAMFER)
