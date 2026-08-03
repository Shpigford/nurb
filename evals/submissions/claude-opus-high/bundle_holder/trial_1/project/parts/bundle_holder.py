from nurb import *


def _block(x0, y0, z0, dx, dy, dz):
    """A box given by its minimum corner and its size, so the profile reads as coordinates."""
    return Pos(x0 + dx / 2, y0 + dy / 2, z0 + dz / 2) * Box(dx, dy, dz)


@part
def bundle_holder(
    bundle_diameter=measured("bundle_diameter"),
    bundle_slack=0.6,
    holder_length=12.0,
    back_thickness=3.0,
    floor_thickness=2.5,
    lip_thickness=2.4,
    lip_rise=2.0,
    screw_hole_width=4.5,
    screw_head_width=8.4,
    draft=False,
):
    """A wall cradle that traps a horizontal cable bundle in a C, on one M4 screw.

    bundle_diameter: how thick the cable bundle is across
    bundle_slack: how much wider than the bundle the cradle is, so the bundle drops in
    holder_length: how much of the run the cradle grips, measured along the bundle
    back_thickness: how thick the plate against the wall is
    floor_thickness: how thick the shelf under the bundle is
    lip_thickness: how thick the front lip that stops the bundle falling out is
    lip_rise: how far the lip stands above the middle of the bundle
    screw_hole_width: how wide the screw hole is, an M4 clearance hole
    screw_head_width: how much room the screw head and driver need above the plate
    """
    channel = bundle_diameter + bundle_slack
    pocket_front = back_thickness + channel
    total_depth = pocket_front + lip_thickness

    bundle_z = floor_thickness + bundle_slack / 2 + bundle_diameter / 2
    lip_top = bundle_z + lip_rise
    # The head and driver have to swing clear over the lip, so the screw sits a head's
    # radius above the top of the bundle, and the plate carries a full seat around it.
    screw_z = bundle_z + bundle_diameter / 2 + screw_head_width / 2 + 0.6
    height = screw_z + screw_head_width / 2 + 1.6

    body = (
        _block(0, 0, 0, back_thickness, holder_length, height)
        + _block(0, 0, 0, total_depth, holder_length, floor_thickness)
        + _block(pocket_front, 0, 0, lip_thickness, holder_length, lip_top)
    )

    bore_radius = screw_hole_width / 2
    screw_y = holder_length / 2
    bore = (
        Pos(back_thickness / 2, screw_y, screw_z)
        * Rot(0, 90, 0)
        * Cylinder(bore_radius, back_thickness + 2.0)
    )
    body -= bore

    if draft:
        return body

    eps = 1e-6
    concave = {_key(e) for e in concave_edges(body)}

    def polishable(edge):
        box = edge.bounding_box()
        if box.max.X < eps:
            return False  # lies in the back face, which sits against the wall
        if box.max.Z < eps:
            return False  # lies in the bed-contact face
        if _key(edge) in concave:
            return False
        seat = (
            box.max.X < back_thickness + eps
            and max(abs(box.min.Y - screw_y), abs(box.max.Y - screw_y)) < bore_radius + 1.0
            and max(abs(box.min.Z - screw_z), abs(box.max.Z - screw_z)) < bore_radius + 1.0
        )
        if seat:
            return False  # the bore mouth is where the screw head lands
        mouth = (
            abs(box.min.X - pocket_front) < eps
            and abs(box.max.X - pocket_front) < eps
            and abs(box.min.Z - lip_top) < eps
        )
        return not mouth  # no lead-in on the mouth the bundle drops through

    # 1.2 rather than the usual 1.0: three chamfers meeting at a convex corner leave a
    # triangle of 0.87 * size ** 2, and at 1.0 that lands under the 1mm2 sliver floor.
    return polish(body, body.edges().filter_by(polishable), 1.2)


def _key(edge):
    c = edge.center()
    return (round(c.X, 4), round(c.Y, 4), round(c.Z, 4), round(edge.length, 4))
