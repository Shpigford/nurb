"""A wall cradle that carries one horizontal cable bundle on a single M4 screw."""

from nurb import *


def _key(edge):
    """A position key, so an edge selected once can be recognised in another list."""
    c = edge.center()
    return (round(c.X, 4), round(c.Y, 4), round(c.Z, 4))


@part
def bundle_holder(
    bundle_diameter=8.0,
    bundle_clearance=0.6,
    holder_length=12.4,
    back_thickness=3.0,
    floor_thickness=2.4,
    lip_thickness=2.4,
    cradle_relief=2.0,
    screw_hole_width=4.4,
    screw_head_width=8.4,
    screw_wall=4.0,
    chamfer_size=1.0,
    draft=False,
):
    """A wall cradle for a horizontal cable bundle, held by one M4 pan-head screw.

    bundle_diameter: how thick the cable bundle is across
    bundle_clearance: extra room around the bundle so it threads through easily
    holder_length: how far the holder reaches along the bundle
    back_thickness: the plate that sits flat against the wall
    floor_thickness: the material the bundle rests on
    lip_thickness: the front wall that stops the bundle coming off the wall
    cradle_relief: the 45 degree corner fills the bundle nests into
    screw_hole_width: clearance hole for the M4 screw
    screw_head_width: room the screw head and screwdriver need in front of the plate
    screw_wall: material around the screw hole
    chamfer_size: the chamfer taken off exposed edges
    """
    channel = bundle_diameter + bundle_clearance
    tab_width = screw_hole_width + 2.0 * screw_wall
    if holder_length < tab_width:
        reject(
            f"holder_length {holder_length} leaves no material around the screw: "
            f"raise it above {tab_width}",
            param="holder_length",
        )
    if cradle_relief < 0:
        reject(
            f"cradle_relief {cradle_relief} is negative: it is a corner fill, not a cut",
            param="cradle_relief",
        )
    if back_thickness < 2.6:
        reject(
            f"back_thickness {back_thickness} is too shallow for the screw to seat "
            "squarely: raise it above 2.6",
            param="back_thickness",
        )

    x_in = back_thickness                      # inner face of the channel
    x_out = x_in + channel                     # inner face of the lip
    x_max = x_out + lip_thickness              # front of the part
    z_floor = floor_thickness                  # the bundle rests here
    lip_top = z_floor + channel                # lip wraps the full height of the bundle

    # The bundle is only held while it cannot drop a millimetre, so the highest it can
    # ever sit is a millimetre of lift above a bundle resting on the floor. The screw
    # head and its driver clear that, and clear the lip, with room to spare.
    bundle_reach = z_floor + 1.0 + bundle_diameter
    screw_z = max(lip_top, bundle_reach) + screw_head_width / 2.0 + 0.8

    # Body: the channel block, the wall plate behind it, and a domed tab for the screw.
    solid = Box(x_max, holder_length, lip_top, align=(Align.MIN, Align.CENTER, Align.MIN))
    solid += Box(
        back_thickness, holder_length, screw_z, align=(Align.MIN, Align.CENTER, Align.MIN)
    )
    solid += (
        Pos(back_thickness / 2.0, 0, screw_z)
        * Rot(0, 90, 0)
        * Cylinder(holder_length / 2.0, back_thickness)
    )

    # The channel, open at the top so the bundle drops in, with 45 degree reliefs at the
    # two inside corners: they cradle a round bundle and take the stress off the corner.
    r = min(cradle_relief, channel / 4.0)   # a small bundle gets proportionally smaller
    profile = [
        (x_in, z_floor + r),
        (x_in + r, z_floor),
        (x_out - r, z_floor),
        (x_out, z_floor + r),
        (x_out, lip_top + 1.0),
        (x_in, lip_top + 1.0),
    ]
    solid -= extrude(
        Plane.XZ * Polygon(*profile, align=None), amount=holder_length, both=True
    )

    # Clearance bore for the screw, mouth on the wall face, head seating on the front of
    # the plate the way a pan head does.
    solid -= (
        Pos(back_thickness / 2.0, 0, screw_z)
        * Rot(0, 90, 0)
        * Cylinder(screw_hole_width / 2.0, back_thickness * 4.0)
    )

    if draft:
        return solid

    box = solid.bounding_box()
    bed, back = box.min.Z, box.min.X
    tol = 1e-6
    inside = {_key(e) for e in concave_edges(solid)}
    # The screw bore is mating geometry: a chamfer at its mouth eats the depth the head
    # needs to seat squarely, so nothing within reach of the bore is polished.
    reach = screw_hole_width / 2.0 + 1.5 * chamfer_size

    def at_the_bore(e):
        b = e.bounding_box()
        return (
            max(abs(b.min.Y), abs(b.max.Y)) < reach
            and max(abs(b.min.Z - screw_z), abs(b.max.Z - screw_z)) < reach
        )

    keep = solid.edges().filter_by(
        lambda e: not (
            e.bounding_box().max.Z < bed + tol      # lies in the bed face
            or e.bounding_box().max.X < back + tol  # lies in the wall face
            or _key(e) in inside                    # concave, never polished
            or at_the_bore(e)                       # mating geometry, left sharp
        )
    )
    return polish(solid, keep, chamfer_size)
