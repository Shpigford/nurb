from nurb import *


def _edge_key(edge):
    c = edge.center()
    return (round(c.X, 2), round(c.Y, 2), round(c.Z, 2), round(edge.length, 2))


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Wall clip for a horizontal cable bundle, one M4 pan-head screw.

    bundle_diameter: calipered width of the taped cable bundle
    """
    if bundle_diameter < 4.0:
        reject(
            f"bundle_diameter {bundle_diameter} is too small for a printable cavity",
            param="bundle_diameter",
        )

    # Fit: 0.4 total clearance across the seat (8.4 for an 8.0 bundle).
    cavity = bundle_diameter + 0.4
    length = 12.0
    wall = 2.0
    mount_t = 2.6  # >= 2.4 of shank material before the head seats
    screw_d = 4.4
    head_clear = 8.4

    # Open-top U: floor blocks -Z, front lip blocks +X, back wall blocks -X.
    lip_h = wall + cavity
    # Keep the 8.4 head cylinder clear of the front lip.
    screw_z = lip_h + head_clear / 2 + 0.6
    top_z = screw_z + screw_d / 2 + 2.0
    depth = mount_t + cavity + wall

    back = Box(
        mount_t,
        length,
        top_z,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    floor = Box(
        depth,
        length,
        wall,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    front = Box(
        wall,
        length,
        lip_h,
        align=(Align.MIN, Align.MIN, Align.MIN),
    ).move(Location((mount_t + cavity, 0, 0)))

    body = back.fuse(floor).fuse(front)

    # M4 clearance through-bore along +X; head seats on the front of the mount.
    hole = (
        Cylinder(
            screw_d / 2,
            mount_t + 2,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        )
        .rotate(Axis.Y, 90)
        .move(Location((mount_t / 2, length / 2, screw_z)))
    )
    body = body.cut(hole)

    if draft:
        return body

    bed = body.bounding_box().min.Z
    skip = {_edge_key(e) for e in concave_edges(body)}

    # Leave the screw bore sharp so polish does not smear the seat.
    for face in body.faces():
        if face.geom_type == GeomType.CYLINDER:
            skip.update(_edge_key(e) for e in face.edges())

    # Leave the wall-mating back face sharp.
    for face in body.faces():
        n = face.normal_at(face.center())
        if abs(n.X + 1.0) < 0.01 and face.center().X < 0.1:
            skip.update(_edge_key(e) for e in face.edges())

    edges = [
        e
        for e in body.edges()
        if _edge_key(e) not in skip and e.bounding_box().min.Z > bed + 1e-4
    ]
    # 1.2mm so three-way corner faces stay above the 1mm2 sliver floor.
    return polish(body, edges, 1.2)
