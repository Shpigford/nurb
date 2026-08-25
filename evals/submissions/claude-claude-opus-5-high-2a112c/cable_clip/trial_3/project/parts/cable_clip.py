from nurb import *


@part
def cable_clip(
    bundle_diameter=measured("bundle_diameter"),
    bundle_clearance=0.4,
    wall_thickness=2.4,
    base_thickness=3.0,
    clip_length=12.0,
    tab_length=10.0,
    screw_hole_width=4.2,
    chamfer_size=1.2,
    draft=False,
):
    """A screw-down clip that traps a cable bundle in an open-top channel.

    bundle_diameter: how thick the cable bundle is across
    bundle_clearance: extra channel width so the bundle drops in without forcing
    wall_thickness: how thick each channel wall is
    base_thickness: how much material sits under the cable, and how thick the tab is
    clip_length: how far the clip runs along the cable
    tab_length: how far the screw tab reaches out sideways
    screw_hole_width: diameter of the screw hole through the tab
    chamfer_size: how big the finishing chamfers on the outside edges are
    """
    if bundle_diameter <= 0:
        reject(
            "bundle_diameter has to be a real cable width; measure the bundle "
            "and raise it above 0",
            param="bundle_diameter",
        )

    channel_width = bundle_diameter + bundle_clearance
    channel_depth = bundle_diameter
    height = base_thickness + channel_depth
    block_width = channel_width + 2 * wall_thickness

    if screw_hole_width + 2 * 2.0 > tab_length:
        reject(
            f"screw_hole_width {screw_hole_width} leaves under 2mm of tab around the "
            f"bore; raise tab_length above {screw_hole_width + 4.0}",
            param="tab_length",
        )

    # The channel block: walls either side of the cable, base underneath.
    body = Pos(block_width / 2, clip_length / 2, height / 2) * Box(
        block_width, clip_length, height
    )

    # Open-top channel, cut clean through both ends and out of the top so the
    # floor and the two inner walls each stay a single flat face.
    cut = Pos(
        wall_thickness + channel_width / 2,
        clip_length / 2,
        base_thickness + (channel_depth + chamfer_size) / 2,
    ) * Box(channel_width, clip_length + 2 * chamfer_size, channel_depth + chamfer_size)
    body = body - cut

    # Mounting tab, flush with the bottom, off the outside of the +X wall.
    tab_center_x = block_width + tab_length / 2
    body = body + Pos(tab_center_x, clip_length / 2, base_thickness / 2) * Box(
        tab_length, clip_length, base_thickness
    )

    # Screw hole, vertical and centred in the tab, so it prints support-free.
    body = body - Pos(tab_center_x, clip_length / 2, base_thickness / 2) * Cylinder(
        screw_hole_width / 2, base_thickness + 2 * chamfer_size
    )

    if draft:
        return body

    # Polish: outside edges only. The bed face, the concave junctions and every
    # edge bounding the channel interior stay sharp.
    bed = body.bounding_box().min.Z
    channel_x0 = wall_thickness
    channel_x1 = wall_thickness + channel_width
    tol = 1e-6

    concave = {
        (round(e.center().X, 4), round(e.center().Y, 4), round(e.center().Z, 4))
        for e in concave_edges(body)
    }

    def keeps(edge):
        box = edge.bounding_box()
        # Nothing lying in the bed face: a bottom chamfer buys nothing and prints badly.
        if box.max.Z <= bed + tol:
            return False
        # Never a chamfer on an inside corner.
        c = edge.center()
        if (round(c.X, 4), round(c.Y, 4), round(c.Z, 4)) in concave:
            return False
        # Nothing on the screw bore: a lead-in on a 3mm tab eats a third of the
        # bearing depth, and the rim is where the screw head has to seat flat.
        if (
            box.min.X >= tab_center_x - screw_hole_width / 2 - tol
            and box.max.X <= tab_center_x + screw_hole_width / 2 + tol
        ):
            return False
        # Nothing that reaches the channel. The floor, the two inner walls and
        # their end corners are the fit, and a chamfer landing anywhere on them
        # would round the square section the bundle sits in.
        if (
            box.max.X >= channel_x0 - tol
            and box.min.X <= channel_x1 + tol
            and box.max.Z >= base_thickness - tol
        ):
            return False
        return True

    return polish(body, body.edges().filter_by(keeps), chamfer_size)
