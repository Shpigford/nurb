from nurb import *

# An M4 pan head plus the driver socket that turns it: 8.4mm across, and the
# screw cannot go in unless that cylinder is clear from the seat outward.
HEAD_CLEARANCE = 8.4


@part
def bundle_holder(
    bundle_diameter=measured("bundle_diameter"),
    holder_length=11.0,
    bundle_clearance=0.6,
    back_thickness=3.0,
    floor_thickness=2.5,
    lip_thickness=3.0,
    screw_hole_width=4.4,
    draft=False,
):
    """A wall cradle the cable bundle drops into from above.

    bundle_diameter: how thick the cable bundle is where it runs along the wall
    holder_length: how much of the bundle the cradle holds, measured along the wall
    bundle_clearance: slack around the bundle so it drops in without being forced
    back_thickness: the plate against the wall, and how far the screw runs through it
    floor_thickness: the shelf the bundle rests on
    lip_thickness: the front wall that stops the bundle falling away from the wall
    screw_hole_width: clearance hole for the M4 pan-head screw
    """
    radius = bundle_diameter / 2.0
    span = bundle_diameter + bundle_clearance
    depth = back_thickness + span + lip_thickness
    head_radius = HEAD_CLEARANCE / 2.0
    facet = 1.0  # the polish chamfer, sized here because the plate has to clear it

    # The lip catches the bundle well past its widest point, so a tug on the cable
    # cannot roll it out forward. It never blocks loading: the bundle drops in from
    # above, down the full-width slot between the plate and the lip.
    lip_height = floor_thickness + radius + 1.5

    # The bundle rests on the floor, but the floor still catches it a millimetre
    # higher, so the screw clears the highest bundle it has to coexist with: head
    # and bundle stacked and just touching, plus a little air.
    screw_z = floor_thickness + radius + 1.0 + radius + head_radius + 0.4
    # The head seats on a full ring of material, so the plate carries on above it,
    # far enough that the top chamfer does not eat into the ring the head lands on.
    height = screw_z + head_radius + facet + 0.4

    to_min = (Align.MIN, Align.CENTER, Align.MIN)
    back = Box(back_thickness, holder_length, height, align=to_min)
    floor = Box(depth, holder_length, floor_thickness, align=to_min)
    lip = Pos(depth - lip_thickness, 0, 0) * Box(
        lip_thickness, holder_length, lip_height, align=to_min
    )
    body = back + floor + lip

    bore = (
        Pos(back_thickness / 2.0, 0, screw_z)
        * Rot(0, 90, 0)
        * Cylinder(screw_hole_width / 2.0, back_thickness + 2.0)
    )
    body = body - bore

    if draft:
        return body

    eps = 1e-6
    mouth = back_thickness + span
    hollows = [e.center() for e in concave_edges(body)]

    def keep(e):
        bb = e.bounding_box()
        mid = e.center()
        if any((mid - c).length < eps for c in hollows):
            return False  # never polish an inside corner
        if bb.max.X < eps or bb.max.Z < eps:
            return False  # lies in the wall face or in the bed face
        near_axis = (mid.Y**2 + (mid.Z - screw_z) ** 2) ** 0.5
        if abs(mid.X - back_thickness) < 0.5 and near_axis < screw_hole_width:
            return False  # the screw seat, which the head has to land flat on
        if abs(bb.min.X - mouth) < eps and abs(bb.max.X - mouth) < eps:
            return False  # the channel's front wall: fit geometry, and what holds
        if (
            abs(bb.min.Z - floor_thickness) < eps
            and abs(bb.max.Z - floor_thickness) < eps
            and bb.min.X > back_thickness - eps
            and bb.max.X < mouth + eps
        ):
            return False  # the channel floor, same reason
        level = abs(bb.max.Z - bb.min.Z) < eps
        across = abs(bb.max.Y - bb.min.Y) < eps and bb.max.X - bb.min.X > eps
        if level and across:
            return False  # a top face's side edge: three chamfers on one corner leave a sliver
        return True

    return polish(body, body.edges().filter_by(keep), facet)
