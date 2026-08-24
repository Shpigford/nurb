from nurb import *


@part
def pole_rest(pole_diameter=20.0, length=22.0, wall=3.0, clearance=0.15, draft=False):
    """
    pole_diameter: diameter of the pole this rest cradles
    length: how far the rest runs along the pole, in a row of identical rests
    wall: material left behind the cradle surface and at its sides
    clearance: gap kept between the cradle surface and the pole
    """
    axis_height = 18.0
    groove_radius = pole_diameter / 2 + clearance
    width = 2 * (groove_radius + wall)

    body = Box(width, length, axis_height)
    groove = Cylinder(groove_radius, length, rotation=(90, 0, 0))
    groove = Pos(0, 0, axis_height / 2) * groove
    body = body - groove

    if draft:
        return body

    bed = body.bounding_box().min.Z
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed and e.geom_type != GeomType.CIRCLE
    )
    return polish(body, keep, 0.6)
