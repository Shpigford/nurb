from nurb import *


@part
def pole_rest(pole_diameter=measured("pole_diameter"), length=20.0, draft=False):
    """A support-free drying rest with a full-length, drop-in pole cradle.

    pole_diameter: measured diameter of the finished pole being supported
    length: how far the rest runs along the pole
    """
    if pole_diameter <= 0.0:
        reject("pole_diameter must be greater than zero", param="pole_diameter")
    if length < 20.0:
        reject("length must be at least 20mm for a stable bench rest", param="length")

    axis_height = 18.0
    clearance = 0.20
    side_wall = 5.0
    seat_radius = pole_diameter / 2.0 + clearance
    width = 2.0 * (seat_radius + side_wall)

    # The open top half of this horizontal cylindrical cut is the drop-in path.
    # Material remains continuously behind the lower half of the pole.
    body = Box(width, length, axis_height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    cutter = Pos(0, 0, axis_height) * Cylinder(
        seat_radius, length + 2.0, align=(Align.CENTER, Align.CENTER, Align.CENTER)
    ).rotate(Axis.X, 90)
    rest = body - cutter

    if draft:
        return rest
    # Only the four outside vertical corners are softened.  Leaving the seat rim
    # sharp preserves its full cylindrical bearing arc and avoids tiny end facets.
    vertical_corners = rest.edges().filter_by(
        lambda edge: edge.bounding_box().size.Z > axis_height - 0.1
    )
    return polish(rest, vertical_corners, 1.0)
