from nurb import *


@part
def cable_clip(
    bundle_diameter=8.0,
    cable_clearance=0.4,
    wall_thickness=2.4,
    base_thickness=3.0,
    clip_length=12.0,
    tab_length=10.0,
    screw_hole_width=4.2,
    draft=False,
):
    """A screw-down clip: the cable drops into an open-top channel and a screw
    through the side tab holds it to the surface.

    bundle_diameter: how thick the cable bundle is across
    cable_clearance: extra width in the channel over the bundle, so it drops in
    wall_thickness: how thick each channel wall is
    base_thickness: how much material sits under the cable
    clip_length: how far the clip runs along the cable
    tab_length: how far the mounting tab sticks out sideways
    screw_hole_width: diameter of the screw hole through the tab
    """
    if bundle_diameter < 2.0:
        reject("bundle_diameter under 2mm leaves no channel to print", param="bundle_diameter")

    channel_width = bundle_diameter + cable_clearance
    channel_depth = bundle_diameter
    body_width = channel_width + 2 * wall_thickness
    height = base_thickness + channel_depth

    body = Pos(body_width / 2, clip_length / 2, height / 2) * Box(body_width, clip_length, height)

    channel = Pos(
        body_width / 2,
        clip_length / 2,
        base_thickness + channel_depth / 2,
    ) * Box(channel_width, clip_length, channel_depth)
    body -= channel

    tab = Pos(
        body_width + tab_length / 2,
        clip_length / 2,
        base_thickness / 2,
    ) * Box(tab_length, clip_length, base_thickness)
    body += tab

    hole_center = body_width + tab_length / 2
    body -= Pos(hole_center, clip_length / 2, base_thickness / 2) * Cylinder(
        screw_hole_width / 2, base_thickness
    )

    if draft:
        return body

    bed = body.bounding_box().min.Z
    concave = set(concave_edges(body))
    channel_x0 = wall_thickness
    channel_x1 = wall_thickness + channel_width

    def keep(e):
        bb = e.bounding_box()
        if bb.max.Z <= bed + 1e-6:
            return False
        if e in concave:
            return False
        # nothing inside the channel: the floor stays flat and the mouth keeps no lead-in
        if bb.min.X > channel_x0 - 1e-6 and bb.max.X < channel_x1 + 1e-6 and bb.max.Z > base_thickness + 1e-6:
            return False
        # the screw bore rim: a chamfer there thins the 3mm tab
        if (bb.min.X > hole_center - screw_hole_width and bb.max.X < hole_center + screw_hole_width
                and bb.min.Y > clip_length / 2 - screw_hole_width and bb.max.Y < clip_length / 2 + screw_hole_width):
            return False
        # vertical corners stay sharp: chamfering them too would leave three
        # chamfers colliding in a sliver facet at every top corner
        if bb.max.X - bb.min.X < 1e-6 and bb.max.Y - bb.min.Y < 1e-6:
            return False
        return True

    return polish(body, body.edges().filter_by(keep), 1.0)
