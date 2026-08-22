from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Wall clip that holds a taped cable bundle running along the wall.

    bundle_diameter: across-measurement of the taped cable bundle
    """
    if bundle_diameter < 3.0:
        reject(
            f"bundle_diameter {bundle_diameter} is under 3mm: raise it to at least 3",
            param="bundle_diameter",
        )

    # 0.4mm of diametral clearance so an 8.0 bundle sits in an 8.4 seat.
    seat = bundle_diameter + 0.4
    back = 3.0
    floor = 2.2
    wall = 2.2
    length = 14.0

    hole = 4.4
    head_dia = 8.4
    head_keep = 1.5

    front_x = back + seat
    overall_x = front_x + wall
    cradle_top = floor + seat

    # Head-and-driver cylinder (8.4) must leave the part in +X without
    # clipping the cradle, so the bore sits above the channel plus the head.
    screw_z = cradle_top + head_dia / 2 + head_keep
    plate_top = screw_z + hole / 2 + 4.0

    corner = (Align.MIN, Align.CENTER, Align.MIN)
    back_plate = Box(back, length, plate_top, align=corner)
    floor_slab = Box(overall_x, length, floor, align=corner)
    front_wall = Pos(front_x, 0, 0) * Box(wall, length, cradle_top, align=corner)
    body = back_plate + floor_slab + front_wall

    bore = Pos(back / 2, 0, screw_z) * Cylinder(hole / 2, back + 4, rotation=(0, 90, 0))
    body = body - bore

    if draft:
        return body

    bed = body.bounding_box().min.Z
    xmin = body.bounding_box().min.X
    banned = set(concave_edges(body))

    def exposed(edge):
        bb = edge.bounding_box()
        if edge in banned:
            return False
        if bb.max.Z <= bed + 1e-3:
            return False
        if bb.max.X <= xmin + 1e-3:
            return False
        if edge.geom_type == GeomType.CIRCLE:
            return False
        # Channel faces are the bundle seat: leave those edges sharp.
        mid = edge.center()
        in_channel_x = back - 1e-3 <= mid.X <= front_x + 1e-3
        in_channel_z = floor - 1e-3 <= mid.Z <= cradle_top + 1e-3
        if in_channel_x and in_channel_z:
            return False
        # Three 1mm chamfers cannot meet on the plate's or front wall's top corners.
        if mid.Z >= plate_top - 1e-3 and mid.X <= back + 1e-3:
            return False
        if mid.Z >= cradle_top - 1e-3 and mid.X >= front_x - 1e-3:
            return False
        return True

    keep = body.edges().filter_by(exposed)
    return polish(body, keep, 1.0)
