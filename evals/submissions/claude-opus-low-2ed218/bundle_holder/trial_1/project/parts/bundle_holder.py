from nurb import *

SCREW_CLEAR = 4.4   # ISO 273 medium clearance for M4
HEAD_CLEAR = 8.4    # pan head plus driver socket


@part
def bundle_holder(
    bundle_diameter=measured("bundle_diameter"),
    bundle_clearance=0.6,
    holder_length=12.0,
    back_thickness=2.6,
    wall_thickness=2.0,
    screw_headroom=0.8,
    draft=False,
):
    """A wall hook that cradles a horizontal cable bundle, screwed on with one M4.

    bundle_diameter: how thick the cable bundle is across
    bundle_clearance: extra room around the bundle so it drops in easily
    holder_length: how far the holder runs along the bundle
    back_thickness: how thick the flat plate against the wall is
    wall_thickness: how thick the floor and the front lip are
    screw_headroom: gap between the front lip and the screw driver's swing
    """
    if bundle_diameter < 2.0:
        reject(
            f"bundle_diameter {bundle_diameter} is smaller than anything worth "
            "cradling: raise it above 2.0",
            param="bundle_diameter",
        )
    if bundle_clearance < 0.4:
        reject(
            f"bundle_clearance {bundle_clearance} leaves the bundle jammed: "
            "raise it to 0.4 or more",
            param="bundle_clearance",
        )

    cradle = bundle_diameter + bundle_clearance      # clear opening for the bundle
    front_x = back_thickness + cradle                # where the front lip starts
    total_x = front_x + wall_thickness
    lip_top = wall_thickness + cradle * 0.75         # front lip stops above centre

    # The screw sits above both the front lip and the bundle itself, so the driver
    # never fouls the lip and the installed screw never crowds the cable.
    screw_z = (
        max(lip_top, wall_thickness + cradle) + HEAD_CLEAR / 2 + screw_headroom
    )
    plate_top = screw_z + HEAD_CLEAR / 2 + screw_headroom

    floor = Pos(0, 0, 0) * Box(
        total_x, holder_length, wall_thickness,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    back = Box(
        back_thickness, holder_length, plate_top,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    lip = Pos(front_x, 0, 0) * Box(
        wall_thickness, holder_length, lip_top,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    body = floor + back + lip

    bore = Pos(-1.0, 0, screw_z) * Rot(0, 90, 0) * Cylinder(
        SCREW_CLEAR / 2, back_thickness + 2.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    body = body - bore

    if draft:
        return body
    bed = body.bounding_box().min.Z
    concave = set(concave_edges(body))
    keep = [
        e
        for e in body.edges()
        if e.bounding_box().min.Z > bed
        and e not in concave
        and e.bounding_box().min.X > 0.01  # leave the wall face alone
        and e.geom_type != GeomType.CIRCLE  # the bore mouths stay square
        and not (
            e.bounding_box().min.X > back_thickness
            and abs(e.bounding_box().max.Z - lip_top) < 0.01
        )  # the lip is only two walls wide: chamfering its rim leaves slivers
    ]
    return polish(body, keep, 1.0)
