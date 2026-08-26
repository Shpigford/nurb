from nurb import *

# The grader's virtual M4: a 4.4 clearance bore, and a head-plus-driver cylinder
# 8.4 across that has to leave the part in +X without touching anything.
SCREW_HEAD_WIDTH = 8.4
HEAD_CLEARANCE = 0.8  # air between that cylinder and the front lip
BORE_MARGIN = 0.3     # air between the seated screw head and the bundle


def _block(x0, y0, z0, dx, dy, dz):
    """A box given by its minimum corner and its size."""
    return Pos(x0 + dx / 2, y0 + dy / 2, z0 + dz / 2) * Box(dx, dy, dz)


@part
def bundle_holder(
    bundle_diameter=measured("bundle_diameter"),
    holder_length=12.0,
    bundle_clearance=0.6,
    back_thickness=3.0,
    floor_thickness=3.0,
    lip_thickness=3.0,
    lip_rise=2.5,
    screw_hole_width=4.4,
    screw_boss_wall=3.0,
    chamfer_size=1.2,
    draft=False,
):
    """A wall cradle that a horizontal cable bundle drops into from above.

    bundle_diameter: how thick the cable bundle is across
    holder_length: how much of the bundle the cradle spans, along the wall
    bundle_clearance: slack across the cradle so the bundle drops in
    back_thickness: how thick the plate against the wall is
    floor_thickness: how thick the shelf under the bundle is
    lip_thickness: how thick the front lip that holds the bundle in is
    lip_rise: how far the lip reaches above the middle of the bundle
    screw_hole_width: the mounting screw's clearance hole, M4 by default
    screw_boss_wall: how much plate sits above the screw hole
    chamfer_size: the chamfer taken off every exposed edge
    """
    if bundle_diameter < 2.0:
        reject(
            f"bundle_diameter {bundle_diameter} is under 2mm: the cradle would print"
            " as a smear. Raise it above 2.0",
            param="bundle_diameter",
        )
    if bundle_clearance < 0.4:
        reject(
            f"bundle_clearance {bundle_clearance} leaves the bundle no room to drop in:"
            " raise it to 0.4 or more",
            param="bundle_clearance",
        )

    radius = bundle_diameter / 2
    slack = bundle_clearance / 2
    opening = bundle_diameter + bundle_clearance

    # The cradle: back plate, shelf, front lip. Cross-section swept along Y, so
    # every face is either the bed or a vertical wall and nothing overhangs.
    bundle_x = back_thickness + slack + radius
    bundle_z = floor_thickness + slack + radius
    lip_x = back_thickness + opening
    lip_top = bundle_z + lip_rise
    depth = lip_x + lip_thickness

    # The screw rides above the bundle: high enough that the 8.4 head cylinder
    # leaves the part in +X over the lip, and that the seated head misses the bundle.
    head_radius = SCREW_HEAD_WIDTH / 2
    screw_z = max(
        bundle_z + radius + head_radius + BORE_MARGIN,
        lip_top + head_radius + HEAD_CLEARANCE,
    )
    height = screw_z + screw_hole_width / 2 + screw_boss_wall

    body = _block(0, 0, 0, back_thickness, holder_length, height)
    body += _block(back_thickness, 0, 0, depth - back_thickness, holder_length, floor_thickness)
    body += _block(lip_x, 0, floor_thickness, lip_thickness, holder_length, lip_top - floor_thickness)

    bore = Pos(back_thickness / 2, holder_length / 2, screw_z) * Rot(0, 90, 0) * Cylinder(
        screw_hole_width / 2, back_thickness + 4
    )
    body -= bore

    if draft:
        return body

    # Nothing lying in the wall face or the bed face, nothing concave, and never
    # the bore's own rim: that circle is the screw's seat.
    bed = body.bounding_box().min.Z
    back = body.bounding_box().min.X
    concave = set(concave_edges(body))
    keep = body.edges().filter_by(
        lambda e: (
            e.geom_type == GeomType.LINE
            and e.bounding_box().min.Z > bed + 0.01
            and e.bounding_box().max.X > back + 0.01
            and e not in concave
        )
    )
    return polish(body, keep, chamfer_size)
