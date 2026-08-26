from nurb import *


@part
def bundle_holder(
    bundle_diameter=measured("bundle_diameter"),
    bundle_clearance=0.4,
    wall=3.0,
    back_thickness=3.0,
    back_width=14.0,
    cradle_width=8.0,
    screw_hole_width=4.4,
    screw_head_width=8.4,
    chamfer_size=1.2,
    draft=False,
):
    """A wall hook that cradles a horizontal cable bundle, held by one M4 screw.

    bundle_diameter: how thick the cable bundle is
    bundle_clearance: extra room around the bundle so it slides through
    wall: thickness of the cradle floor and its outer lip
    back_thickness: thickness of the flat plate that sits against the wall
    back_width: how far the back plate runs along the bundle
    cradle_width: how much of that width the cradle band actually wraps
    screw_hole_width: clearance hole for the mounting screw (M4 medium fit)
    screw_head_width: room the screw head and driver need in front of the plate
    chamfer_size: size of the chamfer on every exposed edge
    """
    if bundle_diameter <= 0.0:
        reject("bundle_diameter has to be a real measurement", param="bundle_diameter")
    if cradle_width < back_width / 3.0:
        reject(
            f"cradle_width {cradle_width} holds less than a third of back_width "
            f"{back_width}: raise it above {back_width / 3.0:.1f}",
            param="cradle_width",
        )

    opening = bundle_diameter + bundle_clearance
    depth = back_thickness + opening + wall

    # The bundle can never rest higher than 1mm off the floor and still be
    # blocked downward, so the lip only has to reach a little past that, and the
    # screw only has to clear that highest resting bundle.
    highest_seat = wall + bundle_diameter / 2.0 + 1.0
    lip_top = highest_seat + 2.0
    screw_z = highest_seat + bundle_diameter / 2.0 + screw_head_width / 2.0 + 0.8
    back_height = screw_z + screw_head_width / 2.0 + chamfer_size + 1.0

    back = Pos(back_thickness / 2.0, 0, back_height / 2.0) * Box(
        back_thickness, back_width, back_height
    )
    arm = depth - back_thickness
    floor = Pos(back_thickness + arm / 2.0, 0, wall / 2.0) * Box(arm, cradle_width, wall)
    lip = Pos(depth - wall / 2.0, 0, lip_top / 2.0) * Box(wall, cradle_width, lip_top)

    body = back + floor + lip

    bore = (
        Pos(back_thickness / 2.0, 0, screw_z)
        * Rot(0, 90, 0)
        * Cylinder(screw_hole_width / 2.0, back_thickness * 3.0)
    )
    body = body - bore

    if draft:
        return body

    box = body.bounding_box()
    bed, wall_face = box.min.Z, box.min.X
    inside = concave_edges(body)

    def exposed(e):
        eb = e.bounding_box()
        if eb.max.Z <= bed + 1e-6:  # lies in the bed face
            return False
        if eb.max.X <= wall_face + 1e-6:  # lies in the back face
            return False
        return not any(e.is_same(c) for c in inside)

    keep = [e for e in body.edges().filter_by(GeomType.LINE) if exposed(e)]
    return polish(body, keep, chamfer_size)
