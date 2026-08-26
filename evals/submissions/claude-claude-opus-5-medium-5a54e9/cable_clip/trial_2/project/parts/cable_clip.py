from nurb import *


@part
def cable_clip(
    bundle_diameter=measured("bundle_diameter"),
    channel_clearance=0.4,
    wall_thickness=2.4,
    base_thickness=3.0,
    clip_length=12.0,
    tab_length=10.0,
    tab_thickness=3.0,
    screw_hole_width=4.2,
    chamfer_size=1.2,
    draft=False,
):
    """A screw-down clip that traps a cable bundle in an open-top channel.

    bundle_diameter: how thick the cable bundle is across
    channel_clearance: how much wider than the bundle the channel is cut
    wall_thickness: how thick each of the two channel walls is
    base_thickness: how much material sits under the cable
    clip_length: how far the clip runs along the cable
    tab_length: how far the screw tab sticks out sideways
    tab_thickness: how thick the screw tab is
    screw_hole_width: diameter of the screw hole through the tab
    chamfer_size: size of the chamfer on the exposed outside edges
    """
    if bundle_diameter <= 0:
        reject("bundle_diameter has to be a positive width", param="bundle_diameter")
    if wall_thickness < 2.0:
        reject(
            f"wall_thickness {wall_thickness} is under the 2mm printable minimum: raise it to 2.0 or more",
            param="wall_thickness",
        )

    channel_width = bundle_diameter + channel_clearance
    channel_depth = bundle_diameter
    body_width = channel_width + 2 * wall_thickness
    height = base_thickness + channel_depth

    x_in = wall_thickness
    x_out = wall_thickness + channel_width

    body = Pos(body_width / 2, clip_length / 2, height / 2) * Box(
        body_width, clip_length, height
    )
    # open-top channel: cut through in Y and open through the top
    channel = Pos(
        (x_in + x_out) / 2,
        clip_length / 2,
        base_thickness + channel_depth,
    ) * Box(channel_width, clip_length + 2, 2 * channel_depth)

    tab = Pos(
        body_width + tab_length / 2, clip_length / 2, tab_thickness / 2
    ) * Box(tab_length, clip_length, tab_thickness)

    hole_x = body_width + tab_length / 2
    hole_y = clip_length / 2
    hole = Pos(hole_x, hole_y, tab_thickness / 2) * Cylinder(
        screw_hole_width / 2, tab_thickness + 2
    )

    solid = (body - channel + tab) - hole

    if draft:
        return solid

    eps = 1e-6
    bed = solid.bounding_box().min.Z
    hole_r = screw_hole_width / 2

    def key(edge):
        b = edge.bounding_box()
        return (
            round(b.min.X, 4),
            round(b.min.Y, 4),
            round(b.min.Z, 4),
            round(b.max.X, 4),
            round(b.max.Y, 4),
            round(b.max.Z, 4),
        )

    concave = {key(e) for e in concave_edges(solid)}

    def keep(edge):
        b = edge.bounding_box()
        if key(edge) in concave:
            return False
        # nothing lying in the bed face
        if b.max.Z <= bed + eps:
            return False
        # nothing inside the channel or at its mouth: it is mating geometry,
        # and the floor has to stay one flat face the full channel width
        if b.min.X >= x_in - eps and b.max.X <= x_out + eps and b.min.Z >= base_thickness - eps:
            return False
        # nor anything that merely touches an inner wall plane above the floor:
        # its chamfer would nick the corner of the mouth
        if b.min.Z >= base_thickness - eps and (
            b.min.X - eps <= x_in <= b.max.X + eps
            or b.min.X - eps <= x_out <= b.max.X + eps
        ):
            return False
        # nothing around the screw bore
        if (
            b.min.X >= hole_x - hole_r - eps
            and b.max.X <= hole_x + hole_r + eps
            and b.min.Y >= hole_y - hole_r - eps
            and b.max.Y <= hole_y + hole_r + eps
        ):
            return False
        return True

    return polish(solid, solid.edges().filter_by(keep), chamfer_size)
