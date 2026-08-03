from nurb import *


@part
def bundle_holder(
    bundle_diameter=measured("bundle_diameter"),
    holder_length=12.0,
    bundle_clearance=0.8,
    lip_rise=1.0,
    back_thickness=3.5,
    floor_thickness=2.4,
    lip_thickness=2.4,
    screw_hole_width=4.4,
    screw_head_width=8.4,
    chamfer_size=1.0,
    draft=False,
):
    """A wall cradle that a horizontal cable bundle drops into from above.

    bundle_diameter: how thick the cable bundle is, measured across
    holder_length: how much of the run the cradle grips, along the wall
    bundle_clearance: slack around the bundle so it drops in rather than wedges
    lip_rise: how far the front lip stands above the middle of the bundle
    back_thickness: how thick the plate that sits against the wall is
    floor_thickness: how thick the shelf the bundle rests on is
    lip_thickness: how thick the front lip that keeps the bundle in is
    screw_hole_width: how wide the hole for the mounting screw is
    screw_head_width: how much room the screw head and driver need
    chamfer_size: how big the softened edges are
    """
    channel = bundle_diameter + bundle_clearance
    lip_x = back_thickness + channel
    width = lip_x + lip_thickness

    # The lip has to reach past the middle of the bundle, or the bundle rolls
    # out over the top of it instead of being stopped by it.
    lip_height = floor_thickness + bundle_diameter / 2.0 + lip_rise

    # The screw sits above everything: high enough that the head-and-driver
    # cylinder clears the lip, and that the highest the bundle can sit and still
    # be held stays clear of the installed screw.
    head_radius = screw_head_width / 2.0
    screw_z = (
        max(
            lip_height + head_radius,
            floor_thickness + 1.0 + bundle_diameter + head_radius,
        )
        + 0.4
    )
    back_height = screw_z + screw_hole_width / 2.0 + 2.4

    def block(x0, x1, z0, z1):
        return Pos((x0 + x1) / 2.0, 0.0, (z0 + z1) / 2.0) * Box(
            x1 - x0, holder_length, z1 - z0
        )

    body = block(0.0, back_thickness, 0.0, back_height)
    body += block(0.0, width, 0.0, floor_thickness)
    body += block(lip_x, width, 0.0, lip_height)

    bore = Pos(back_thickness / 2.0, 0.0, screw_z) * (
        Rot(0.0, 90.0, 0.0) * Cylinder(screw_hole_width / 2.0, back_thickness + 4.0)
    )
    body -= bore

    if draft:
        return body

    # Name what must stay sharp, then let `polish` chamfer whatever the kernel takes.
    # A bare `chamfer(...)` is all or nothing: one edge that cannot land loses the lot.
    box = body.bounding_box()
    bed, back, crown = box.min.Z, box.min.X, box.max.Z
    tol = 1e-6

    def across_the_crown(edge):
        # Three chamfers meeting at the top corners of the plate leave a 0.9mm2
        # triangle. The long front edge of the crown is the one worth softening,
        # so the two short ones that close the corner stay sharp.
        b = edge.bounding_box()
        return b.min.Z > crown - tol and b.max.Y - b.min.Y < tol

    def key(edge):
        b = edge.bounding_box()
        return tuple(
            round(v, 4)
            for v in (b.min.X, b.min.Y, b.min.Z, b.max.X, b.max.Y, b.max.Z)
        )

    inside = {key(e) for e in concave_edges(body)}
    keep = [
        e
        for e in body.edges().filter_by(GeomType.LINE)  # the bore is fit geometry
        if e.bounding_box().max.Z > bed + tol  # nothing lying in the bed face
        and e.bounding_box().max.X > back + tol  # nothing lying in the wall face
        and key(e) not in inside  # never a concave edge
        and not across_the_crown(e)
    ]
    return polish(body, keep, chamfer_size)
