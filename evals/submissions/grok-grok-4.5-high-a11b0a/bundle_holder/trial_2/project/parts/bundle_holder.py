from nurb import *


@part
def bundle_holder(
    bundle_diameter=measured("bundle_diameter"),
    draft=False,
):
    """Wall clip for a horizontal cable bundle.

    bundle_diameter: calipered width of the taped cable bundle the clip holds
    """
    # Fit: 0.4 clearance across so an 8.0 bundle sits in an 8.4 seat.
    clearance = 0.4
    cavity = bundle_diameter + clearance
    if cavity < 2.0:
        reject(
            f"bundle_diameter {bundle_diameter} is too small for a printable seat",
            param="bundle_diameter",
        )

    wall_t = 2.5  # >= 2.4 along the bore before the M4 head seats
    shell = 2.0
    front = 2.0  # retention lip, >= 0.8
    length = 12.0  # >= 10 along Y; back face area scales with height

    screw_hole = 4.4
    # Keep the M4 head (8.4 clearance cylinder, 3.2 tall) clear of the bundle seat.
    screw_above_channel = 5.0
    screw_z = shell + cavity + screw_above_channel
    plate_above = screw_hole / 2 + 2.5
    total_h = screw_z + plate_above
    depth_x = wall_t + cavity + front
    channel_h = shell + cavity

    # Back at min X (wall), bed at min Z, bundle runs along Y.
    body = Box(
        depth_x,
        length,
        channel_h,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    # Tall back plate for the screw; thin so the head sits in free space +X of the seat.
    back_ext = Box(
        wall_t,
        length,
        total_h - channel_h,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    ).moved(Location((0, 0, channel_h)))
    body = body + back_ext

    # Open-top rectangular seat: floor blocks -Z, front lip blocks +X, wall blocks -X.
    seat = Box(
        cavity,
        length + 2,
        cavity + 1,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    ).moved(Location((wall_t, 0, shell)))
    body = body - seat

    # M4 clearance through-bore, axis along X, opens on the back face.
    bore = (
        Cylinder(screw_hole / 2, wall_t + 2, align=(Align.CENTER, Align.CENTER, Align.MIN))
        .rotate(Axis.Y, 90)
        .moved(Location((-1, 0, screw_z)))
    )
    body = body - bore

    if draft:
        return body

    bed = body.bounding_box().min.Z
    back = body.bounding_box().min.X
    top = body.bounding_box().max.Z
    mate = concave_edges(body)
    cavity_x0 = wall_t
    cavity_x1 = wall_t + cavity
    cavity_z0 = shell
    cavity_z1 = shell + cavity

    def keep_edge(e):
        bb = e.bounding_box()
        mid = e.center()
        # Bed and wall-back faces stay flat.
        if bb.min.Z <= bed + 1e-6:
            return False
        if bb.min.X <= back + 1e-6 and bb.max.X <= back + 1e-3:
            return False
        # Screw bore is fit-critical; chamfering both rims of a 2.5 wall leaves ~0.5.
        dy = mid.Y
        dz = mid.Z - screw_z
        if (dy * dy + dz * dz) ** 0.5 <= screw_hole / 2 + 1.2:
            return False
        # Seat walls are fit-critical.
        if cavity_x0 - 0.05 <= mid.X <= cavity_x1 + 0.05 and cavity_z0 - 0.05 <= mid.Z <= cavity_z1 + 0.05:
            return False
        if abs(mid.X - cavity_x0) < 0.05 or abs(mid.X - cavity_x1) < 0.05:
            if mid.Z <= cavity_z1 + 0.05:
                return False
        if abs(mid.Z - cavity_z0) < 0.05 and cavity_x0 <= mid.X <= cavity_x1:
            return False
        # Skip the thin plate's top: 1mm chamfers there make ceiling facets and slivers.
        if bb.min.Z >= top - 1e-3:
            return False
        return True

    keep = body.edges().filter_by(keep_edge) - mate
    return polish(body, keep, 1.0)
