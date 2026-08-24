from nurb import *

BORE_DIA = 4.5  # ISO 273 medium clearance for M4
HEAD_DIA = 8.4  # M4 pan head plus driver clearance
HEAD_HEIGHT = 3.2  # how far the seated head stands proud of the plate


@part
def bundle_holder(
    bundle_diameter=measured("bundle_diameter"),
    holder_length=12.0,
    wall_thickness=2.8,
    draft=False,
):
    """Wall-mounted hook for a horizontal cable bundle, held by one M4 screw.

    bundle_diameter: how thick the cable bundle is across
    holder_length: how far the holder runs along the wall
    wall_thickness: how thick the back plate, floor and front lip are
    """
    if bundle_diameter < 2.0:
        reject(
            "bundle_diameter under 2 prints the channel shut: raise it to 2 or more",
            param="bundle_diameter",
        )
    if holder_length < 10.0:
        reject(
            "holder_length under 10 cannot grip the bundle: raise it to 10 or more",
            param="holder_length",
        )
    if wall_thickness < 2.4:
        reject(
            "wall_thickness under 2.4 leaves the M4 head nothing to seat against: "
            "raise it to 2.4 or more",
            param="wall_thickness",
        )

    r = bundle_diameter / 2.0
    plate = wall_thickness
    floor_top = wall_thickness
    bundle_z = floor_top + 0.6 + r  # bundle rests 0.6 above the floor
    lip_top = bundle_z + 2.4  # front lip reaches past the bundle's equator
    bundle_x = plate + HEAD_HEIGHT + 0.3 + r  # bundle sits clear of the seated head
    lip_inner = bundle_x + r + 0.6  # escape gap under the 1.0 that would free it
    depth = lip_inner + wall_thickness
    screw_z = lip_top + HEAD_DIA / 2 + 0.6  # driver corridor clears the lip
    height = screw_z + HEAD_DIA / 2 + 1.6  # top chamfer stays clear of the head's seat

    corner = (Align.MIN, Align.MIN, Align.MIN)
    body = (
        Box(plate, holder_length, height, align=corner)
        + Box(depth, holder_length, floor_top, align=corner)
        + Pos(lip_inner, 0, 0)
        * Box(depth - lip_inner, holder_length, lip_top, align=corner)
    )
    bore = (
        Pos(-1.0, holder_length / 2, screw_z)
        * Rot(Y=90)
        * Cylinder(
            BORE_DIA / 2,
            plate + 2.0,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    )
    body = body - bore

    if draft:
        return body

    concave = concave_edges(body)
    bed = body.bounding_box().min.Z

    def wants_chamfer(edge):
        bb = edge.bounding_box()
        if bb.max.Z <= bed + 1e-6:  # lies in the bed face
            return False
        if bb.max.X <= 1e-6:  # lies in the back face, against the wall
            return False
        if bb.max.X <= plate + 1e-6 and abs(bb.center().Z - screw_z) < HEAD_DIA / 2:
            return False  # the screw bore stays fit-critical
        return edge not in concave

    keep = body.edges().filter_by(wants_chamfer)
    # 1.2 rather than 1.0: the corner triangles three chamfers leave then sit
    # above the 1mm2 sliver floor instead of just under it.
    return polish(body, keep, 1.2)
