from nurb import *


@part
def pole_rest(pole_diameter=measured("pole_diameter"), draft=False):
    """A soft-finish pole rest with a drop-in cradle.

    pole_diameter: diameter of the freshly finished pole
    """
    axis_height = 18.0
    length = 24.0
    clearance = 0.20
    pole_radius = pole_diameter / 2.0
    seat_radius = pole_radius + clearance

    # The width grows with the pole so the cradle keeps 1.8mm of radial
    # material behind its 0.2mm-clear seat at every nearby size.
    body = Box(
        pole_diameter + 4.0,
        length,
        axis_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    seat_tool = (
        Pos(0, 0, axis_height)
        * Rot(90, 0, 0)
        * Cylinder(
            seat_radius,
            length + 2.0,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        )
    )
    cradle = body - seat_tool

    if draft:
        return cradle

    # Keep the functional cylindrical seat sharp and chamfer the exposed
    # outer edges for handling.  Concave edges are deliberately excluded.
    concave = concave_edges(cradle)
    bed = cradle.bounding_box().min.Z
    exposed = cradle.edges().filter_by(
        lambda edge: (
            edge.bounding_box().min.Z > bed
            and edge.length > 4.0
            and (
                edge.bounding_box().min.X < -11.9
                or edge.bounding_box().max.X > 11.9
            )
            and edge not in concave
        )
    )
    return polish(cradle, exposed, 1.0)
