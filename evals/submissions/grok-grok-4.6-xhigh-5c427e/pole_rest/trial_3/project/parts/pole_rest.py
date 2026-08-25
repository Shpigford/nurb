from nurb import *


@part
def pole_rest(pole_diameter=measured("pole_diameter"), draft=False):
    """Rest that cradles a freshly finished pole while it dries.

    pole_diameter: width of the pole across its circular section
    """
    axis_height = 18.0
    clearance = 0.2
    wall = 3.5
    length = 22.0

    if pole_diameter < 8.0:
        reject(
            f"pole_diameter {pole_diameter} is too small for a printable cradle; raise it above 8",
            param="pole_diameter",
        )

    inner_r = pole_diameter / 2.0 + clearance
    floor = axis_height - inner_r
    if floor < 2.4:
        reject(
            f"pole_diameter {pole_diameter} leaves less than 2.4mm of bed under the cradle at axis height 18; use a smaller pole",
            param="pole_diameter",
        )

    width = 2.0 * (inner_r + wall)
    height = axis_height

    body = Box(width, length, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    cut = Pos(0, 0, axis_height) * Rot(90, 0, 0) * Cylinder(
        inner_r, length + 4.0
    )
    body = body - cut

    if draft:
        return body

    bed = body.bounding_box().min.Z
    cradle = body.faces().filter_by(GeomType.CYLINDER)
    keep = body.edges().filter_by(lambda e: e.bounding_box().min.Z > bed + 1e-4)
    keep = keep - cradle.edges() - concave_edges(body)
    return polish(body, keep, 1.0)
