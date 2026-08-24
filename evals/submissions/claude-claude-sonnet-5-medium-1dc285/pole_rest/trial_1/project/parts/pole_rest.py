from nurb import *


AXIS_HEIGHT = 18.0  # fixed interface: pole axis height above the bed, several rests share this


@part
def pole_rest(pole_diameter=measured("pole_diameter"), width=24.0, length=28.0, clearance=0.25, draft=False):
    """
    pole_diameter: diameter of the pole this rest cradles
    width: how wide the rest's base is, side to side under the pole
    length: how long the rest is along the pole's axis
    clearance: gap left between the cradle and the pole's surface
    """
    pole_radius = pole_diameter / 2
    inner_radius = pole_radius + clearance

    # Keep at least 1.5mm of material behind the cradle wall regardless of how
    # width was set, so the part stays correct as pole_diameter moves.
    min_width = 2 * (inner_radius + 1.5)
    width = max(width, min_width)

    base = Pos(0, 0, AXIS_HEIGHT / 2) * Box(width, length, AXIS_HEIGHT)
    groove = Pos(0, 0, AXIS_HEIGHT) * Rot(X=90) * Cylinder(inner_radius, length + 2)
    body = base - groove

    if draft:
        return body

    bed = body.bounding_box().min.Z
    concave = concave_edges(body)
    cradle = body.faces().filter_by(GeomType.CYLINDER).edges()
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed and e not in concave and e not in cradle
    )
    return polish(body, keep, 1.0)
