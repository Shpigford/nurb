from nurb import *


@part
def pole_rest(pole_diameter=measured("pole_diameter"), draft=False):
    """A bench rest that cradles a freshly finished pole while it dries.

    pole_diameter: the measured width across the pole
    """
    axis_height = 18.0
    clearance = 0.2
    cradle_length = 24.0
    side_wall = 4.0
    top_height = 15.5

    pole_radius = pole_diameter / 2.0
    cradle_radius = pole_radius + clearance
    body_width = pole_diameter + 2.0 * side_wall

    body = Box(
        body_width,
        cradle_length,
        top_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    seat = Cylinder(
        cradle_radius,
        cradle_length + 2.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    seat = seat.rotate(Axis.X, 90.0).translate((0.0, 0.0, axis_height))
    body = body - seat

    if draft:
        return body

    bed = body.bounding_box().min.Z
    exposed = body.edges().filter_by(
        lambda edge: edge.bounding_box().min.Z > bed
        and abs(edge.center().X) > body_width / 2.0 - 0.01
    )
    return polish(body, exposed, 1.0)
