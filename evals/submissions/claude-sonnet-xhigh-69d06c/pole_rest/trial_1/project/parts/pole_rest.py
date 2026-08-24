from nurb import *


@part
def pole_rest(
    pole_diameter=20.0,
    rest_length=21.0,
    clearance=0.25,
    wall=1.6,
    side_margin=2.0,
    draft=False,
):
    """
    pole_diameter: diameter of the pole this rest cradles
    rest_length: how long the rest runs along the pole's axis
    clearance: gap left open between the cradle and the pole's surface
    wall: material thickness behind the cradle's cupped contact
    side_margin: extra flat shoulder on each side, beyond the structural wall
    """
    axis_height = 18.0
    pole_radius = pole_diameter / 2.0
    inner_radius = pole_radius + clearance

    if clearance < 0.1:
        reject(
            f"clearance {clearance} leaves less than the 0.1mm this cradle needs "
            f"to stay clear of the pole: raise it above 0.1",
            param="clearance",
        )
    if inner_radius + wall > axis_height:
        reject(
            f"pole_diameter {pole_diameter} makes the cradle deeper than the fixed "
            f"18.0mm mount height allows: it will not fit this bench",
            param="pole_diameter",
        )

    rest_width = 2.0 * (inner_radius + wall + side_margin)

    base = Box(
        rest_width, rest_length, axis_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    channel = Cylinder(
        inner_radius, rest_length + 2.0,
        rotation=(-90, 0, 0),
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    channel = Pos(0, 0, axis_height) * channel
    body = base - channel

    if draft:
        return body

    bed = body.bounding_box().min.Z
    concave = concave_edges(body)
    mating = body.faces().filter_by(GeomType.CYLINDER).edges()
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed + 1e-6
        and e not in concave
        and e not in mating
    )
    return polish(body, keep, 1.0)
