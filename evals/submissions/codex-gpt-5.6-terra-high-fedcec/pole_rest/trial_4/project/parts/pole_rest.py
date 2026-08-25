from nurb import *


@part
def pole_rest(pole_diameter=20.0, length=24.0, side_wall=3.5, clearance=0.25):
    """Low-print-time drying rest with a broad, open, padded-in-air cradle.

    pole_diameter: measured diameter of the finished pole it supports
    length: how far the cradle continues along the pole
    side_wall: material outside each side of the circular seat
    clearance: air gap between the pole and the printed cradle
    """
    pole_radius = pole_diameter / 2.0
    axis_height = 18.0
    seat_radius = pole_radius + clearance

    # Keeping the rim below the pole's midline leaves an unobstructed vertical
    # drop path while retaining a 127-degree lower circular bearing arc.
    rim_height = axis_height - 0.45 * seat_radius
    rest_width = 2.0 * (seat_radius + side_wall)
    body = Box(
        rest_width,
        length,
        rim_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    # The bore is deliberately longer than the body so the same continuous seat
    # profile exists from one end of the rest to the other.
    cutter = Cylinder(
        seat_radius,
        length + 2.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).rotate(Axis.X, 90).translate((0, (length + 2.0) / 2.0, axis_height))
    rest = body.cut(cutter)

    # A small chamfer removes harsh exterior print edges; the concave seat stays
    # circular so it remains a true cradle rather than a pair of contact edges.
    bed = rest.bounding_box().min.Z
    exposed = rest.edges().filter_by(lambda edge: edge.bounding_box().min.Z > bed)
    return polish(rest, exposed, 0.8)
