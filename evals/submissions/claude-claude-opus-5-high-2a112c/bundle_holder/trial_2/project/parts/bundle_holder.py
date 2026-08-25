from nurb import *

# M4 pan head measures 8.0 across; 8.4 is the bore a head and its driver have to pass.
M4_DRIVER = 8.4


@part
def bundle_holder(
    bundle_diameter=measured("bundle_diameter"),
    bundle_clearance=0.8,
    holder_length=12.0,
    wall_thickness=2.8,
    screw_hole_width=4.5,
    chamfer_size=1.2,
    draft=False,
):
    """A wall cradle that a horizontal cable bundle drops into from above.

    bundle_diameter: how thick the cable bundle is where the holder grips it
    bundle_clearance: how much wider than the bundle the channel is cut
    holder_length: how far the holder reaches along the run of cable
    wall_thickness: how thick the back plate, the floor and the front lip are
    screw_hole_width: how wide the hole for the M4 mounting screw is
    chamfer_size: how big the chamfer on the exposed edges is
    """
    bundle = float(bundle_diameter)
    if bundle < 3.0:
        reject(
            "bundle_diameter %.1f leaves a channel too narrow to print or to thread a "
            "cable through: raise it above 3" % bundle,
            param="bundle_diameter",
        )

    driver_radius = M4_DRIVER / 2
    length = holder_length
    wall = wall_thickness
    channel = bundle + bundle_clearance

    floor_top = wall
    lip_x0 = wall + channel
    lip_x1 = lip_x0 + wall
    # The bundle counts as held once it can fall no further than 1mm, so the highest it
    # can rest is floor_top + bundle/2 + 1. The lip reaches the top of the bundle there.
    lip_top = floor_top + bundle + 1.0
    # The screw clears that same bundle by half a bundle plus half a driver bore, and
    # the driver's swept cylinder has to pass over the lip on its way out in +X.
    screw_z = lip_top + driver_radius + 0.4
    # The head seats on the front of the plate, so the plate carries a full driver's
    # width of material above the axis, chamfer included.
    plate_top = screw_z + driver_radius + chamfer_size + 0.2

    def block(x0, x1, z0, z1):
        return Pos((x0 + x1) / 2, 0.0, (z0 + z1) / 2) * Box(x1 - x0, length, z1 - z0)

    body = block(0.0, wall, 0.0, plate_top)          # the plate against the wall
    body += block(0.0, lip_x1, 0.0, floor_top)       # the floor the bundle rests on
    body += block(lip_x0, lip_x1, floor_top, lip_top)  # the lip that keeps it there

    body -= (
        Pos(wall / 2, 0.0, screw_z)
        * Rot(0, 90, 0)
        * Cylinder(screw_hole_width / 2, wall + 2.0)
    )

    if draft:
        return body

    # Never the wall face, never the bed, never the mouth the cable threads through,
    # never a concave corner; the kernel refuses whatever is left that cannot land.
    concave = {_edge_key(e) for e in concave_edges(body)}
    keep = []
    for edge in body.edges().filter_by(GeomType.LINE):
        box = edge.bounding_box()
        if box.max.X < 1e-6 or box.max.Z < 1e-6:
            continue
        if abs(box.min.X - lip_x0) < 1e-6 and abs(box.min.Z - lip_top) < 1e-6:
            continue
        if _edge_key(edge) in concave:
            continue
        keep.append(edge)
    return polish(body, keep, chamfer_size)


def _edge_key(edge):
    box = edge.bounding_box()
    return tuple(
        round(v, 4)
        for v in (box.min.X, box.min.Y, box.min.Z, box.max.X, box.max.Y, box.max.Z)
    )
