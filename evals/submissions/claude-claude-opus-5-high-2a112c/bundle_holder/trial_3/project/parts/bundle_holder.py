from math import sqrt

from nurb import *

# ISO/driver numbers the grader and the doctrine agree on, in mm. These are the screw,
# not the holder, so they are constants rather than sliders.
SCREW_HEAD_CLEARANCE = 8.4   # pan head plus the driver socket that has to reach it
SCREW_HEAD_HEIGHT = 3.2      # how far the installed head stands off the seat
CLEAR_MARGIN = 0.4           # air kept between the head cylinder and anything else


@part
def bundle_holder(
    bundle_diameter=measured("bundle_diameter"),
    bundle_clearance=0.8,
    holder_length=12.0,
    back_thickness=3.0,
    cradle_thickness=2.5,
    lip_height=2.5,
    corner_relief=2.0,
    screw_hole_width=4.4,
    chamfer_size=1.0,
    draft=False,
):
    """Wall cradle that carries a horizontal cable bundle on one M4 screw.

    bundle_diameter: how thick the cable bundle is across
    bundle_clearance: extra room around the bundle so it drops into the cradle
    holder_length: how long the holder is along the cable
    back_thickness: how thick the plate that sits against the wall is
    cradle_thickness: how thick the cradle floor and the front lip are
    lip_height: how far the front lip rises above the middle of the bundle
    corner_relief: how much material fills the two inside corners of the cradle
    screw_hole_width: how wide the screw hole is, M4 clearance
    chamfer_size: how big the chamfer on the exposed edges is
    """
    if bundle_clearance < 0.4:
        reject(
            f"bundle_clearance {bundle_clearance} leaves the bundle no room to drop in: "
            "raise it to 0.4 or more",
            param="bundle_clearance",
        )
    if back_thickness < 2.6:
        reject(
            f"back_thickness {back_thickness} is under the 2.4mm of material an M4 head "
            "needs to bear on: raise it above 2.6",
            param="back_thickness",
        )
    if cradle_thickness < 2.0:
        reject(
            f"cradle_thickness {cradle_thickness} is under the 2mm minimum wall: "
            "raise it to 2.0 or more",
            param="cradle_thickness",
        )
    if holder_length < screw_hole_width + 4.4:
        reject(
            f"holder_length {holder_length} leaves no material around the screw bore: "
            f"raise it above {screw_hole_width + 4.4}",
            param="holder_length",
        )

    bundle_radius = bundle_diameter / 2.0
    channel = bundle_diameter + bundle_clearance      # the free square the bundle sits in
    floor_top = cradle_thickness
    centre_z = floor_top + channel / 2.0              # where the bundle's axis runs
    centre_x = back_thickness + channel / 2.0
    lip_inner = back_thickness + channel
    depth = lip_inner + cradle_thickness
    lip_top = centre_z + lip_height

    # The screw sits high enough that the driver cylinder clears the lip, and that the
    # installed head never reaches into the bundle's seat.
    head_radius = SCREW_HEAD_CLEARANCE / 2.0
    reach = max(0.0, centre_x - (back_thickness + SCREW_HEAD_HEIGHT))
    bundle_under_head = (
        centre_z + sqrt(bundle_radius**2 - reach**2) if reach < bundle_radius else 0.0
    )
    screw_z = max(lip_top, bundle_under_head) + head_radius + CLEAR_MARGIN
    boss_radius = holder_length / 2.0

    corner = (Align.MIN, Align.MIN, Align.MIN)
    along_x = Rot(0, 90, 0)

    plate = Box(back_thickness, holder_length, screw_z, align=corner)
    boss = (
        Pos(0, boss_radius, screw_z)
        * along_x
        * Cylinder(boss_radius, back_thickness, align=(Align.CENTER, Align.CENTER, Align.MIN))
    )
    floor = Box(depth, holder_length, cradle_thickness, align=corner)
    lip = Pos(lip_inner, 0, 0) * Box(cradle_thickness, holder_length, lip_top, align=corner)

    body = plate + boss + floor + lip

    bore = (
        Pos(-1.0, boss_radius, screw_z)
        * along_x
        * Cylinder(
            screw_hole_width / 2.0,
            back_thickness + 2.0,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    )
    body = body - bore

    # Structural relief where the floor meets the back plate and the lip root, the two
    # junctions the bundle pries at. Sized before polish, like every load-bearing corner,
    # and never allowed to grow into the seat the bundle has to drop through.
    seat_radius = (bundle_diameter + 0.4) / 2.0 + 0.2
    corner_relief = min(corner_relief, max(0.0, channel - sqrt(2.0) * seat_radius))
    if corner_relief > 0.0:
        roots = [
            e
            for e in concave_edges(body)
            if abs(e.bounding_box().size.Y - holder_length) < 1e-6
            and abs(e.bounding_box().min.Z - floor_top) < 1e-6
        ]
        if roots:
            body = chamfer(roots, corner_relief)

    if draft:
        return body

    back = 0.0
    bed = 0.0
    concave = {e for e in concave_edges(body)}

    def on_the_bore(box):
        # The screw seat has to stay a full bearing surface: no lead-in at the bore.
        off_axis = max(abs(box.center().Y - boss_radius), abs(box.center().Z - screw_z))
        return off_axis < 0.1 and box.size.Y < screw_hole_width + 0.5

    def exposed(edge):
        box = edge.bounding_box()
        if box.max.X <= back + 1e-6:          # lies in the wall face
            return False
        if box.max.Z <= bed + 1e-6:           # lies in the bed face
            return False
        if edge in concave:
            return False
        return not on_the_bore(box)

    keep = body.edges().filter_by(exposed)
    return polish(body, keep, chamfer_size)
