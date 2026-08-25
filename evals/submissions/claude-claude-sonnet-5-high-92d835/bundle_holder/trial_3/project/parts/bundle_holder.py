from nurb import *


@part
def bundle_holder(bundle_diameter=8.0, length=12.0, wall=1.4, draft=False):
    """
    bundle_diameter: diameter of the cable bundle the holder cradles
    length: how far the holder runs along the bundle
    wall: material thickness around the cable channel and the screw bore
    """
    clearance = 0.5
    channel_r = (bundle_diameter + clearance) / 2.0

    screw_bore_r = 2.2   # M4 through-bore, 4.4mm dia
    pocket_r = 4.45        # clears the 8.4mm head-and-driver with a touch of margin
    seat_depth = 2.6      # material ahead of the through-bore before the head seats
    void_gap = 1.0         # solid band separating the channel bore from the screw pocket

    if wall < 0.8:
        reject(f"wall {wall} is under the 0.8mm the retained bundle needs held: raise it above 0.8", param="wall")

    depth = channel_r * 2 + wall * 2

    min_length = 2 * (pocket_r + wall)
    if length < min_length:
        reject(f"length {length} is under the {min_length:.1f}mm the screw pocket needs clear on both sides: raise it above {min_length:.1f}", param="length")

    screw_z = wall + pocket_r
    channel_z = screw_z + pocket_r + void_gap + channel_r
    height = channel_z + channel_r + wall

    body = Box(depth, length, height, align=(Align.MIN, Align.MIN, Align.MIN))

    channel_bore = Pos(depth / 2, -1, channel_z) * (
        Rot(X=-90) * Cylinder(radius=channel_r, height=length + 2, align=(Align.CENTER, Align.CENTER, Align.MIN))
    )

    screw_bore = Pos(0, length / 2, screw_z) * (
        Rot(Y=90) * Cylinder(radius=screw_bore_r, height=seat_depth, align=(Align.CENTER, Align.CENTER, Align.MIN))
    )
    screw_pocket = Pos(seat_depth, length / 2, screw_z) * (
        Rot(Y=90) * Cylinder(radius=pocket_r, height=depth - seat_depth + 1, align=(Align.CENTER, Align.CENTER, Align.MIN))
    )

    body = body - channel_bore - screw_bore - screw_pocket

    if draft:
        return body

    bed = body.bounding_box().min.Z
    back = body.bounding_box().min.X
    y_min = body.bounding_box().min.Y
    y_max = body.bounding_box().max.Y
    concave = concave_edges(body)
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed
        and e.bounding_box().min.X > back
        and e.bounding_box().min.Y > y_min
        and e.bounding_box().max.Y < y_max
        and e not in concave
    )
    return polish(body, keep, 1.0)
