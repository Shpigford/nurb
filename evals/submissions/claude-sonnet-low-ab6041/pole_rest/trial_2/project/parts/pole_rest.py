from nurb import *


@part
def pole_rest(pole_diameter=20.0, draft=False):
    """
    pole_diameter: how wide the pole is across, at its finished/sanded size
    """
    pole_radius = pole_diameter / 2
    clearance = 0.3
    groove_radius = pole_radius + clearance
    wall = 2.5
    axis_height = 18.0

    half_width = groove_radius + wall
    width = 2 * half_width
    length = 25.0
    height = axis_height

    block = Pos(0, 0, height / 2) * Box(width, length, height)
    groove = Pos(0, 0, axis_height) * Rot(-90, 0, 0) * Cylinder(groove_radius, length + 4)
    body = block - groove

    if draft:
        return body

    bed = body.bounding_box().min.Z
    top = body.bounding_box().max.Z

    def is_vertical_corner(e):
        bb = e.bounding_box()
        return (
            abs(bb.min.Z - bed) < 1e-3
            and abs(bb.max.Z - top) < 1e-3
            and abs(bb.min.X - bb.max.X) < 1e-3
            and abs(bb.min.Y - bb.max.Y) < 1e-3
        )

    keep = body.edges().filter_by(is_vertical_corner)
    return polish(body, keep, 1.0)
